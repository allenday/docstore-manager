# Core components 
from .exceptions import (
    DocumentStoreError, 
    ConfigurationError, 
    ConnectionError, 
    CollectionError,
    CollectionAlreadyExistsError,
    CollectionNotFoundError,
    DocumentError,
    DocumentValidationError,
    BatchOperationError,
    QueryError,
    FileOperationError,
    FileParseError
)
from .logging import setup_logging
# Import config functions from .config.base
from .config.base import get_config_dir, get_profiles, load_config, DEFAULT_CONFIG_PATH

__all__ = [
    # Exceptions
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
    "FileParseError",
    # Logging
    'setup_logging',
    # Config
    'get_config_dir',
    'get_profiles',
    'load_config', 
    'DEFAULT_CONFIG_PATH'
] 