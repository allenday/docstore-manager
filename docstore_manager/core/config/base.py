"""
Base configuration functionality for document store managers.
"""
import os
import sys
import yaml
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

# Use absolute import
from docstore_manager.core.exceptions import ConfigurationError

# Define logger for this module
logger = logging.getLogger(__name__)

def _get_default_config_path() -> Path:
    """Calculate the default config path based on environment."""
    # Check for DOCSTORE_MANAGER_CONFIG environment variable first
    env_config_path = os.environ.get('DOCSTORE_MANAGER_CONFIG')
    if env_config_path:
        logger.debug(f"Using config path from DOCSTORE_MANAGER_CONFIG: {env_config_path}")
        return Path(env_config_path)
        
    # Otherwise, use XDG_CONFIG_HOME or default
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config_home:
        base_path = Path(xdg_config_home)
    else:
        base_path = Path(os.path.expanduser('~/.config'))
        
    default_path = base_path / 'docstore-manager' / 'config.yaml'
    logger.debug(f"Calculated default config path: {default_path}")
    return default_path

def get_config_dir() -> Path:
    """Get the configuration directory path dynamically."""
    # Calculate the path each time to respect environment changes during tests
    config_path = _get_default_config_path()
    # Return the parent directory of the calculated path
    return config_path.parent

def get_profiles(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Get available configuration profiles.
    
    Args:
        config_path: Optional path to config file. If not provided, uses default.
        
    Returns:
        Dictionary of profile names to profile configurations
        
    Raises:
        ConfigurationError: If config file cannot be read or parsed
    """
    # Calculate the resolved path, checking env var if config_path is None
    resolved_config_path = config_path if config_path is not None else _get_default_config_path()
    
    try:
        if not resolved_config_path.exists():
            # If the path was explicitly provided or came from ENV var and doesn't exist, raise error
            if config_path is not None or os.environ.get('DOCSTORE_MANAGER_CONFIG'):
                 raise ConfigurationError(f"Configuration file specified but not found at {resolved_config_path}")
            # Otherwise, if it was the calculated default path, just warn and return empty default
            logger.warning(f"Default configuration file not found at {resolved_config_path}. Returning empty default profile.")
            return {'default': {}}
        
        with open(resolved_config_path) as f:
            config_data = yaml.safe_load(f)
            # If file is empty or YAML parsing returns None, return empty default
            if not config_data:
                logger.warning(f"Configuration file {resolved_config_path} is empty or invalid YAML. Returning empty default profile.")
                return {'default': {}} 
            # Assume the entire loaded data is the dictionary of profiles
            # No need to check for a 'profiles' key
            if not isinstance(config_data, dict):
                 logger.error(f"Configuration file {resolved_config_path} should contain a dictionary of profiles at the top level.")
                 return {'default': {}} # Or raise ConfigurationError?
                 
            logger.debug(f"Loaded profiles from {resolved_config_path}: {list(config_data.keys())}")
            return config_data # Return the whole loaded dictionary
            
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Error parsing YAML file {resolved_config_path}: {e}")
    except Exception as e:
        # Catch other potential errors like file permission issues
        raise ConfigurationError(f"Could not load profiles from {resolved_config_path}: {e}")

def load_config(profile: Optional[str] = None, config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration for a specific profile.
    
    Args:
        profile: Profile name to load (default: 'default')
        config_path: Optional path to config file. If not provided, uses default.
        
    Returns:
        Configuration dictionary for the profile
        
    Raises:
        ConfigurationError: If profile does not exist or config is invalid
    """
    profiles = get_profiles(config_path)
    profile_name = profile or 'default'
    
    if profile_name not in profiles:
        raise ConfigurationError(f"Profile '{profile_name}' not found")
        
    return profiles[profile_name]

def merge_config_with_args(config: Dict[str, Any], args: Any) -> Dict[str, Any]:
    """Merge configuration dictionary with command line arguments.

    Args:
        config: Configuration dictionary
        args: Parsed command line arguments

    Returns:
        Merged configuration dictionary
    """
    # Start with a copy of the config
    result = config.copy()
    
    # Get all attributes from args object
    for key in dir(args):
        # Skip private attributes and methods
        if key.startswith('_'):
            continue
        
        # Get the value using getattr
        value = getattr(args, key)
        
        # Only update if value is not None
        if value is not None:
            result[key] = value
    
    return result

class ConfigurationConverter(ABC):
    """Base class for store-specific configuration converters."""
    
    @abstractmethod
    def convert(self, profile_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert the profile configuration to store-specific format.
        
        Args:
            profile_config: Raw profile configuration
            
        Returns:
            Converted configuration dictionary
        """
        pass
    
    def load_configuration(self, profile: Optional[str] = None) -> Dict[str, Any]:
        """Load and convert store-specific configuration.
        
        Args:
            profile: Profile name to load (default: 'default')
            
        Returns:
            Converted configuration dictionary
            
        Raises:
            ConfigurationError: If configuration cannot be loaded or is invalid
        """
        try:
            raw_config = load_config(profile)
            return self.convert(raw_config)
        except ConfigurationError as e:
            print(f"Error loading configuration: {e}", file=sys.stderr)
            sys.exit(1) 

__all__ = [
    "get_config_dir", 
    "get_profiles", 
    "load_config", 
    "merge_config_with_args", 
    "ConfigurationConverter"
] 