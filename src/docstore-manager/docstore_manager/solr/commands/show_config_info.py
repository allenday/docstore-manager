import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from docstore_manager.core.config.base import load_config, get_config_dir, get_profiles
from docstore_manager.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

def show_config_info(
    profile: str,
    config_path: Optional[Path] = None,
    # Added parameters for potential future extension, e.g., show_sensitive=False
) -> None:
    """Display configuration information.

    Args:
        profile: The configuration profile to display (or 'all').
        config_path: Optional path to the configuration file.
    """
    config_dir = get_config_dir()
    logger.info(f"Configuration directory: {config_dir}")
    print(f"Configuration directory: {config_dir}")

    profiles = get_profiles(config_path)
    logger.info(f"Available profiles: {profiles}")
    print(f"Available profiles: {profiles}")

    if profile and profile.lower() != 'all':
        try:
            config_data = load_config(profile=profile, config_path=config_path)
            logger.info(f"Configuration for profile '{profile}':")
            print(f"\nConfiguration for profile '{profile}':")
            print(json.dumps(config_data, indent=2))
        except ConfigurationError as e:
            logger.error(f"Error loading profile '{profile}': {e}")
            print(f"\nError loading profile '{profile}': {e}", file=sys.stderr)
            # Don't exit, just report error for specific profile
        except Exception as e:
            logger.error(f"Unexpected error loading profile '{profile}': {e}", exc_info=True)
            print(f"\nUnexpected error loading profile '{profile}': {e}", file=sys.stderr)
    elif profile and profile.lower() == 'all':
        all_config = {}
        for p in profiles:
            try:
                all_config[p] = load_config(profile=p, config_path=config_path)
            except Exception as e:
                 logger.warning(f"Could not load profile '{p}' for 'all' view: {e}")
                 all_config[p] = {"error": f"Failed to load: {e}"}
        logger.info("Configuration for all profiles:")
        print("\nConfiguration for all profiles:")
        print(json.dumps(all_config, indent=2))
    else:
        # Default case if no profile specified (show default? or just dirs?)
        # Let's show the default profile by default if 'profile' is None/empty
        try:
            default_config = load_config(profile='default', config_path=config_path)
            logger.info("Configuration for profile 'default':")
            print("\nConfiguration for profile 'default':")
            print(json.dumps(default_config, indent=2))
        except ConfigurationError as e:
             logger.error(f"Error loading default profile: {e}")
             print(f"\nError loading default profile: {e}", file=sys.stderr)
        except Exception as e:
            logger.error(f"Unexpected error loading default profile: {e}", exc_info=True)
            print(f"\nUnexpected error loading default profile: {e}", file=sys.stderr)
            

__all__ = ["show_config_info"] 