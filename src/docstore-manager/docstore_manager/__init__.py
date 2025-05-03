"""
Document Store Manager.

This package provides a unified interface for interacting with various document stores,
including vector databases like Qdrant and search engines like Solr. It includes
client, command, and formatter implementations for each supported document store.

The package is designed to be extensible, allowing for easy addition of new document
store implementations while maintaining a consistent interface.
"""

# Core interfaces
from docstore_manager.core import (
    BaseDocumentStoreFormatter,
    CommandResponse,
    DocumentStoreClient,
    DocumentStoreCommand,
    DocumentStoreFormatter,
)

# Qdrant implementation
from docstore_manager.qdrant import QdrantCommand, QdrantDocumentStore, QdrantFormatter

# Solr implementation
from docstore_manager.solr import SolrClient, SolrCommand, SolrFormatter

__version__ = "0.1.0"

__all__ = [
    # Core interfaces
    "DocumentStoreClient",
    "DocumentStoreCommand",
    "CommandResponse",
    "DocumentStoreFormatter",
    "BaseDocumentStoreFormatter",
    # Qdrant implementation
    "QdrantDocumentStore",
    "QdrantCommand",
    "QdrantFormatter",
    # Solr implementation
    "SolrClient",
    "SolrCommand",
    "SolrFormatter",
]
