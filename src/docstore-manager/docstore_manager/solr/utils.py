"""Utility functions for Solr operations."""

import os
import sys
import logging
import random
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

try:
    import pysolr
except ImportError:
    logger.error("Error: pysolr is not installed. Please run: pip install pysolr")
    sys.exit(1)

try:
    from kazoo.client import KazooClient
    kazoo_imported = True
except ImportError:
    kazoo_imported = False

from docstore_manager.core.exceptions import ConfigurationError, ConnectionError
from docstore_manager.core.config.base import load_config

logger = logging.getLogger(__name__)

def load_configuration(args):
    """Load configuration from config file or command line arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        Dict containing configuration
        
    Raises:
        ConfigurationError: If required configuration is missing
    """
    # First try to load from config file
    if hasattr(args, 'profile') and args.profile:
        raw_config = load_config(args.profile)
    else:
        raw_config = load_config()
    
    # Extract Solr-specific configuration
    config = raw_config.get('solr', {}).get('connection', {})
    
    # Override with command-line arguments if provided
    if hasattr(args, 'solr_url') and args.solr_url:
        config['solr_url'] = args.solr_url
    if hasattr(args, 'zk_hosts') and args.zk_hosts:
        config['zk_hosts'] = args.zk_hosts
    if hasattr(args, 'collection') and args.collection:
        config['collection'] = args.collection
    
    # Validate configuration
    if not config.get('solr_url') and not config.get('zk_hosts'):
        raise ConfigurationError(
            "Either solr_url or zk_hosts must be provided",
            details={'config_keys': list(config.keys())}
        )
    
    # Validate connection method specific requirements
    if config.get('zk_hosts') and not kazoo_imported:
        raise ConfigurationError(
            "ZooKeeper connection specified but 'kazoo' library is not installed",
            details={
                'missing_package': 'kazoo',
                'install_command': 'pip install solr-manager[zookeeper]'
            }
        )
    
    return config

def initialize_solr_client(config: Dict[str, Any], collection_name: str) -> pysolr.Solr:
    """Initialize and return a Solr client based on the configuration.
    
    Args:
        config: The connection configuration dictionary
        collection_name: The collection name to connect to
        
    Returns:
        A pysolr.Solr instance
        
    Raises:
        ConfigurationError: If required configuration is missing
        ConnectionError: If connection to Solr fails
    """
    auth = None
    if config.get('username') and config.get('password'):
        auth = (config['username'], config['password'])
        logger.info("Using authentication.")
        
    # Determine connection timeout (use a default if not specified)
    timeout = config.get('timeout', 30) # Default to 30 seconds

    try:
        if config.get('zk_hosts'):
            # Connect using ZooKeeper (SolrCloud)
            zk_hosts = config['zk_hosts']
            logger.info(f"Initializing SolrCloud client via ZooKeeper: {zk_hosts}, collection: {collection_name}")
            
            if not kazoo_imported:
                raise ConfigurationError(
                    "Cannot initialize SolrCloud client: 'kazoo' is not installed",
                    details={'install_command': 'pip install solr-manager[zookeeper]'}
                )
                
            zk = KazooClient(hosts=zk_hosts, timeout=timeout)
            # Note: pysolr.SolrCloud takes KazooClient instance
            solr_client = pysolr.SolrCloud(zk, collection_name, auth=auth, timeout=timeout)
            logger.info(f"SolrCloud client initialized for collection '{collection_name}'.")

        elif config.get('solr_url'):
            # Connect using direct URL
            solr_url_from_config = config['solr_url']
            # Initialize WITH collection for data operations
            full_solr_url = f"{solr_url_from_config.rstrip('/')}/{collection_name}"
            logger.info(f"Initializing Solr client for collection URL: {full_solr_url}")
            
            solr_client = pysolr.Solr(full_solr_url, auth=auth, timeout=timeout)
            logger.info(f"Solr client initialized for collection '{collection_name}'.")
        else:
            raise ConfigurationError(
                "Invalid configuration: No 'solr_url' or 'zk_hosts' provided",
                details={'config_keys': list(config.keys())}
            )
            
        return solr_client
        
    except pysolr.SolrError as e:
        # Error during client instantiation itself
        raise ConnectionError(
            f"Failed to initialize Solr client: {e}",
            details={
                'collection': collection_name,
                'solr_url': config.get('solr_url'),
                'zk_hosts': config.get('zk_hosts')
            }
        )
    except ConfigurationError: # Let specific config errors pass through
        raise
    except Exception as e:
        # Catch other potential errors (e.g., network issues, Kazoo errors)
        # Re-raise as ConnectionError for consistent handling
        raise ConnectionError(
            f"An unexpected error occurred during Solr connection: {e}",
            details={
                'collection': collection_name,
                'solr_url': config.get('solr_url'),
                'zk_hosts': config.get('zk_hosts'),
                'error_type': e.__class__.__name__
            }
        )

def get_solr_base_url(config: Dict[str, Any]) -> str:
    """Get the base Solr URL for admin operations.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Base Solr URL
        
    Raises:
        ConfigurationError: If base URL cannot be determined
    """
    if config.get('solr_url'):
        return config['solr_url'].rstrip('/')
    
    if config.get('zk_hosts'):
        if not kazoo_imported:
            raise ConfigurationError(
                "Admin command requires Solr base URL, but 'solr_url' is missing and 'kazoo' is not installed",
                details={
                    'missing_package': 'kazoo',
                    'install_command': 'pip install solr-manager[zookeeper]'
                }
            )
        
        try:
            # Try to discover Solr URL from ZooKeeper
            solr_url = discover_solr_url_from_zk(config['zk_hosts'])
            if solr_url:
                return solr_url
        except Exception as e:
            raise ConfigurationError(
                f"Error discovering Solr nodes via ZooKeeper: {e}",
                details={
                    'zk_hosts': config['zk_hosts'],
                    'error_type': e.__class__.__name__
                }
            )
    
    raise ConfigurationError(
        "Cannot determine base Solr URL for admin task",
        details={
            'missing_keys': ['solr_url', 'zk_hosts'],
            'config_keys': list(config.keys())
        }
    )

def discover_solr_url_from_zk(zk_hosts: str) -> str:
    """Discover Solr URL from ZooKeeper.
    
    Args:
        zk_hosts: ZooKeeper connection string
        
    Returns:
        Discovered Solr URL
        
    Raises:
        ConfigurationError: If Solr URL cannot be discovered
    """
    try:
        zk = KazooClient(hosts=zk_hosts)
        zk.start()
        
        try:
            # Get list of live nodes
            live_nodes_path = '/live_nodes'
            if not zk.exists(live_nodes_path):
                raise ConfigurationError(
                    f"No live nodes found in ZooKeeper at {live_nodes_path}",
                    details={'zk_hosts': zk_hosts}
                )
            
            live_nodes = zk.get_children(live_nodes_path)
            if not live_nodes:
                raise ConfigurationError(
                    "No live Solr nodes found in ZooKeeper",
                    details={'zk_hosts': zk_hosts}
                )
            
            # Pick a random live node
            random_node = random.choice(live_nodes)
            
            # Parse node name to get host, port, and context
            # Expected format: host:port_context (e.g., 10.0.0.1:8983_solr)
            try:
                host_and_port, context = random_node.split('_')
                # Further split host_and_port to validate format if needed
                # Example: host, port_str = host_and_port.split(':')
            except ValueError:
                raise ConfigurationError(
                    f"Could not parse host:port_context from live node name: {random_node}",
                    details={'node_name': random_node}
                )

            # Construct Solr URL (assuming http)
            # Note: We use host_and_port directly as it contains host:port
            # The context usually includes the leading '/' if needed by Solr, 
            # but standard ZK registration doesn't include it, so we add it.
            base_url = f"http://{host_and_port}"
            full_url = f"{base_url.rstrip('/')}/{context.lstrip('/')}"
            return full_url

        except ConfigurationError: # Propagate specific config errors
            raise
        except ConnectionError: # Propagate specific connection errors from inner block
            raise
        except Exception as inner_e: # Catch other errors during ZK interaction
            raise ConnectionError(
                f"Error interacting with ZooKeeper after connection: {inner_e}",
                details={
                    'zk_hosts': zk_hosts,
                    'error_type': inner_e.__class__.__name__
                }
            )
        finally:
            zk.stop()

    except ConfigurationError: # Propagate specific config errors from inner block
        raise
    except ConnectionError: # Propagate specific connection errors from inner block
        raise
    except Exception as e: # Catch potential KazooClient init or start errors
        # These are likely connection issues as well
        raise ConnectionError(
            f"Failed to initialize or connect to ZooKeeper: {e}",
            details={
                'zk_hosts': zk_hosts,
                'error_type': e.__class__.__name__
            }
        ) 