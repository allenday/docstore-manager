"""
Configuration management for Qdrant Manager.
"""
import sys
from typing import Dict, Any, Optional
from pathlib import Path

from ..common.config import get_config_dir, get_profiles as base_get_profiles, load_config as base_load_config
from ..common.exceptions import ConfigurationError

def _convert_config(profile_config: Dict[str, Any]) -> Dict[str, Any]:
    """Convert the profile configuration to Qdrant-specific format.
    
    Args:
        profile_config: Raw profile configuration
        
    Returns:
        Converted configuration dictionary
    """
    if not profile_config:
        return {}
        
    # Extract connection details
    connection = profile_config.get("connection", {})
    
    # Extract vector configuration
    vectors = profile_config.get("vectors", {})
    
    # Build the configuration dictionary
    config = {
        "url": connection.get("url"),
        "port": connection.get("port"),
        "api_key": connection.get("api_key"),
        "collection": connection.get("collection"),
        "vector_size": vectors.get("size", 256),
        "distance": vectors.get("distance", "cosine"),
        "indexing_threshold": vectors.get("indexing_threshold", 0),
        "payload_indices": profile_config.get("payload_indices", [])
    }
    
    return config

def load_configuration(profile: Optional[str] = None) -> Dict[str, Any]:
    """Load and convert Qdrant-specific configuration.
    
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