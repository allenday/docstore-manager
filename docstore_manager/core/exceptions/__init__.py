# Custom exceptions

class DocumentStoreError(Exception):
    """Base class for all document store related errors."""
    def __init__(self, message="An error occurred with the document store", details=None):
        super().__init__(message)
        self.details = details

class ConfigurationError(DocumentStoreError):
    """Error related to configuration loading or validation."""
    def __init__(self, message="Configuration error", details=None):
        super().__init__(message, details)

class ConnectionError(DocumentStoreError):
    """Error related to connecting to the document store."""
    pass

class CollectionError(DocumentStoreError):
    """Error related to collection operations."""
    pass

class CollectionAlreadyExistsError(CollectionError):
    """Specific error when attempting to create a collection that already exists."""
    pass

class CollectionNotFoundError(CollectionError):
    """Specific error when a collection is not found."""
    pass

class DocumentError(DocumentStoreError):
    """Error related to document operations."""
    pass

class DocumentValidationError(DocumentError):
    """Error related to document validation."""
    pass

class BatchOperationError(DocumentError):
    """Error during batch document operations."""
    pass
    
class QueryError(DocumentStoreError):
     """Error related to query operations."""
     pass 

class FileOperationError(DocumentStoreError):
    """Error related to file operations (e.g., reading/writing JSON)."""
    pass

class FileParseError(FileOperationError):
    """Specific error when parsing a file fails (e.g., invalid JSON)."""
    pass

__all__ = [
    "DocumentStoreError",
    "ConfigurationError",
    "ConnectionError",
    "CollectionError",
    "CollectionAlreadyExistsError",
    "CollectionNotFoundError",
    "DocumentError",
    "DocumentValidationError",
    "BatchOperationError",
    "QueryError",
    "FileOperationError",
    "FileParseError"
] 