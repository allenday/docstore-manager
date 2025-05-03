"""Core exceptions for the document store manager."""

# Base exception class
class DocstoreManagerException(Exception):
    """Base exception for all project-specific errors."""
    def __init__(self, message="An error occurred in docstore-manager", details=None, original_exception=None):
        super().__init__(message)
        self.message = message # Store message explicitly
        self.details = details if details is not None else {} # Initialize details correctly
        self.original_exception = original_exception

    def __str__(self):
        return self.message # Ensure __str__ returns the message

# Custom exceptions

class DocumentStoreError(DocstoreManagerException): # Inherit from base manager exception
    """Base exception for document store related errors."""
    def __init__(self, message="Document store error", details=None, original_exception=None):
        # No collection_name at this level
        super().__init__(message, details, original_exception)

class ConfigurationError(DocumentStoreError):
    """Error related to configuration loading or validation."""
    def __init__(self, message="Configuration error", details=None, original_exception=None):
        super().__init__(message, details, original_exception)

class ConnectionError(DocumentStoreError):
    """Error related to connecting to the document store."""
    # No need to override init if base is sufficient
    pass

class CollectionError(DocumentStoreError):
    """Base exception for collection-related errors."""
    def __init__(self, collection_name: str, message="Collection error", details=None, original_exception=None):
        # Pass the potentially custom message up to the parent constructor
        super().__init__(message, details, original_exception)
        # Store the collection name under the 'collection' attribute as expected by tests
        self.collection = collection_name
        # DO NOT automatically add collection to details if details is empty
        # Only add if details is provided and doesn't already contain it
        if details is not None and 'collection' not in self.details:
             self.details['collection'] = collection_name


class CollectionAlreadyExistsError(CollectionError):
    """Raised when trying to create a collection that already exists."""
    def __init__(self, collection_name: str, message=None, details=None, original_exception=None):
        # Determine the final message to be used.
        final_message = message if message is not None else f"Collection '{collection_name}' already exists."
        # Pass the final determined message UP the chain.
        super().__init__(collection_name=collection_name, message=final_message, details=details, original_exception=original_exception)
        # No need to set self.message here, base class handles it.

class CollectionDoesNotExistError(CollectionError):
    """Raised when trying to operate on a non-existent collection."""
    def __init__(self, collection_name: str, message=None, details=None, original_exception=None):
        # Determine the final message to be used.
        final_message = message if message is not None else f"Collection '{collection_name}' does not exist."
        # Pass the final determined message UP the chain.
        super().__init__(collection_name=collection_name, message=final_message, details=details, original_exception=original_exception)
        # Add collection_name attribute to match test expectations
        self.collection_name = collection_name

class CollectionOperationError(CollectionError):
    """General error during a collection operation (e.g., create, delete)."""
    def __init__(self, collection_name: str, message="Collection operation error", details=None, original_exception=None):
        # Pass the message directly up
        super().__init__(collection_name, message, details, original_exception)


class DocumentError(DocumentStoreError):
    """Base exception for document-related errors."""
    def __init__(self, collection_name: str = None, message="Document error", details=None, original_exception=None):
        # Initialize details if None, otherwise ensure it's a dictionary
        if details is None:
            error_details = {}
        elif isinstance(details, dict):
            error_details = details.copy() # Work on a copy
        else:
            # If details is not a dict (e.g., a string), store it under a default key
            error_details = {'original_details': details}
        
        # Pass the provided message and potentially updated details UP the chain.
        super().__init__(message=message, details=error_details, original_exception=original_exception)
        
        # Reinstate direct attribute for easier access in tests
        self.collection_name = collection_name
        # Add collection attribute to match test expectations
        self.collection = collection_name

class DocumentOperationError(DocumentError):
    """General error during a document operation (e.g., add, delete, update)."""
    # Inherits __init__ from DocumentError, which is now correct
    pass


class InvalidInputError(DocumentStoreError): # Changed inheritance
    """Error related to invalid user input or command arguments."""
    # No need to override init if base DocumentStoreError init is sufficient
    # (or DocstoreManagerException if that was intended)
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
