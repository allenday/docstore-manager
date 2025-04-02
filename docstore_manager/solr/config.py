"""
Configuration management for Solr Manager.
"""
import sys
from typing import Dict, Any, Optional
from pathlib import Path

from ..common.config import get_config_dir, get_profiles as base_get_profiles, load_config as base_load_config
from ..common.exceptions import ConfigurationError

def _convert_config(profile_config: Dict[str, Any]) -> Dict[str, Any]:
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

def load_configuration(profile: Optional[str] = None) -> Dict[str, Any]:
    """Load and convert Solr-specific configuration.
    
    Args:
        profile: Profile name to load (default: 'default')
        
    Returns:
        Converted configuration dictionary
        
    Raises:
        ConfigurationError: If configuration cannot be loaded or is invalid
    """
    try:
        raw_config = base_load_config(profile)
        return _convert_config(raw_config)
    except ConfigurationError as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)