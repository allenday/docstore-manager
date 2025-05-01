"""Core exceptions for the document store manager."""

# Base exception class
class DocstoreManagerException(Exception):
    """Base exception for all project-specific errors."""
    def __init__(self, message="An error occurred in docstore-manager", details=None):
        super().__init__(message)
        self.details = details

# Custom exceptions

class DocumentStoreError(Exception):
    """Base exception for document store related errors."""
    def __init__(self, message="Document store error", details=None):
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
    """Raised when trying to create a collection that already exists."""
    pass

class CollectionDoesNotExistError(CollectionError):
    """Raised when trying to operate on a non-existent collection."""
    pass

class CollectionOperationError(CollectionError):
    """General error during a collection operation (e.g., create, delete)."""
    pass

class DocumentError(DocumentStoreError):
    """Error related to document operations."""
    pass

class DocumentOperationError(DocumentError):
    """General error during a document operation (e.g., add, delete, update)."""
    pass

class InvalidInputError(DocstoreManagerException):
    """Error related to invalid user input or command arguments."""
    pass

__all__ = [
    "DocstoreManagerException",
    "DocumentStoreError",
    "ConfigurationError",
    "ConnectionError",
    "CollectionError",
    "CollectionAlreadyExistsError",
    "CollectionDoesNotExistError",
    "CollectionOperationError",
    "DocumentError",
    "DocumentOperationError",
    "InvalidInputError",
] 