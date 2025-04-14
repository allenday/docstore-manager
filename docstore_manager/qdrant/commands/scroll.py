"""Scroll command implementation."""

import logging
import json
from typing import Optional

from ...common.exceptions import CollectionError, DocumentError, QueryError
from ..command import QdrantCommand

logger = logging.getLogger(__name__)

def _parse_filter(filter_str: Optional[str]) -> Optional[dict]:
    """Parse filter string into a filter object.

    Args:
        filter_str: Filter string in JSON format

    Returns:
        Filter object or None if no filter provided

    Raises:
        QueryError: If filter string is invalid
    """
    if not filter_str:
        return None

    try:
        return json.loads(filter_str)
    except json.JSONDecodeError as e:
        raise QueryError(filter_str, f"Invalid filter JSON: {e}")

def scroll_documents(command: QdrantCommand, args) -> None:
    """Scroll through documents in a collection.

    Args:
        command: QdrantCommand instance
        args: Command line arguments

    Raises:
        CollectionError: If collection name is missing
        QueryError: If filter is invalid
        DocumentError: If document retrieval fails
    """
    if not args.collection:
        raise CollectionError("unknown", "Collection name is required")

    try:
        filter_obj = _parse_filter(args.query) if args.query else None

        response = command.scroll_documents(
            collection=args.collection,
            scroll_filter=filter_obj,
            limit=args.batch_size,
            with_vectors=args.with_vectors,
            with_payload=args.with_payload,
            offset=args.offset
        )

        if not response['success']:
            raise DocumentError(
                args.collection,
                f"Failed to scroll documents: {response['error']}"
            )

        logger.info(response['message'])
        if response['data']:
            logger.info(f"Retrieved {len(response['data'])} documents")
            print(json.dumps(response['data'], indent=2))

    except QueryError:
        raise
    except Exception as e:
        raise DocumentError(
            args.collection,
            f"Unexpected error scrolling documents: {e}"
        ) 