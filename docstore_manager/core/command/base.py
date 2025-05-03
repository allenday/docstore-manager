"""Base command functionality for document store operations."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List, Union

from docstore_manager.core.exceptions import (
    DocumentStoreError,
    CollectionError,
    CollectionDoesNotExistError,
    DocumentError,
    InvalidInputError
)
from docstore_manager.core.utils import (
    load_documents_from_file,
    load_ids_from_file,
    parse_json_string,
    write_output
)

logger = logging.getLogger(__name__)

@dataclass
class CommandResponse:
    """Response from a document store command."""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class DocumentStoreCommand:
    """Base class for document store commands."""

    def __init__(self):
        """Initialize the command handler."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_response(
        self,
        success: bool,
        message: str,
        data: Optional[Any] = None,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> CommandResponse:
        """Create a command response.
        
        Args:
            success: Whether the command succeeded
            message: Response message
            data: Optional response data
            error: Optional error message
            details: Optional error details
            
        Returns:
            CommandResponse instance
        """
        return CommandResponse(
            success=success,
            message=message,
            data=data,
            error=error,
            details=details
        )

    def _load_documents(
        self,
        collection: str,
        docs_file: Optional[str] = None,
        docs_str: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Load documents from file or string.
        
        Args:
            collection: Collection name (for error context)
            docs_file: Path to documents file
            docs_str: JSON string containing documents
            
        Returns:
            List of documents
            
        Raises:
            DocumentError: If no documents source provided or invalid format
            FileOperationError: If file cannot be read
            FileParseError: If JSON parsing fails
        """
        if docs_file:
            try:
                return load_documents_from_file(docs_file)
            except (DocumentStoreError, InvalidInputError) as e:
                raise DocumentError(
                    collection_name=collection,
                    message=f"Failed to load documents from file '{docs_file}': {e}",
                    details={'file': docs_file},
                    original_exception=e
                )
        elif docs_str:
            try:
                docs = parse_json_string(docs_str, "documents")
                if not isinstance(docs, list):
                    raise InvalidInputError(
                        f"Documents JSON must be an array (list), got {type(docs).__name__}",
                        details={'input_type': type(docs).__name__}
                    )
                return docs
            except InvalidInputError as e:
                raise InvalidInputError(f"Failed to parse documents JSON for collection '{collection}': {e}", details=e.details, original_exception=e)
        else:
            raise InvalidInputError("Either --documents-file or --documents must be provided.")

    def _load_ids(
        self,
        collection: str,
        ids_file: Optional[str] = None,
        ids_str: Optional[str] = None
    ) -> Optional[List[str]]:
        """Load document IDs from file or string.
        
        Args:
            collection: Collection name (for error context)
            ids_file: Path to IDs file
            ids_str: Comma-separated IDs string
            
        Returns:
            List of document IDs or None if no IDs provided
            
        Raises:
            DocumentError: If IDs are invalid
            FileOperationError: If file cannot be read
        """
        if ids_file:
            try:
                return load_ids_from_file(ids_file)
            except DocumentStoreError as e:
                raise DocumentError(
                    collection_name=collection,
                    message=f"Failed to load IDs from file '{ids_file}': {e}",
                    details={'file': ids_file},
                    original_exception=e
                )
        elif ids_str:
            ids = [id.strip() for id in ids_str.split(',') if id.strip()]
            if not ids:
                raise InvalidInputError(
                    f"No valid document IDs provided in input for collection '{collection}'",
                    details={'ids_input': ids_str}
                )
            return ids
        return None

    def _parse_query(
        self,
        collection: str,
        query_str: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Parse a query string.
        
        Args:
            collection: Collection name (for error context)
            query_str: Query string in JSON format
            
        Returns:
            Parsed query dict or None if no query provided
            
        Raises:
            QueryError: If query parsing fails
        """
        if not query_str:
            return None
            
        try:
            return parse_json_string(query_str, "query")
        except InvalidInputError as e:
            raise InvalidInputError(f"Failed to parse query JSON for collection '{collection}': {e}", details=e.details, original_exception=e)

    def _write_output(
        self,
        data: Any,
        output: Optional[Union[str, Any]] = None,
        format: str = 'json'
    ) -> None:
        """Write command output.
        
        Args:
            data: Data to write
            output: Output file path or file-like object
            format: Output format ('json' or 'csv')
            
        Raises:
            FileOperationError: If output cannot be written
        """
        try:
            # If the input data is a CommandResponse, extract the actual data
            data_to_write = data.data if isinstance(data, CommandResponse) else data
            
            # Call the utility function with the extracted data
            write_output(data_to_write, output, format)
        except DocumentStoreError as e:
            raise DocumentStoreError(f"Failed to write output: {e}", details=e.details, original_exception=e)
        except ValueError as e:
            raise InvalidInputError(f"Output format error: {e}") 