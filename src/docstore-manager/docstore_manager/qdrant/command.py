"""
Qdrant command implementation.

This module provides command implementations for interacting with Qdrant vector database.
It includes a QdrantCommand class that implements the DocumentStoreCommand interface
for Qdrant-specific operations.

The module handles various operations such as creating and managing collections,
adding, retrieving, searching, and deleting documents in Qdrant collections.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Union

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    HnswConfigDiff,
    OptimizersConfigDiff,
    CollectionStatus,
    UpdateStatus,
)
from qdrant_client.models import Filter, PointStruct

from docstore_manager.core.command import DocumentStoreCommand
from docstore_manager.core.exceptions import (
    CollectionError,
    DocumentError,
    DocumentStoreError,
    InvalidInputError
)
from docstore_manager.core.response import Response
from docstore_manager.qdrant.client import QdrantDocumentStore

class QdrantCommand(DocumentStoreCommand):
    """
    Qdrant command handler.
    
    This class implements the DocumentStoreCommand interface for Qdrant vector database,
    providing methods for executing commands against Qdrant collections and documents.
    It handles operations such as creating and managing collections, adding, retrieving,
    searching, and deleting documents.
    
    Attributes:
        client (QdrantDocumentStore): The Qdrant document store client instance.
    """

    def __init__(self):
        """
        Initialize the command handler.
        
        This constructor initializes the QdrantCommand instance with a null client.
        The client must be set using the initialize method before executing commands.
        """
        super().__init__()
        self.client = None

    def initialize(self, client: QdrantDocumentStore) -> None:
        """
        Initialize the command handler with a client.

        This method sets the Qdrant document store client to be used by the command handler.

        Args:
            client (QdrantDocumentStore): The Qdrant document store client instance.
            
        Examples:
            >>> command = QdrantCommand()
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> command.initialize(client)
        """
        self.client = client

    def create_collection(
        self,
        name: str,
        dimension: int,
        distance: str = "Cosine",
        on_disk_payload: bool = False,
        hnsw_ef: Optional[int] = None,
        hnsw_m: Optional[int] = None,
        shards: Optional[int] = None,
        replication_factor: Optional[int] = None,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """
        Create or recreate a collection with detailed configuration.
        
        This method creates a new Qdrant collection with the specified parameters.
        If the collection already exists and overwrite is True, it will be recreated.
        Otherwise, an error will be returned.
        
        Args:
            name (str): The name of the collection to create.
            dimension (int): The dimension of the vector space.
            distance (str): The distance metric to use. Defaults to "Cosine".
                Options include "Cosine", "Euclid", "Dot".
            on_disk_payload (bool): Whether to store payload on disk. Defaults to False.
            hnsw_ef (Optional[int]): The ef_construct parameter for HNSW index.
                Higher values improve recall at the expense of indexing speed.
            hnsw_m (Optional[int]): The M parameter for HNSW index.
                Higher values improve recall at the expense of memory usage.
            shards (Optional[int]): The number of shards for the collection.
            replication_factor (Optional[int]): The replication factor for the collection.
            overwrite (bool): Whether to overwrite the collection if it already exists.
                Defaults to False.
                
        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
                If successful, contains 'success': True and 'message'.
                If failed, contains 'success': False and 'error'.
                
        Examples:
            >>> command = QdrantCommand()
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> command.initialize(client)
            >>> result = command.create_collection(
            ...     name="my_collection",
            ...     dimension=768,
            ...     distance="Cosine",
            ...     hnsw_ef=100,
            ...     hnsw_m=16
            ... )
            >>> print(result)
            {'success': True, 'message': "Collection 'my_collection' created successfully."}
        """
        try:
            distance_enum = getattr(Distance, distance.upper())
            vector_params = VectorParams(size=dimension, distance=distance_enum)

            hnsw_config = None
            if hnsw_ef is not None or hnsw_m is not None:
                hnsw_config = HnswConfigDiff(
                    ef_construct=hnsw_ef,
                    m=hnsw_m
                )
            
            optimizers_config = OptimizersConfigDiff() 

            if overwrite:
                operation_result = self.client.client.recreate_collection(
                    collection_name=name,
                    vectors_config=vector_params,
                    shard_number=shards,
                    replication_factor=replication_factor,
                    hnsw_config=hnsw_config,
                    optimizers_config=optimizers_config,
                    on_disk_payload=on_disk_payload,
                )
                self.logger.info(f"Recreated collection '{name}' (overwrite=True)")
                return {'success': True, 'message': f"Collection '{name}' recreated successfully."}
            else:
                collection_exists = False
                try:
                    # Check if collection exists
                    existing_collections = self.client.client.get_collections().collections
                    if name in [c.name for c in existing_collections]:
                        collection_exists = True
                except Exception as e:
                    # Log warning if check fails, but proceed to attempt creation
                    self.logger.warning(f"Could not check for existing collection '{name}': {e}")
                    # We will let the create_collection call below handle potential errors

                if collection_exists:
                    # Collection exists and overwrite is False, return error
                    self.logger.warning(f"Collection '{name}' already exists and overwrite=False.")
                    return {'success': False, 'error': f"Collection '{name}' already exists."}
                else:
                    # Collection does not exist (or check failed), proceed with creation
                    self.logger.info(f"Proceeding to create collection '{name}' (overwrite=False)")
                    operation_result = self.client.client.create_collection(
                        collection_name=name,
                        vectors_config=vector_params,
                        shard_number=shards,
                        replication_factor=replication_factor,
                        hnsw_config=hnsw_config,
                        optimizers_config=optimizers_config,
                        on_disk_payload=on_disk_payload,
                    )
                    self.logger.info(f"Create operation finished for collection '{name}'. Result: {operation_result}")
                    return {'success': operation_result, 'message': f"Collection '{name}' created successfully." if operation_result else f"Failed to create collection '{name}'."}

        except Exception as e:
            error_message = f"Failed to create/recreate collection '{name}': {str(e)}"
            self.logger.error(error_message, exc_info=True)
            # Directly return the error dict, don't rely on success/message vars here
            return {'success': False, 'error': error_message, 'details': str(e)}

    def delete_collection(self, name: str) -> None:
        """
        Delete a collection.
        
        This method deletes the specified collection from the Qdrant server.
        
        Args:
            name (str): The name of the collection to delete.
            
        Raises:
            CollectionError: If the collection deletion fails.
            
        Examples:
            >>> command = QdrantCommand()
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> command.initialize(client)
            >>> command.delete_collection("my_collection")
        """
        try:
            self.client.delete_collection(name)
            self.logger.info(f"Deleted collection '{name}'")
        except Exception as e:
            raise CollectionError(name, f"Failed to delete collection: {str(e)}")

    def list_collections(self) -> List[Dict[str, Any]]:
        """
        List all collections.
        
        This method retrieves a list of all collections available in the Qdrant server.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing information
                about a collection. Each dictionary has at least a 'name' key.
                
        Raises:
            CollectionError: If the operation fails.
            
        Examples:
            >>> command = QdrantCommand()
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> command.initialize(client)
            >>> collections = command.list_collections()
            >>> print(collections)
            [{'name': 'collection1'}, {'name': 'collection2'}]
        """
        try:
            return self.client.get_collections()
        except Exception as e:
            raise CollectionError("", f"Failed to list collections: {str(e)}")

    def get_collection(self, name: str) -> Dict[str, Any]:
        """
        Get collection details.
        
        This method retrieves detailed information about the specified collection.
        
        Args:
            name (str): The name of the collection to get details for.
            
        Returns:
            Dict[str, Any]: A dictionary containing information about the collection,
                including name, vector configuration, points count, and storage settings.
                
        Raises:
            CollectionError: If the collection retrieval fails.
            
        Examples:
            >>> command = QdrantCommand()
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> command.initialize(client)
            >>> info = command.get_collection("my_collection")
            >>> print(info)
            {
                'name': 'my_collection',
                'vectors': {'size': 768, 'distance': 'Cosine'},
                'points_count': 1000,
                'on_disk_payload': False
            }
        """
        try:
            return self.client.get_collection(name)
        except Exception as e:
            raise CollectionError(name, f"Failed to get collection: {str(e)}")

    def add_documents(self, collection: str, documents: List[Dict[str, Any]],
                     batch_size: int = 100) -> Dict[str, Any]:
        """
        Add documents to collection.
        
        This method adds or updates documents in the specified collection.
        Each document must have at least 'id' and 'vector' fields.
        
        Args:
            collection (str): The name of the collection to add documents to.
            documents (List[Dict[str, Any]]): A list of documents to add. Each document
                must be a dictionary containing at least 'id' and 'vector' fields.
                Any other fields will be stored as payload.
            batch_size (int): The number of documents to process in each batch.
                Defaults to 100.
                
        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
                If successful, contains 'success': True and 'message'.
                If failed, contains 'success': False and 'error'.
                
        Raises:
            InvalidInputError: If any document is missing required fields.
            DocumentError: If the document addition fails.
            
        Examples:
            >>> command = QdrantCommand()
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> command.initialize(client)
            >>> documents = [
            ...     {"id": "doc1", "vector": [0.1, 0.2, 0.3], "text": "Document 1"},
            ...     {"id": "doc2", "vector": [0.4, 0.5, 0.6], "text": "Document 2"}
            ... ]
            >>> result = command.add_documents("my_collection", documents)
            >>> print(result)
            {'success': True, 'message': "Successfully added 2 documents."}
        """
        try:
            points = []
            for doc in documents:
                if "id" not in doc or "vector" not in doc:
                    raise InvalidInputError(
                        f"Document missing 'id' or 'vector' field in collection '{collection}'. Document: {doc}",
                        details={"collection": collection, "document_preview": str(doc)[:100]}
                    )
                
                point = PointStruct(
                    id=doc["id"],
                    vector=doc["vector"],
                    payload={k: v for k, v in doc.items() if k != "vector"}
                )
                points.append(point)

            self.logger.info(f"Attempting to add {len(documents)} documents to collection '{collection}'")
            self.client.add_documents(collection, points, batch_size)
            self.logger.info(f"Added {len(documents)} documents to collection '{collection}'")
            return {'success': True, 'message': f"Successfully added {len(documents)} documents."}
        except InvalidInputError as e:
            self.logger.error(f"Invalid document structure error adding to '{collection}': {e}", exc_info=False)
            raise e
        except Exception as e:
            error_message = f"Failed to add documents to collection '{collection}': {str(e)}"
            self.logger.error(error_message, exc_info=True)
            raise DocumentError(collection, error_message) from e

    def delete_documents(self, collection: str, ids: List[str]) -> None:
            # Return error dictionary for other exceptions
            error_message = f"Failed to add documents: {str(e)}"
            self.logger.error(f"Error adding documents to '{collection}': {error_message}", exc_info=True)
            # raise DocumentError(collection, error_message)
            return {'success': False, 'error': error_message, 'details': str(e)}

    def delete_documents(self, collection: str, ids: List[str]) -> None:
        """
        Delete documents from collection.
        
        This method deletes documents with the specified IDs from the collection.
        
        Args:
            collection (str): The name of the collection to delete documents from.
            ids (List[str]): A list of document IDs to delete.
            
        Raises:
            DocumentError: If the document deletion fails.
            
        Examples:
            >>> command = QdrantCommand()
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> command.initialize(client)
            >>> command.delete_documents("my_collection", ["doc1", "doc2"])
        """
        try:
            self.client.delete_documents(collection, ids)
            self.logger.info(f"Deleted {len(ids)} documents from collection '{collection}'")
        except Exception as e:
            raise DocumentError(collection, f"Failed to delete documents: {str(e)}")

    def search_documents(self, collection: str, query: Dict[str, Any],
                        limit: int = 10, with_vectors: bool = False) -> List[Dict[str, Any]]:
        """
        Search documents in collection.
        
        This method performs a vector similarity search in the specified collection
        using the provided query vector and optional filter.
        
        Args:
            collection (str): The name of the collection to search in.
            query (Dict[str, Any]): The search query. Must contain a 'vector' field
                and optionally a 'filter' field.
            limit (int): The maximum number of results to return. Defaults to 10.
            with_vectors (bool): Whether to include vectors in the results.
                Defaults to False.
                
        Returns:
            List[Dict[str, Any]]: A list of matching documents, each containing 'id',
                'score', and payload fields. If with_vectors is True, also includes
                'vector' field.
                
        Raises:
            QueryError: If the search operation fails.
            
        Examples:
            >>> command = QdrantCommand()
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> command.initialize(client)
            >>> query = {
            ...     "vector": [0.1, 0.2, 0.3],
            ...     "filter": {
            ...         "must": [
            ...             {"key": "category", "match": {"value": "electronics"}}
            ...         ]
            ...     }
            ... }
            >>> results = command.search_documents("my_collection", query, limit=5)
        """
        try:
            results = self.client.search_documents(collection, query, limit)
            if not with_vectors:
                for doc in results:
                    doc.pop("vector", None)
            return results
        except Exception as e:
            raise QueryError(query, f"Failed to search documents in collection '{collection}': {str(e)}")

    def get_documents(self, collection: str, ids: List[Union[str, int]],
                     with_vectors: bool = False) -> Dict[str, Any]:
        """
        Get documents by IDs, returning a dict response.
        
        This method retrieves documents with the specified IDs from the collection.
        
        Args:
            collection (str): The name of the collection to retrieve documents from.
            ids (List[Union[str, int]]): A list of document IDs to retrieve.
                IDs can be either strings or integers.
            with_vectors (bool): Whether to include vectors in the results.
                Defaults to False.
                
        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
                If successful, contains 'success': True and 'data' with the list of documents.
                If failed, contains 'success': False and 'error'.
                
        Examples:
            >>> command = QdrantCommand()
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> command.initialize(client)
            >>> result = command.get_documents("my_collection", ["doc1", "doc2"])
            >>> if result['success']:
            ...     documents = result['data']
            ...     print(documents)
        """
        try:
            # Pass the potentially mixed list of int/str IDs
            documents = self.client.get_documents(collection, ids) 
            if not with_vectors:
                for doc in documents:
                    # Use pop with default None in case vector is missing
                    doc.pop("vector", None) 
            return {'success': True, 'data': documents}
        except Exception as e:
            error_message = f"Failed to get documents: {str(e)}"
            self.logger.error(f"Error getting documents from '{collection}': {error_message}", exc_info=True)
            # raise DocumentError(collection, error_message)
            return {'success': False, 'error': error_message, 'details': str(e)}

    def scroll_documents(
        self,
        collection: str,
        batch_size: int = 50,
        with_vectors: bool = False,
        with_payload: bool = False,
        offset: Optional[str] = None,
        filter: Optional[dict] = None
    ) -> Response:
        """Scroll through documents in a collection.

        Args:
            collection: Collection name
            batch_size: Number of documents per batch
            with_vectors: Whether to include vectors in results
            with_payload: Whether to include payload in results
            offset: Offset token for pagination
            filter: Filter query

        Returns:
            Response object containing documents and next offset token

        Raises:
            DocumentStoreError: If document retrieval fails
        """
        try:
            scroll_response = self.client.scroll(
                collection_name=collection,
                limit=batch_size,
                with_vectors=with_vectors,
                with_payload=with_payload,
                offset=offset,
                filter=filter
            )

            return Response(
                success=True,
                message=f"Retrieved {len(scroll_response.points)} documents",
                data={
                    "points": scroll_response.points,
                    "next_offset": scroll_response.next_page_offset
                }
            )

        except Exception as e:
            raise DocumentStoreError(
                f"Failed to scroll documents in collection '{collection}': {str(e)}",
                details={'collection': collection, 'original_error': str(e)}
            )

    def count_documents(
        self,
        collection: str,
        query: Optional[dict] = None
    ) -> Response:
        """Count documents in a collection.

        Args:
            collection: Collection name
            query: Filter query

        Returns:
            Response object containing document count

        Raises:
            DocumentStoreError: If document count fails
        """
        try:
            count_response = self.client.count(
                collection_name=collection,
                count_filter=query
            )

            return Response(
                success=True,
                message=f"Found {count_response.count} documents",
                data=count_response.count
            )

        except Exception as e:
            raise DocumentStoreError(
                f"Failed to count documents in collection '{collection}': {str(e)}",
                details={'collection': collection, 'original_error': str(e)}
            )

    def _write_output(self, data: Any, output: Optional[Union[str, TextIO]] = None,
                     format: str = "json") -> None:
        """
        Write command output.
        
        This method writes the command output to the specified output destination
        in the specified format.
        
        Args:
            data (Any): The data to write.
            output (Optional[Union[str, TextIO]]): The output destination. Can be a
                file path or a file-like object. If None, writes to stdout.
            format (str): The output format. Defaults to "json".
                
        Raises:
            Exception: If the output writing fails.
            
        Examples:
            >>> command = QdrantCommand()
            >>> data = {"name": "my_collection", "points_count": 1000}
            >>> command._write_output(data, "output.json")
        """
        try:
            super()._write_output(data, output, format)
        except Exception as e:
            self.logger.error(f"Failed to write output: {str(e)}")
            raise
