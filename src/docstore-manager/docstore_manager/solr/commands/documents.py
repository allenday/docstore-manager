"""Command for document operations in Solr."""

import json
import logging
import sys
from typing import List, Dict, Any, Optional, Tuple, Iterable, TextIO

from pysolr import SolrError

# Import client
from docstore_manager.solr.client import SolrClient
from docstore_manager.core.exceptions import (
    DocumentError,
    DocumentStoreError,
    InvalidInputError,
)
from docstore_manager.core.command.base import CommandResponse
from docstore_manager.core.utils import load_ids_from_file

logger = logging.getLogger(__name__)

ALLOWED_FIELDS = {
    "id",
    "text_txt",
    "userblog_name_s",
    "post_id_l",
    "created_at_l",
    "permalink_url_s",
    "hashtags_ss",
    "weblinks_ss",
    "message_type_s",
    "active_message_s",
    "post_body_type_s",
    "files_ss",
    "suspect_reasons_ss",
}


def _iter_documents_stream(
    file_obj: TextIO, source: str, allow_json_array: bool
) -> Iterable[Dict[str, Any]]:
    """Yield documents from a file-like object.

    If the stream is seekable and starts with '[', treat as a JSON array.
    Otherwise, treat as JSON Lines (one JSON object per line).
    """
    # Detect JSON array only if we can safely peek/reset.
    if allow_json_array and file_obj.seekable():
        pos = file_obj.tell()
        first_char = file_obj.read(1)
        while first_char and first_char.isspace():
            first_char = file_obj.read(1)
        file_obj.seek(pos)

        if first_char == "[":
            try:
                data = json.load(file_obj)
            except json.JSONDecodeError as e:
                raise DocumentStoreError(f"Invalid JSON array in {source}: {e}") from e
            if not isinstance(data, list):
                raise DocumentStoreError(
                    f"Expected a JSON array in {source}, got {type(data).__name__}"
                )
            for doc in data:
                yield doc
            return

    # Fallback: JSONL streaming
    for i, line in enumerate(file_obj, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError as e:
            raise DocumentStoreError(
                f"Invalid JSON on line {i} in {source}: {e}"
            ) from e


def _load_ids_from_file(file_path: str) -> List[str]:
    """Load document IDs from a file."""
    return load_ids_from_file(file_path)

def add_documents(
    client: SolrClient,
    collection_name: str,
    doc_input: str,
    commit: bool,
    batch_size: int,
    commit_every: int = 0,
) -> Tuple[bool, str]:
    """Add documents using the SolrClient.

    Supports:
    - JSON array string
    - Single JSON object string
    - File/pipe via @<path> (JSON array or JSONL). Use @- for stdin.
    - Optional periodic commits via commit_every (>0).
    """
    source_desc = ""

    total = 0  # Track documents processed so we can honor commit_every.

    def _send_batch(batch: List[Dict[str, Any]], is_last: bool, commit_now: bool) -> None:
        if not batch:
            return
        # Only commit on the last batch to avoid repeated commits.
        commit_flag = commit_now or (commit and is_last)
        client.add_documents(
            collection_name=collection_name,
            documents=batch,
            commit=commit_flag,
            batch_size=batch_size,
        )

    try:
        # Determine input mode
        if doc_input == "-" or doc_input == "@-":
            file_obj = sys.stdin
            source_desc = "stdin"
            iterator = _iter_documents_stream(
                file_obj, source=source_desc, allow_json_array=False
            )
        elif doc_input.startswith("@"):
            file_path = doc_input[1:]
            source_desc = f"file '{file_path}'"
            # Open in text mode; allow JSON array only if the stream is seekable.
            file_obj = open(file_path, "r", encoding="utf-8")
            iterator = _iter_documents_stream(
                file_obj,
                source=source_desc,
                allow_json_array=file_obj.seekable(),
            )
        else:
            source_desc = "input string"
            try:
                loaded_data = json.loads(doc_input)
            except json.JSONDecodeError as e:
                raise DocumentStoreError(
                    f"Invalid JSON in input string: {e}"
                ) from e
            if isinstance(loaded_data, list):
                iterator = iter(loaded_data)
            elif isinstance(loaded_data, dict):
                iterator = iter([loaded_data])
            else:
                raise DocumentError(
                    collection_name,
                    "Input JSON string must be an object or a list.",
                )

        total = 0
        batch: List[Dict[str, Any]] = []
        for doc in iterator:
            # Drop any fields not explicitly allowed to avoid schema errors.
            doc = {k: v for k, v in doc.items() if k in ALLOWED_FIELDS}
            if "id" not in doc:
                continue

            batch.append(doc)
            if len(batch) >= batch_size:
                predicted_total = total + len(batch)
                commit_now = commit_every > 0 and predicted_total % commit_every == 0
                _send_batch(batch, is_last=False, commit_now=commit_now)
                total += len(batch)
                batch = []

        # Final batch (commit if requested)
        commit_now = commit_every > 0 and (total + len(batch)) % commit_every == 0
        _send_batch(batch, is_last=True, commit_now=commit_now)
        total += len(batch)

        if total == 0:
            logger.warning(
                f"No documents found to add from {source_desc} for collection '{collection_name}'."
            )
            return (True, f"No documents found in {source_desc} to add.")

        message = (
            f"Successfully added/updated {total} documents in collection '{collection_name}'."
        )
        logger.info(message)
        return (True, message)

    except SolrError as e:
        message = f"SolrError adding documents to '{collection_name}': {e}"
        logger.error(message, exc_info=True)
        raise DocumentStoreError(message) from e
    except (DocumentError, DocumentStoreError):
        raise
    except Exception as e:
        message = f"Unexpected error adding documents to '{collection_name}': {e}"
        logger.error(message, exc_info=True)
        raise DocumentStoreError(message) from e
    finally:
        # Close file handles we opened (not stdin).
        if "file_obj" in locals() and file_obj not in (sys.stdin,):
            try:
                file_obj.close()
            except Exception:
                pass

def remove_documents(# Renamed function
    client: SolrClient, 
    collection_name: str, 
    id_file: Optional[str], 
    ids: Optional[str], 
    query: Optional[str],
    commit: bool
) -> Tuple[bool, str]:
    """Remove documents using the SolrClient.""" # Updated docstring
    # ... (keep existing function logic) ...
    # Load document IDs or query
    delete_ids = None
    delete_query = None
    source_desc = ""

    if id_file:
        source_desc = f"IDs from file '{id_file}'"
        delete_ids = _load_ids_from_file(id_file)
    elif ids:
        source_desc = "provided IDs list"
        delete_ids = [doc_id.strip() for doc_id in ids.split(',') if doc_id.strip()]
    elif query:
        source_desc = f"query '{query}'"
        delete_query = query
    else:
        # This case should be caught by Click validation, but good to have safeguard
        raise DocumentError(collection_name, "Either --ids, --id-file, or --query is required for deletion.")

    num_items = len(delete_ids) if delete_ids is not None else "matching query"
    logger.info(f"Deleting {num_items} documents based on {source_desc} from collection '{collection_name}'. Commit={commit}")

    try:
        # Call the client method 
        client.delete_documents(
            collection_name=collection_name, 
            ids=delete_ids,
            query=delete_query,
            commit=commit
        )
        message = f"Successfully deleted documents based on {source_desc} from collection '{collection_name}'."
        logger.info(message)
        return (True, message)

    except SolrError as e:
         message = f"SolrError deleting documents from '{collection_name}': {e}"
         logger.error(message, exc_info=True)
         raise DocumentStoreError(message) from e 
    except (DocumentError, DocumentStoreError):
        raise 
    except Exception as e:
        message = f"Unexpected error deleting documents from '{collection_name}': {e}"
        logger.error(message, exc_info=True)
        raise DocumentStoreError(message) from e

__all__ = ["add_documents", "remove_documents"] # Updated __all__ 
