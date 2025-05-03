"""Command for managing Qdrant configuration."""

import json
import logging
from typing import Any
from pathlib import Path

from docstore_manager.core.exceptions import (
    ConfigurationError, InvalidInputError
)
from docstore_manager.core.config.base import (
    get_config_dir,
    get_profiles,
    ConfigurationConverter,
    load_config
)
from docstore_manager.qdrant.command import QdrantCommand

logger = logging.getLogger(__name__)

def show_config(command: QdrantCommand, args):
    """Show current Qdrant configuration using the QdrantCommand handler.
    
    Args:
        command: QdrantCommand instance
        args: Command line arguments
        
    Raises:
        ConfigurationError: If retrieving configuration fails
    """
    logger.info("Retrieving Qdrant configuration")

    try:
        response = command.get_config()

        if not response.success:
            raise ConfigurationError(
                f"Failed to retrieve configuration: {response.error}",
                details={'error': response.error}
            )

        if args.output:
            try:
                with open(args.output, 'w') as f:
                    json.dump(response.data, f, indent=2)
                logger.info(f"Configuration written to {args.output}")
            except Exception as e:
                raise ConfigurationError(f"Failed to write configuration to {args.output}: {e}")
        else:
            logger.info(json.dumps(response.data, indent=2))

    except ConfigurationError:
        raise
    except Exception as e:
        raise ConfigurationError(
            f"Unexpected error retrieving configuration: {e}",
            details={'error_type': e.__class__.__name__}
        )

def update_config(command: QdrantCommand, args):
    """Update Qdrant configuration using the QdrantCommand handler.
    
    Args:
        command: QdrantCommand instance
        args: Command line arguments
        
    Raises:
        ConfigurationError: If configuration update fails
    """
    if not args.config:
        raise ConfigurationError("Configuration data is required for update")

    try:
        config = json.loads(args.config)
    except json.JSONDecodeError as e:
        raise InvalidInputError(
            f"Invalid JSON in configuration: {e}",
            details={"input": args.config}
        )

    logger.info("Updating Qdrant configuration")

    try:
        response = command.update_config(config)

        if not response.success:
            raise ConfigurationError(
                f"Failed to update configuration: {response.error}",
                details={
                    'error': response.error,
                    'config': config
                }
            )

        logger.info(response.message)
        if response.data:
            logger.info(f"Update details: {response.data}")

    except (ConfigurationError, InvalidInputError):
        raise
    except Exception as e:
        raise ConfigurationError(
            f"Unexpected error updating configuration: {e}",
            details={
                'error_type': e.__class__.__name__,
                'config': config
            }
        )

def show_config_info(args: Any):
    """Display configuration information.
    
    Args:
        args: Command line arguments
        
    Raises:
        ConfigurationError: If configuration cannot be loaded
    """
    try:
        # Get config directory
        config_dir = get_config_dir()
        logger.info(f"Configuration directory: {config_dir}")
        
        # Get available profiles
        config_path = args.config or Path(config_dir) / "config.yaml"
        profiles = get_profiles(config_path)
        
        if not profiles:
            logger.info("No configuration profiles found.")
            return
            
        logger.info("\nAvailable profiles:")
        for profile in profiles:
            logger.info(f"  - {profile}")
            
        # Show current profile configuration if specified
        if args.profile:
            try:
                config = load_config(args.profile, args.config)
                logger.info(f"\nConfiguration for profile '{args.profile}':")
                logger.info(json.dumps(config, indent=2))
            except ConfigurationError as e:
                logger.error(f"Error loading profile '{args.profile}': {e}")
                
    except ConfigurationError as e:
        raise ConfigurationError(f"Failed to show configuration info: {e}")
    except Exception as e:
        raise ConfigurationError(
            f"Unexpected error showing configuration info: {e}",
            details={'error_type': e.__class__.__name__}
        )
