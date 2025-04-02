"""Exceptions for document store operations."""

from typing import Optional, Any, Dict

class DocumentStoreError(Exception):
    """Base exception for all document store errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}

class ConfigurationError(DocumentStoreError):
    """Raised when there is a configuration error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)

class ConnectionError(DocumentStoreError):
    """Raised when there is a connection error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)

class CollectionError(DocumentStoreError):
    """Base class for collection-related errors."""
    def __init__(self, collection: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.collection = collection

class CollectionNotFoundError(CollectionError):
    """Raised when a collection does not exist."""
    pass

class CollectionAlreadyExistsError(CollectionError):
    """Raised when attempting to create a collection that already exists."""
    pass

class CollectionOperationError(CollectionError):
    """Raised when a collection operation fails."""
    pass

class DocumentError(DocumentStoreError):
    """Base class for document-related errors."""
    def __init__(self, collection: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.collection = collection

class DocumentNotFoundError(DocumentError):
    """Raised when a document does not exist."""
    def __init__(self, collection: str, doc_id: str, message: Optional[str] = None):
        super().__init__(
            collection,
            message or f"Document '{doc_id}' not found in collection '{collection}'",
            {'doc_id': doc_id}
        )
        self.doc_id = doc_id

class DocumentValidationError(DocumentError):
    """Raised when document validation fails."""
    def __init__(self, collection: str, errors: Dict[str, Any], message: Optional[str] = None):
        super().__init__(
            collection,
            message or f"Document validation failed for collection '{collection}'",
            {'validation_errors': errors}
        )
        self.validation_errors = errors

class BatchOperationError(DocumentError):
    """Raised when a batch operation fails."""
    def __init__(self, collection: str, operation: str, failed_items: Dict[str, Any], message: Optional[str] = None):
        super().__init__(
            collection,
            message or f"Batch {operation} operation failed for collection '{collection}'",
            {'failed_items': failed_items}
        )
        self.operation = operation
        self.failed_items = failed_items

class FileOperationError(DocumentStoreError):
    """Base class for file operation errors."""
    def __init__(self, file_path: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.file_path = file_path

class FileNotFoundError(FileOperationError):
    """Raised when a file is not found."""
    def __init__(self, file_path: str):
        super().__init__(file_path, f"File not found: {file_path}")

class FileParseError(FileOperationError):
    """Raised when file parsing fails."""
    def __init__(self, file_path: str, format_type: str, parse_error: str):
        super().__init__(
            file_path,
            f"Failed to parse {format_type} file: {file_path}",
            {'format': format_type, 'parse_error': parse_error}
        )
        self.format_type = format_type
        self.parse_error = parse_error

class QueryError(DocumentStoreError):
    """Base class for query-related errors."""
    def __init__(self, query: Any, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.query = query

class QueryParseError(QueryError):
    """Raised when query parsing fails."""
    pass

class QueryValidationError(QueryError):
    """Raised when query validation fails."""
    pass