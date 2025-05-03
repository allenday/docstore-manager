"""
Standardized client interface for document stores.

This module defines a standardized interface for document store clients,
ensuring consistent method signatures, parameter names, and return types
across different document store implementations.
"""

import abc
from typing import Any, Dict, List, Optional, Union


class DocumentStoreClient(abc.ABC):
    """
    Abstract base class for document store client implementations.
    
    This class defines a standardized interface for document store clients,
    ensuring consistent method signatures, parameter names, and return types
    across different document store implementations (e.g., Qdrant, Solr).
    
    All document store client implementations should inherit from this class
    and implement its abstract methods.
    """

    @abc.abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the client with configuration.
        
        Args:
            config: Configuration dictionary containing connection parameters.
        
        Raises:
            ConfigurationError: If the configuration is invalid.
            ConnectionError: If the connection to the document store cannot be established.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def client(self) -> Any:
        """
        Provides access to the underlying native client instance.
        
        Returns:
            The underlying native client instance.
        
        Raises:
            ConnectionError: If the client is not initialized.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def is_healthy(self) -> bool:
        """
        Check if the connection to the document store is healthy.
        
        Returns:
            True if the connection is healthy, False otherwise.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def list_collections(self) -> List[Dict[str, Any]]:
        """
        List all collections in the document store.
        
        Returns:
            A list of dictionaries, each containing information about a collection.
            Each dictionary must have at least a 'name' key.
        
        Raises:
            CollectionError: If the operation fails.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def create_collection(
        self, 
        name: str, 
        **kwargs
    ) -> None:
        """
        Create a new collection in the document store.
        
        Args:
            name: The name of the collection to create.
            **kwargs: Additional keyword arguments for specific implementations.
                Common parameters include:
                - vector_size: The dimension of vectors (for vector databases).
                - distance_metric: The distance metric to use (for vector databases).
                - num_shards: The number of shards for the collection.
                - replication_factor: The replication factor for the collection.
                - on_disk_payload: Whether to store payload on disk (for vector databases).
        
        Raises:
            CollectionError: If the collection creation fails.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete_collection(self, name: str) -> None:
        """
        Delete a collection from the document store.
        
        Args:
            name: The name of the collection to delete.
        
        Raises:
            CollectionError: If the collection deletion fails.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_collection(self, name: str) -> Dict[str, Any]:
        """
        Get detailed information about a collection.
        
        Args:
            name: The name of the collection to get information about.
        
        Returns:
            A dictionary containing information about the collection.
        
        Raises:
            CollectionError: If the collection retrieval fails.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def add_documents(
        self, 
        collection: str, 
        documents: List[Dict[str, Any]], 
        batch_size: int = 100,
        **kwargs
    ) -> None:
        """
        Add documents to a collection.
        
        Args:
            collection: The name of the collection to add documents to.
            documents: A list of documents to add. Each document must be a dictionary.
            batch_size: The number of documents to process in each batch. Defaults to 100.
            **kwargs: Additional keyword arguments for specific implementations.
                Common parameters include:
                - commit: Whether to commit the changes immediately (for Solr).
        
        Raises:
            DocumentError: If the document addition fails.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete_documents(
        self, 
        collection: str, 
        ids: Optional[List[str]] = None, 
        query: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """
        Delete documents from a collection.
        
        Args:
            collection: The name of the collection to delete documents from.
            ids: A list of document IDs to delete. If None, query must be provided.
            query: A query to select documents to delete. If None, ids must be provided.
            **kwargs: Additional keyword arguments for specific implementations.
                Common parameters include:
                - commit: Whether to commit the changes immediately (for Solr).
        
        Raises:
            DocumentError: If the document deletion fails.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_documents(
        self, 
        collection: str, 
        ids: Optional[List[str]] = None, 
        query: Optional[Dict[str, Any]] = None,
        with_vectors: bool = False,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Get documents from a collection.
        
        Args:
            collection: The name of the collection to get documents from.
            ids: A list of document IDs to get. If None, query must be provided.
            query: A query to select documents to get. If None, ids must be provided.
            with_vectors: Whether to include vectors in the returned documents.
            **kwargs: Additional keyword arguments for specific implementations.
                Common parameters include:
                - fields: A list of fields to include in the returned documents (for Solr).
                - limit: The maximum number of documents to return.
        
        Returns:
            A list of documents.
        
        Raises:
            DocumentError: If the document retrieval fails.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def search_documents(
        self, 
        collection: str, 
        query: Dict[str, Any], 
        limit: int = 10,
        with_vectors: bool = False,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for documents in a collection.
        
        Args:
            collection: The name of the collection to search in.
            query: The search query. For vector databases, this should include a 'vector' field.
                For text databases, this should include a 'text' field.
            limit: The maximum number of results to return. Defaults to 10.
            with_vectors: Whether to include vectors in the returned documents.
            **kwargs: Additional keyword arguments for specific implementations.
        
        Returns:
            A list of documents matching the search criteria.
        
        Raises:
            DocumentError: If the search operation fails.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def count_documents(
        self, 
        collection: str, 
        query: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count documents in a collection.
        
        Args:
            collection: The name of the collection to count documents in.
            query: A query to filter the documents to count. If None, counts all documents.
        
        Returns:
            The number of documents matching the query.
        
        Raises:
            DocumentError: If the count operation fails.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> None:
        """
        Close the client connection.
        
        This method should be called when the client is no longer needed to release resources.
        """
        raise NotImplementedError
