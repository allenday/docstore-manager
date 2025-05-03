# Core components
from docstore_manager.core.client_interface import DocumentStoreClient
from docstore_manager.core.command_interface import CommandResponse, DocumentStoreCommand
from docstore_manager.core.config.base import get_config_dir, get_profiles, load_config
from docstore_manager.core.exceptions import (
    CollectionAlreadyExistsError,
    CollectionDoesNotExistError,
    CollectionError,
    CollectionOperationError,
    ConfigurationError,
    ConnectionError,
    DocstoreManagerException,
    DocumentError,
    DocumentOperationError,
    DocumentStoreError,
    InvalidInputError,
)
from docstore_manager.core.format.base import DocumentStoreFormatter
from docstore_manager.core.format.base_formatter import BaseDocumentStoreFormatter
from docstore_manager.core.logging import setup_logging
from docstore_manager.core.response import Response

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
    "setup_logging",
    # Config
    "get_config_dir",
    "get_profiles",
    "load_config",
    # Interfaces
    "DocumentStoreClient",
    "DocumentStoreCommand",
    "CommandResponse",
    "DocumentStoreFormatter",
    "BaseDocumentStoreFormatter",
    "Response",
]

# This file makes the directory a Python package
