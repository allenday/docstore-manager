"""Command for creating a new Solr collection."""

import json
import logging
from typing import Dict, Any, Optional

from ..command import SolrCommand

logger = logging.getLogger(__name__)

def _parse_config(args) -> Optional[Dict[str, Any]]:
    """Parse collection configuration from command line arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        Dict containing collection configuration or None if parsing fails
    """
    if not args.config:
        return {}

    try:
        return json.loads(args.config)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration: {args.config}")
        return None

def create_collection(command: SolrCommand, args):
    """Create a new Solr collection using the SolrCommand handler.
    
    Args:
        command: SolrCommand instance
        args: Command line arguments
    """
    if not args.collection:
        logger.error("Collection name is required")
        return

    config = _parse_config(args)
    if args.config and config is None:
        return

    # Build collection configuration
    collection_config = config or {}
    if args.num_shards:
        collection_config['numShards'] = args.num_shards
    if args.replication_factor:
        collection_config['replicationFactor'] = args.replication_factor
    if args.config_name:
        collection_config['collection.configName'] = args.config_name

    logger.info(f"Creating collection '{args.collection}'")
    if collection_config:
        logger.info(f"Using configuration: {json.dumps(collection_config, indent=2)}")

    try:
        response = command.create_collection(
            collection=args.collection,
            config=collection_config
        )

        if not response.success:
            logger.error(f"Failed to create collection: {response.error}")
            return

        logger.info(response.message)
        if response.data:
            logger.info(f"Collection details: {json.dumps(response.data, indent=2)}")

    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        import traceback
        traceback.print_exc() 