"""
Common exceptions for document store managers.
"""

class DocumentStoreError(Exception):
    """Base exception for document store errors."""
    pass

class ConfigurationError(DocumentStoreError):
    """Raised when there is a configuration error."""
    pass

class ConnectionError(DocumentStoreError):
    """Raised when there is a connection error."""
    pass

class CollectionError(DocumentStoreError):
    """Raised when there is an error with collection operations."""
    pass

class DocumentError(DocumentStoreError):
    """Raised when there is an error with document operations."""
    pass

class ValidationError(DocumentStoreError):
    """Raised when there is a validation error."""
    pass 