"""Command for managing Qdrant configuration."""

import json
import logging

from ...common.exceptions import (
    ConfigurationError,
    FileOperationError,
    FileParseError
)
from ..command import QdrantCommand

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
                raise FileOperationError(args.output, f"Failed to write configuration: {e}")
        else:
            print(json.dumps(response.data, indent=2))

    except (ConfigurationError, FileOperationError):
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
        FileParseError: If configuration JSON is invalid
    """
    if not args.config:
        raise ConfigurationError("Configuration data is required for update")

    try:
        config = json.loads(args.config)
    except json.JSONDecodeError as e:
        raise FileParseError(
            "config",
            "JSON",
            f"Invalid JSON in configuration: {e}"
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

    except (ConfigurationError, FileParseError):
        raise
    except Exception as e:
        raise ConfigurationError(
            f"Unexpected error updating configuration: {e}",
            details={
                'error_type': e.__class__.__name__,
                'config': config
            }
        ) 