"""Base command handler for document store operations.

This module provides an abstract base class that defines the interface for document store
command handlers. Both Qdrant and Solr implementations will extend this class to provide
their specific implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class CommandResponse:
    """Standard response format for command operations."""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None


class DocumentStoreCommand(ABC):
    """Abstract base class for document store command handlers."""

    @abstractmethod
    def create_collection(self, name: str, **kwargs) -> CommandResponse:
        """Create a new collection.
        
        Args:
            name: Name of the collection to create
            **kwargs: Additional implementation-specific parameters
            
        Returns:
            CommandResponse with operation result
        """
        pass

    @abstractmethod
    def delete_collection(self, name: str) -> CommandResponse:
        """Delete an existing collection.
        
        Args:
            name: Name of the collection to delete
            
        Returns:
            CommandResponse with operation result
        """
        pass

    @abstractmethod
    def list_collections(self) -> CommandResponse:
        """List all available collections.
        
        Returns:
            CommandResponse with list of collections
        """
        pass

    @abstractmethod
    def get_collection_info(self, name: str) -> CommandResponse:
        """Get detailed information about a collection.
        
        Args:
            name: Name of the collection
            
        Returns:
            CommandResponse with collection details
        """
        pass

    @abstractmethod
    def add_documents(self, collection: str, documents: List[Dict[str, Any]], 
                     batch_size: int = 100) -> CommandResponse:
        """Add documents to a collection.
        
        Args:
            collection: Name of the target collection
            documents: List of documents to add
            batch_size: Number of documents to process in each batch
            
        Returns:
            CommandResponse with operation result
        """
        pass

    @abstractmethod
    def delete_documents(self, collection: str, 
                        ids: Optional[List[str]] = None,
                        query: Optional[str] = None) -> CommandResponse:
        """Delete documents from a collection.
        
        Args:
            collection: Name of the target collection
            ids: Optional list of document IDs to delete
            query: Optional query string to filter documents for deletion
            
        Returns:
            CommandResponse with operation result
        """
        pass

    @abstractmethod
    def get_documents(self, collection: str, 
                     ids: Optional[List[str]] = None,
                     query: Optional[str] = None,
                     fields: Optional[List[str]] = None,
                     limit: int = 10) -> CommandResponse:
        """Retrieve documents from a collection.
        
        Args:
            collection: Name of the target collection
            ids: Optional list of document IDs to retrieve
            query: Optional query string to filter documents
            fields: Optional list of fields to return
            limit: Maximum number of documents to return
            
        Returns:
            CommandResponse with matching documents
        """
        pass

    @abstractmethod
    def search_documents(self, collection: str,
                        vector: Optional[List[float]] = None,
                        query: Optional[str] = None,
                        fields: Optional[List[str]] = None,
                        limit: int = 10,
                        score_threshold: Optional[float] = None) -> CommandResponse:
        """Search for documents in a collection.
        
        Args:
            collection: Name of the target collection
            vector: Optional vector for similarity search
            query: Optional query string for filtering
            fields: Optional list of fields to return
            limit: Maximum number of documents to return
            score_threshold: Optional minimum similarity score threshold
            
        Returns:
            CommandResponse with search results
        """
        pass

    @abstractmethod
    def get_config(self) -> CommandResponse:
        """Get the current configuration.
        
        Returns:
            CommandResponse with configuration details
        """
        pass

    @abstractmethod
    def update_config(self, config: Dict[str, Any]) -> CommandResponse:
        """Update the configuration.
        
        Args:
            config: Dictionary of configuration updates
            
        Returns:
            CommandResponse with operation result
        """
        pass 