"""
Configuration management for Solr Manager.
"""
from typing import Dict, Any

from docstore_manager.core.config.base import ConfigurationConverter
from docstore_manager.core.config.base import get_config_dir, get_profiles, load_config

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
            
        # Extract Solr-specific configuration
        solr_config = profile_config.get("solr", {})
        
        # Extract connection details
        connection = solr_config.get("connection", {})
        
        # Build the configuration dictionary
        config = {
            "solr_url": connection.get("solr_url"),
            "collection": connection.get("collection"),
            "zk_hosts": connection.get("zk_hosts"),
            "num_shards": connection.get("num_shards", 1),
            "replication_factor": connection.get("replication_factor", 1),
            "config_name": connection.get("config_name", "_default"),
            "max_shards_per_node": connection.get("max_shards_per_node", -1)
        }
        
        return config

# Create a singleton instance for convenience
config_converter = SolrConfigurationConverter()

# Export the common config functions
__all__ = ['get_config_dir', 'get_profiles', 'load_config', 'config_converter']