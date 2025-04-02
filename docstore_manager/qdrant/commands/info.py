"""Command for getting collection information."""

import logging

from ...common.exceptions import CollectionError, CollectionNotFoundError
from ..command import QdrantCommand

logger = logging.getLogger(__name__)

def collection_info(command: QdrantCommand, args):
    """Get collection information using the QdrantCommand handler.
    
    Args:
        command: QdrantCommand instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        CollectionNotFoundError: If collection does not exist
    """
    if not args.collection:
        raise CollectionError("", "Collection name is required")

    logger.info(f"Getting information for collection '{args.collection}'")

    try:
        response = command.get_collection_info(name=args.collection)

        if not response.success:
            if "not found" in str(response.error).lower():
                raise CollectionNotFoundError(
                    args.collection,
                    f"Collection '{args.collection}' does not exist"
                )
            raise CollectionError(
                args.collection,
                f"Failed to get collection info: {response.error}",
                details={'error': response.error}
            )

        if not response.data:
            logger.info("No collection information available.")
            return

        # Print collection info
        print(f"\nCollection: {args.collection}")
        print("=" * (len(args.collection) + 11))
        
        info = response.data
        print(f"Vector size: {info.get('vector_size', 'N/A')}")
        print(f"Distance: {info.get('distance', 'N/A')}")
        print(f"Status: {info.get('status', 'N/A')}")
        print(f"Indexed vectors: {info.get('vectors_count', 0)}")
        print(f"Segments: {info.get('segments_count', 0)}")
        print(f"On disk: {info.get('on_disk', False)}")
        
        if info.get('payload_schema'):
            print("\nPayload Schema:")
            for field, schema in info['payload_schema'].items():
                print(f"  {field}: {schema}")

    except (CollectionError, CollectionNotFoundError):
        raise
    except Exception as e:
        raise CollectionError(
            args.collection,
            f"Unexpected error getting collection info: {e}",
            details={'error_type': e.__class__.__name__}
        ) 