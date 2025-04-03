"""
Base configuration functionality for document store managers.
"""
import os
import sys
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

from ..exceptions import ConfigurationError

def get_config_dir() -> Path:
    """Get the configuration directory path.
    
    Returns:
        Path to the configuration directory
    """
    # Use XDG_CONFIG_HOME if set, otherwise fallback to ~/.config
    config_home = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    return Path(config_home) / 'docstore-manager'

def get_profiles(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Get available configuration profiles.
    
    Args:
        config_path: Optional path to config file. If not provided, uses default.
        
    Returns:
        Dictionary of profile names to profile configurations
        
    Raises:
        ConfigurationError: If config file cannot be read or parsed
    """
    if config_path is None:
        config_path = get_config_dir() / 'config.yaml'
    
    try:
        if not config_path.exists():
            return {'default': {}}
        
        with open(config_path) as f:
            profiles = yaml.safe_load(f)
            if not profiles:
                return {'default': {}}
            return profiles
            
    except Exception as e:
        raise ConfigurationError(f"Could not load profiles from {config_path}: {e}")

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
    """Merge configuration with command line arguments.
    
    Command line arguments take precedence over config values.
    
    Args:
        config: Configuration dictionary
        args: Parsed command line arguments
        
    Returns:
        Merged configuration dictionary
    """
    result = config.copy()
    
    # Convert args to dictionary, excluding None values and private attributes
    arg_dict = {
        k: v for k, v in vars(args).items() 
        if not k.startswith('_') and v is not None
    }
    
    # Update config with non-None argument values
    result.update(arg_dict)
    
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