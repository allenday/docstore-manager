"""Exports Solr command functions."""

from docstore_manager.solr.commands.list import list_collections
from docstore_manager.solr.commands.create import create_collection
from docstore_manager.solr.commands.delete import delete_collection
from docstore_manager.solr.commands.info import collection_info
from docstore_manager.solr.commands.documents import add_documents, remove_documents
from docstore_manager.solr.commands.get import get_documents
from docstore_manager.solr.commands.config import show_config_info
from docstore_manager.solr.commands.search import search_documents

__all__ = [
    "list_collections",
    "create_collection",
    "delete_collection",
    "collection_info",
    "add_documents",
    "remove_documents",
    "get_documents",
    "show_config_info",
    "search_documents",
] 