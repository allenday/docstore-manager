"""
Solr client implementation.
"""
from typing import Dict, Any, Optional
import pysolr
from kazoo.client import KazooClient

from ..common.client import DocumentStoreClient
from ..common.exceptions import ConfigurationError, ConnectionError
from .config import config_converter
# Import the flag from utils
from .utils import kazoo_imported

class SolrDocumentStore(DocumentStoreClient):
    """Solr-specific client implementation."""
    
    def __init__(self):
        """Initialize with Solr configuration converter."""
        super().__init__(config_converter)
    
    def validate_config(self, config: Dict[str, Any]):
        """Validate Solr configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Either solr_url or zk_hosts is required
        if not config.get("solr_url") and not config.get("zk_hosts"):
            raise ConfigurationError("Either solr_url or zk_hosts must be provided")
    
    def _get_solr_url_via_zk(self, zk_hosts: str) -> str:
        """Connects to ZK, finds a live Solr node URL, and disconnects."""
        zk = None
        try:
            zk = KazooClient(hosts=zk_hosts)
            zk.start()
            # Get live nodes from /live_nodes
            live_nodes = zk.get_children("/live_nodes")
            if not live_nodes:
                raise ConnectionError("No live Solr nodes found in ZooKeeper")
            
            # Basic: Use the first live node. 
            # TODO: Implement better node selection (random, load balancing)
            node_path = live_nodes[0]
            node_data_bytes, _ = zk.get(f"/live_nodes/{node_path}")
            node_data = node_data_bytes.decode('utf-8')
            # Extract host and port (assuming format like host:port_solr)
            # This might need adjustment based on actual ZK data format
            solr_node_address = node_data.split('_')[0]
            return f"http://{solr_node_address}" # Construct base URL
            
        except Exception as e:
            # Catch Kazoo errors or others during ZK interaction
            raise ConnectionError(f"Failed to get Solr URL from ZooKeeper: {e}")
        finally:
            if zk:
                zk.stop()
                zk.close() # Ensure Kazoo client is closed

    def create_client(self, config: Dict[str, Any]) -> pysolr.Solr:
        """Create a new Solr client instance."""
        try:
            solr_url_base = None
            if config.get("zk_hosts"):
                if not kazoo_imported:
                    raise ConfigurationError("kazoo library is required for zk_hosts support. Please install it.")
                # Use the new helper method
                solr_url_base = self._get_solr_url_via_zk(config["zk_hosts"])
            elif config.get("solr_url"):
                solr_url_base = config["solr_url"]
            else:
                # This case should be caught by validate_config, but belts and suspenders
                 raise ConfigurationError("Either solr_url or zk_hosts must be provided")

            # Construct final URL with collection
            collection = config.get('collection', '')
            # Ensure no double slashes if collection is empty or base URL ends with /
            final_solr_url = f"{solr_url_base.rstrip('/')}/{collection.lstrip('/')}"
            if not collection: # Avoid trailing slash if no collection
                 final_solr_url = solr_url_base.rstrip('/')
                 
            # TODO: Add support for auth (username/password) from config
            timeout = config.get('timeout', 10) 

            # Create the Solr client
            return pysolr.Solr(final_solr_url, timeout=timeout)
            
        except ConnectionError: # Re-raise specific connection errors
            raise
        except Exception as e:
            # Wrap other exceptions
            raise ConnectionError(f"Failed to create Solr client: {e}")
    
    def validate_connection(self, client: pysolr.Solr) -> bool:
        """Validate connection to Solr server.
        
        Args:
            client: Solr client instance to validate
            
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to ping Solr as a connection test
            client.ping()
            return True
        except Exception:
            return False
    
    def close(self, client: pysolr.Solr):
        """Close the Solr client connection.
        
        Args:
            client: Solr client instance to close
        """
        try:
            client.get_session().close()
        except Exception:
            pass  # Best effort

# Create a singleton instance for convenience
client = SolrDocumentStore() 