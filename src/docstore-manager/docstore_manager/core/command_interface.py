"""
Standardized command interface for document stores.

This module defines a standardized interface for document store commands,
ensuring consistent method signatures, parameter names, and return types
across different document store implementations.
"""

import abc
from typing import Any, Dict, List, Optional, TextIO, Union

from docstore_manager.core.client_interface import DocumentStoreClient
from docstore_manager.core.response import Response


class CommandResponse(Response):
    """
    Standardized response object for command results.
    
    This class extends the base Response class to provide a consistent
    structure for command results across different document store implementations.
    
    Attributes:
        success (bool): Whether the command was successful.
        message (str): A message describing the result of the command.
        data (Optional[Any]): The data returned by the command, if any.
        error (Optional[str]): An error message if the command failed.
    """
    
    def __init__(
        self,
        success: bool,
        message: str,
        data: Optional[Any] = None,
        error: Optional[str] = None
    ):
        """
        Initialize a CommandResponse.
        
        Args:
            success: Whether the command was successful.
            message: A message describing the result of the command.
            data: The data returned by the command, if any.
            error: An error message if the command failed.
        """
        super().__init__(success=success, message=message, data=data, error=error)


class DocumentStoreCommand(abc.ABC):
    """
    Abstract base class for document store command implementations.
    
    This class defines a standardized interface for document store commands,
    ensuring consistent method signatures, parameter names, and return types
    across different document store implementations (e.g., Qdrant, Solr).
    
    All document store command implementations should inherit from this class
    and implement its abstract methods.
    """

    def __init__(self):
        """Initialize the command handler."""
        self.client = None
        self.logger = None

    @abc.abstractmethod
    def initialize(self, client: DocumentStoreClient) -> None:
        """
        Initialize the command handler with a client.
        
        Args:
            client: The document store client to use for executing commands.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def list_collections(self) -> CommandResponse:
        """
        List all collections in the document store.
        
        Returns:
            CommandResponse containing a list of collection information dictionaries.
            Each dictionary should have at least a 'name' key.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def create_collection(
        self,
        name: str,
        **kwargs
    ) -> CommandResponse:
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
                - overwrite: Whether to overwrite the collection if it already exists.
        
        Returns:
            CommandResponse indicating success or failure.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete_collection(self, name: str) -> CommandResponse:
        """
        Delete a collection from the document store.
        
        Args:
            name: The name of the collection to delete.
        
        Returns:
            CommandResponse indicating success or failure.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_collection(self, name: str) -> CommandResponse:
        """
        Get detailed information about a collection.
        
        Args:
            name: The name of the collection to get information about.
        
        Returns:
            CommandResponse containing information about the collection.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def add_documents(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 100,
        **kwargs
    ) -> CommandResponse:
        """
        Add documents to a collection.
        
        Args:
            collection: The name of the collection to add documents to.
            documents: A list of documents to add. Each document must be a dictionary.
            batch_size: The number of documents to process in each batch. Defaults to 100.
            **kwargs: Additional keyword arguments for specific implementations.
                Common parameters include:
                - commit: Whether to commit the changes immediately (for Solr).
        
        Returns:
            CommandResponse indicating success or failure.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete_documents(
        self,
        collection: str,
        ids: Optional[List[str]] = None,
        query: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> CommandResponse:
        """
        Delete documents from a collection.
        
        Args:
            collection: The name of the collection to delete documents from.
            ids: A list of document IDs to delete. If None, query must be provided.
            query: A query to select documents to delete. If None, ids must be provided.
            **kwargs: Additional keyword arguments for specific implementations.
                Common parameters include:
                - commit: Whether to commit the changes immediately (for Solr).
        
        Returns:
            CommandResponse indicating success or failure.
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
    ) -> CommandResponse:
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
            CommandResponse containing the retrieved documents.
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
    ) -> CommandResponse:
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
            CommandResponse containing the search results.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def count_documents(
        self,
        collection: str,
        query: Optional[Dict[str, Any]] = None
    ) -> CommandResponse:
        """
        Count documents in a collection.
        
        Args:
            collection: The name of the collection to count documents in.
            query: A query to filter the documents to count. If None, counts all documents.
        
        Returns:
            CommandResponse containing the count.
        """
        raise NotImplementedError

    def _write_output(
        self,
        data: Any,
        output: Optional[Union[str, TextIO]] = None,
        format: str = "json"
    ) -> None:
        """
        Write command output to a file or stdout.
        
        Args:
            data: The data to write.
            output: The output destination. Can be a file path or a file-like object.
                If None, writes to stdout.
            format: The output format. Defaults to "json".
        
        Raises:
            Exception: If the output writing fails.
        """
        # This method can be implemented in the base class
        # or left for specific implementations
        raise NotImplementedError
