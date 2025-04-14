"""Count command implementation."""

import json
import logging
from typing import Optional

from ...common.exceptions import CollectionError, DocumentError, QueryError
from ..command import QdrantCommand

logger = logging.getLogger(__name__)

def _parse_query(query_str: Optional[str]) -> Optional[dict]:
    """Parse query string into a query object.

    Args:
        query_str: Query string in JSON format

    Returns:
        Query object or None if no query provided

    Raises:
        QueryError: If query string is invalid
    """
    if not query_str:
        return None

    try:
        return json.loads(query_str)
    except json.JSONDecodeError as e:
        raise QueryError(query_str, f"Invalid query JSON: {e}")

def count_documents(command: QdrantCommand, args) -> None:
    """Count documents in a collection.

    Args:
        command: QdrantCommand instance
        args: Command line arguments

    Raises:
        CollectionError: If collection name is missing
        QueryError: If query is invalid
        DocumentError: If document count fails
    """
    if not args.collection:
        raise CollectionError("unknown", "Collection name is required")

    try:
        query = _parse_query(args.query) if args.query else None

        response = command.count_documents(
            collection=args.collection,
            query=query
        )

        if not response.success:
            raise DocumentError(
                args.collection,
                f"Failed to count documents: {response.error}"
            )

        logger.info(response.message)
        if response.data is not None:
            print(json.dumps({"count": response.data}, indent=2))

    except QueryError:
        raise
    except Exception as e:
        raise DocumentError(
            args.collection,
            f"Unexpected error counting documents: {e}"
        ) 