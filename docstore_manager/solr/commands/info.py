"""Command for getting Solr collection information."""

import json
import logging

from docstore_manager.core.exceptions import ConfigurationError # Absolute, new path
from docstore_manager.solr.command import SolrCommand # Absolute

logger = logging.getLogger(__name__)

def collection_info(command: SolrCommand, args):
    """Get information about a Solr collection.
    
    Args:
        command: SolrCommand instance
        args: Command line arguments
        
    Raises:
        ConfigurationError: If getting collection info fails
    """
    if not args.collection:
        logger.error("Collection name is required")
        return

    logger.info(f"Retrieving information for collection '{args.collection}'")

    try:
        response = command.get_collection_info(args.collection)

        if not response.success:
            raise ConfigurationError(
                f"Failed to get collection info: {response.error}",
                details={
                    'collection': args.collection,
                    'error': response.error
                }
            )

        # Format and output the results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(response.data, f, indent=2)
            logger.info(f"Collection info written to {args.output}")
        else:
            print(json.dumps(response.data, indent=2))

    except ConfigurationError:
        raise
    except Exception as e:
        raise ConfigurationError(
            f"Unexpected error getting collection info: {e}",
            details={
                'collection': args.collection,
                'error_type': e.__class__.__name__
            }
        )