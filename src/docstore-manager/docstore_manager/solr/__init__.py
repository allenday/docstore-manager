"""
Solr document store implementation.

This module provides client, command, and formatter implementations for interacting
with Apache Solr document stores. It includes classes for managing Solr collections,
documents, and search operations.
"""

from docstore_manager.solr.client import SolrClient
from docstore_manager.solr.command import SolrCommand
from docstore_manager.solr.format import SolrFormatter

__all__ = [
    "SolrClient",
    "SolrCommand",
    "SolrFormatter",
]
