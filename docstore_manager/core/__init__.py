# Core components 
from docstore_manager.core.exceptions import (
    DocstoreManagerException, 
    DocumentStoreError, 
    ConfigurationError, 
    ConnectionError, 
    CollectionError,
    CollectionAlreadyExistsError,
    CollectionDoesNotExistError,
    CollectionOperationError,
    DocumentError,
    DocumentOperationError,
    InvalidInputError
)
from docstore_manager.core.logging import setup_logging
from docstore_manager.core.config.base import (
    get_config_dir, 
    get_profiles, 
    load_config, 
)

__all__ = [
    # Exceptions
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
    # Logging
    'setup_logging',
    # Config
    'get_config_dir',
    'get_profiles',
    'load_config', 
]

# This file makes the directory a Python package 