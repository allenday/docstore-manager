"""
Configuration management for Solr Manager.
"""
from typing import Dict, Any

from ..common.config import ConfigurationConverter

class SolrConfigurationConverter(ConfigurationConverter):
    """Solr-specific configuration converter."""
    
    def convert(self, profile_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert the profile configuration to Solr-specific format.
        
        Args:
            profile_config: Raw profile configuration
            
        Returns:
            Converted configuration dictionary
        """
        if not profile_config:
            return {}
            
        # Extract connection details
        connection = profile_config.get("connection", {})
        
        # Build the configuration dictionary
        config = {
            "solr_url": connection.get("solr_url"),
            "collection": connection.get("collection"),
            "zk_hosts": connection.get("zk_hosts"),
            "num_shards": connection.get("num_shards", 1),
            "replication_factor": connection.get("replication_factor", 1),
            "config_name": connection.get("config_name", "default"),
            "max_shards_per_node": connection.get("max_shards_per_node", -1)
        }
        
        return config

# Create a singleton instance for convenience
config_converter = SolrConfigurationConverter()
load_configuration = config_converter.load_configuration