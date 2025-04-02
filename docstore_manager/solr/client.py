"""
Solr client implementation.
"""
from typing import Dict, Any, Optional
import pysolr
from kazoo.client import KazooClient

from ..common.client import DocumentStoreClient
from ..common.exceptions import ConfigurationError, ConnectionError
from .config import config_converter

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
    
    def create_client(self, config: Dict[str, Any]) -> pysolr.Solr:
        """Create a new Solr client instance.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            New Solr client instance
            
        Raises:
            ConnectionError: If client creation fails
        """
        try:
            # If ZooKeeper hosts are provided, use them to find Solr
            if config.get("zk_hosts"):
                zk = KazooClient(hosts=config["zk_hosts"])
                zk.start()
                try:
                    # Get active Solr nodes from ZooKeeper
                    # This is a simplified example - in practice you'd want to:
                    # 1. Get the list of live nodes
                    # 2. Choose one randomly or using a load balancing strategy
                    # 3. Handle failover
                    solr_url = self._get_solr_url_from_zk(zk)
                finally:
                    zk.stop()
            else:
                solr_url = config["solr_url"]
            
            # Create the Solr client
            return pysolr.Solr(
                f"{solr_url}/{config.get('collection', '')}",
                timeout=10
            )
            
        except Exception as e:
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
    
    def _get_solr_url_from_zk(self, zk: KazooClient) -> str:
        """Get Solr URL from ZooKeeper.
        
        Args:
            zk: Active KazooClient instance
            
        Returns:
            Solr URL
            
        Raises:
            ConnectionError: If no Solr URL can be found
        """
        # This is a simplified example - in practice you'd want more robust logic
        try:
            # Get live nodes from /live_nodes
            live_nodes = zk.get_children("/live_nodes")
            if not live_nodes:
                raise ConnectionError("No live Solr nodes found in ZooKeeper")
            
            # Use the first live node
            # In practice, you'd want to implement load balancing
            node = live_nodes[0]
            return f"http://{node}"
            
        except Exception as e:
            raise ConnectionError(f"Failed to get Solr URL from ZooKeeper: {e}")

# Create a singleton instance for convenience
client = SolrDocumentStore() 