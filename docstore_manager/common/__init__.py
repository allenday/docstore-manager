"""
Common functionality for document store managers.

This package provides shared functionality that can be used across different
document store implementations (e.g., Qdrant, Solr).

Modules:
    cli: Common CLI functionality and base classes
    config: Configuration management
    exceptions: Common exception types
    formatting: Output formatting utilities
    logging: Logging configuration
"""

from .cli import BaseCLI
from .exceptions import (
    DocumentStoreError,
    ConfigurationError,
    ConnectionError,
    CollectionError,
    DocumentError,
    DocumentValidationError,
    QueryValidationError
)
from .logging import setup_logging

__all__ = [
    'BaseCLI',
    'DocumentStoreError',
    'ConfigurationError',
    'ConnectionError',
    'CollectionError',
    'DocumentError',
    'DocumentValidationError',
    'QueryValidationError',
    'setup_logging'
] 