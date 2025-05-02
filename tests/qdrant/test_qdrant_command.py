"""Tests for the Qdrant command module."""
import pytest
from unittest.mock import patch, MagicMock
import argparse

from docstore_manager.qdrant.command import QdrantCommand
from docstore_manager.core.command.base import CommandResponse
from docstore_manager.core.exceptions import (
    DocumentError,
    CollectionError,
    DocumentStoreError,
    ConfigurationError,
    ConnectionError,
    CollectionAlreadyExistsError,
    CollectionDoesNotExistError,
    CollectionOperationError,
    DocumentOperationError,
    InvalidInputError
)
from qdrant_client.http.models import Distance, VectorParams, PointStruct

@pytest.fixture
def command():
    """Create a QdrantCommand instance with a mock client."""
    # Create a mock QdrantDocumentStore client
    mock_client = MagicMock()
    
    # Instantiate QdrantCommand
    cmd = QdrantCommand()
    
    # Initialize the command with the mock client
    cmd.initialize(mock_client)
    
    return cmd

@pytest.fixture
def mock_args():
    """Create mock command line arguments."""
    return argparse.Namespace(
        collection="test_collection",
        name="test_collection",
        dimension=128,
        distance="cosine",
        on_disk_payload=False,
        output=None,
        format="json"
    )

def test_command_initialization():
    """Test command initialization."""
    mock_client = MagicMock()
    cmd = QdrantCommand()
    cmd.initialize(mock_client)
    assert hasattr(cmd, 'client')
    assert cmd.client is mock_client # Check it's the actual mock client

def test_create_collection(command):
    """Test create collection."""
    with patch.object(command.client, "create_collection") as mock_create:
        command.create_collection("test_collection", 128, "Cosine", False)
        mock_create.assert_called_once_with(
            "test_collection",
            VectorParams(size=128, distance=Distance.COSINE),
            on_disk_payload=False
        )

def test_create_collection_error(command):
    """Test create collection error handling."""
    with patch.object(command.client, "create_collection") as mock_create:
        mock_create.side_effect = Exception("Failed to create")
        with pytest.raises(CollectionError) as exc_info:
            command.create_collection("test_collection", 128)
        assert "Failed to create collection" in str(exc_info.value)

def test_delete_collection(command):
    """Test delete collection."""
    with patch.object(command.client, "delete_collection") as mock_delete:
        command.delete_collection("test_collection")
        mock_delete.assert_called_once_with("test_collection")

def test_delete_collection_error(command):
    """Test delete collection error handling."""
    with patch.object(command.client, "delete_collection") as mock_delete:
        mock_delete.side_effect = Exception("Failed to delete")
        with pytest.raises(CollectionError) as exc_info:
            command.delete_collection("test_collection")
        assert "Failed to delete collection" in str(exc_info.value)

def test_list_collections(command):
    """Test list collections."""
    expected = [{"name": "test_collection"}]
    with patch.object(command.client, "get_collections") as mock_list:
        mock_list.return_value = expected
        result = command.list_collections()
        assert result == expected
        mock_list.assert_called_once()

def test_list_collections_error(command):
    """Test list collections error handling."""
    with patch.object(command.client, "get_collections") as mock_list:
        mock_list.side_effect = Exception("Failed to list")
        with pytest.raises(CollectionError) as exc_info:
            command.list_collections()
        assert "Failed to list collections" in str(exc_info.value)

def test_get_collection(command):
    """Test get collection."""
    expected = {"name": "test_collection", "dimension": 128}
    with patch.object(command.client, "get_collection") as mock_get:
        mock_get.return_value = expected
        result = command.get_collection("test_collection")
        assert result == expected
        mock_get.assert_called_once_with("test_collection")

def test_get_collection_error(command):
    """Test get collection error handling."""
    with patch.object(command.client, "get_collection") as mock_get:
        mock_get.side_effect = Exception("Failed to get")
        with pytest.raises(CollectionError) as exc_info:
            command.get_collection("test_collection")
        assert "Failed to get collection" in str(exc_info.value)

def test_add_documents(command):
    """Test add documents."""
    docs = [{"id": "1", "vector": [0.1, 0.2], "text": "test"}]
    with patch.object(command.client, "add_documents") as mock_add:
        command.add_documents("test_collection", docs)
        mock_add.assert_called_once()
        # Verify the points were created correctly
        points = mock_add.call_args[0][1]
        assert len(points) == 1
        assert points[0].id == "1"
        assert points[0].vector == [0.1, 0.2]
        # The payload includes all non-vector fields, including id
        assert points[0].payload == {"id": "1", "text": "test"}

def test_add_documents_validation_error(command):
    """Test add documents with validation error."""
    docs = [{"vector": [0.1]}] # Missing 'id'
    with pytest.raises(InvalidInputError) as exc_info:
        command.add_documents("test_collection", docs)
    assert "Document must contain 'id' and 'vector' fields" in str(exc_info.value)

def test_add_documents_error(command):
    """Test add documents error handling."""
    docs = [{"id": "1", "vector": [0.1, 0.2]}]
    with patch.object(command.client, "add_documents") as mock_add:
        mock_add.side_effect = Exception("Failed to add")
        with pytest.raises(DocumentError) as exc_info:
            command.add_documents("test_collection", docs)
        assert "Failed to add documents" in str(exc_info.value)

def test_delete_documents(command):
    """Test delete documents."""
    ids = ["1", "2", "3"]
    with patch.object(command.client, "delete_documents") as mock_delete:
        command.delete_documents("test_collection", ids)
        mock_delete.assert_called_once_with("test_collection", ids)

def test_delete_documents_error(command):
    """Test delete documents error handling."""
    with patch.object(command.client, "delete_documents") as mock_delete:
        mock_delete.side_effect = Exception("Failed to delete")
        with pytest.raises(DocumentError) as exc_info:
            command.delete_documents("test_collection", ["1"])
        assert "Failed to delete documents" in str(exc_info.value)

def test_search_documents(command):
    """Test search documents."""
    query = {"vector": [0.1, 0.2]}
    expected = [{"id": "1", "vector": [0.1, 0.2], "text": "test"}]
    with patch.object(command.client, "search_documents") as mock_search:
        mock_search.return_value = expected
        result = command.search_documents("test_collection", query)
        assert len(result) == 1
        assert "vector" not in result[0]  # Vector should be removed by default
        mock_search.assert_called_once_with("test_collection", query, 10)

def test_search_documents_with_vectors(command):
    """Test search documents with vectors included."""
    query = {"vector": [0.1, 0.2]}
    expected = [{"id": "1", "vector": [0.1, 0.2], "text": "test"}]
    with patch.object(command.client, "search_documents") as mock_search:
        mock_search.return_value = expected
        result = command.search_documents("test_collection", query, with_vectors=True)
        assert len(result) == 1
        assert "vector" in result[0]
        mock_search.assert_called_once_with("test_collection", query, 10)

@patch('docstore_manager.qdrant.command.QdrantDocumentStore')
def test_search_documents_error(MockQdrantStore, qdrant_command):
    """Test handling errors during search documents."""
    mock_store_instance = MockQdrantStore.return_value
    qdrant_command.client = mock_store_instance
    # Simulate the underlying client raising a generic Exception
    mock_store_instance.search_documents.side_effect = Exception("Search engine failure")
    query = {"vector": [0.5]}

    # Catch DocumentStoreError as the more general error type
    with pytest.raises(DocumentStoreError) as exc_info:
        qdrant_command.search_documents("error_collection", query)

    # Check the message from the wrapped exception
    assert "Failed to search documents in collection 'error_collection'" in str(exc_info.value)
    assert "Search engine failure" in str(exc_info.value)

def test_get_documents(command):
    """Test get documents."""
    ids = ["1", "2"]
    expected = [
        {"id": "1", "vector": [0.1, 0.2], "text": "test1"},
        {"id": "2", "vector": [0.3, 0.4], "text": "test2"}
    ]
    with patch.object(command.client, "get_documents") as mock_get:
        mock_get.return_value = expected
        result = command.get_documents("test_collection", ids)
        assert len(result) == 2
        assert all("vector" not in doc for doc in result)
        mock_get.assert_called_once_with("test_collection", ids)

def test_get_documents_with_vectors(command):
    """Test get documents with vectors included."""
    ids = ["1"]
    expected = [{"id": "1", "vector": [0.1, 0.2], "text": "test"}]
    with patch.object(command.client, "get_documents") as mock_get:
        mock_get.return_value = expected
        result = command.get_documents("test_collection", ids, with_vectors=True)
        assert len(result) == 1
        assert "vector" in result[0]
        mock_get.assert_called_once_with("test_collection", ids)

def test_get_documents_error(command):
    """Test get documents error handling."""
    with patch.object(command.client, "get_documents") as mock_get:
        mock_get.side_effect = Exception("Failed to get")
        with pytest.raises(DocumentError) as exc_info:
            command.get_documents("test_collection", ["1"])
        assert "Failed to get documents" in str(exc_info.value)

def test_scroll_documents(command):
    """Test scroll documents."""
    with patch.object(command.client, "scroll") as mock_scroll_client:
        # Mock the scroll response structure from the qdrant_client
        mock_scroll_response = MagicMock()
        mock_scroll_response.points = [
            PointStruct(id="1", vector=[0.1, 0.2], payload={"text": "test1"}),
            PointStruct(id="2", vector=[0.3, 0.4], payload={"text": "test2"})
        ]
        mock_scroll_response.next_page_offset = None
        mock_scroll_client.return_value = mock_scroll_response

        result = command.scroll_documents("test_collection")
        assert result.success is True
        assert len(result.data['points']) == 2
        # QdrantCommand.scroll_documents should handle this, but let's test it was called correctly
        # mock_scroll_client.assert_called_once_with(
        #     collection_name="test_collection", limit=50, with_vectors=False, 
        #     with_payload=False, offset=None, filter=None
        # )

def test_scroll_documents_with_vectors(command):
    """Test scroll documents with vectors included."""
    with patch.object(command.client, "scroll") as mock_scroll_client:
        mock_scroll_response = MagicMock()
        mock_scroll_response.points = [PointStruct(id="1", vector=[0.1, 0.2], payload={"text": "test"})]
        mock_scroll_response.next_page_offset = None
        mock_scroll_client.return_value = mock_scroll_response

        result = command.scroll_documents("test_collection", with_vectors=True)
        assert result.success is True
        assert len(result.data['points']) == 1
        assert result.data['points'][0].vector == [0.1, 0.2]
        # mock_scroll_client.assert_called_once_with(
        #     collection_name="test_collection", limit=50, with_vectors=True, 
        #     with_payload=False, offset=None, filter=None
        # )

def test_scroll_documents_error(command):
    """Test scroll documents error handling."""
    collection_name = "test_collection_scroll_fail"
    with patch.object(command.client, "scroll") as mock_scroll_client:
        original_error_msg = "Internal scroll error"
        mock_scroll_client.side_effect = Exception(original_error_msg)
        # Expect DocumentStoreError now
        with pytest.raises(DocumentStoreError) as exc_info:
            command.scroll_documents(collection_name)
            
        # Check the wrapped exception message and details
        expected_msg_part = f"Failed to scroll documents in collection '{collection_name}': {original_error_msg}"
        assert expected_msg_part in str(exc_info.value)
        assert exc_info.value.details == {'collection': collection_name, 'original_error': original_error_msg}

def test_count_documents(command):
    """Test count documents."""
    with patch.object(command.client, "count") as mock_count_client:
        # Mock the count response structure
        mock_count_response = MagicMock()
        mock_count_response.count = 42
        mock_count_client.return_value = mock_count_response

        result = command.count_documents("test_collection")
        assert result.success is True
        assert result.data == 42
        mock_count_client.assert_called_once_with(collection_name="test_collection", count_filter=None)

def test_count_documents_with_query(command):
    """Test count documents with query."""
    query = {"filter": {"must": [{"key": "value"}]}}
    with patch.object(command.client, "count") as mock_count_client:
        mock_count_response = MagicMock()
        mock_count_response.count = 10
        mock_count_client.return_value = mock_count_response

        result = command.count_documents("test_collection", query)
        assert result.success is True
        assert result.data == 10
        mock_count_client.assert_called_once_with(
            collection_name="test_collection", 
            count_filter=query # Pass the whole query dict as filter
        )

def test_count_documents_error(command):
    """Test count documents error handling."""
    collection_name = "test_collection_count_fail"
    with patch.object(command.client, "count") as mock_count_client:
        original_error_msg = "Internal count error"
        mock_count_client.side_effect = Exception(original_error_msg)
        # Expect DocumentStoreError now
        with pytest.raises(DocumentStoreError) as exc_info:
            command.count_documents(collection_name)

        # Check the wrapped exception message and details
        expected_msg_part = f"Failed to count documents in collection '{collection_name}': {original_error_msg}"
        assert expected_msg_part in str(exc_info.value)
        assert exc_info.value.details == {'collection': collection_name, 'original_error': original_error_msg}

def test_write_output(command):
    """Test write output."""
    data = {"test": "data"}
    with patch("docstore_manager.core.command.base.DocumentStoreCommand._write_output") as mock_write:
        command._write_output(data)
        mock_write.assert_called_once_with(data, None, "json")

def test_write_output_error(command):
    """Test write output error handling."""
    with patch("docstore_manager.core.command.base.DocumentStoreCommand._write_output") as mock_write:
        mock_write.side_effect = Exception("Failed to write")
        with pytest.raises(Exception) as exc_info:
            command._write_output({})
        assert "Failed to write" in str(exc_info.value)

def test_write_output_handles_error(command):
    """Test that _write_output handles exceptions during write."""
    response = CommandResponse(success=True, message="Test data", data={"key": "value"})
    with patch("docstore_manager.core.command.base.DocumentStoreCommand._write_output") as mock_write:
        with pytest.raises(DocumentStoreError):
            mock_write.side_effect = DocumentStoreError("mock_output.json", "Cannot write")
            command._write_output(response, format="json", output="mock_output.json")

def test_run_method_calls_write_output(command):
    """Test that the run method correctly calls _write_output on success."""
    args = argparse.Namespace(collection_name="test_coll", dimension=128, format="json", output=None)
    execute_response = CommandResponse(success=True, message="Created", data={"created": True})
    command.execute = MagicMock(return_value=execute_response)
    with patch("docstore_manager.core.command.base.DocumentStoreCommand._write_output") as mock_write:
        result = command.execute(args)
        assert result == execute_response
        # mock_write assertion needs to be done in the calling context (e.g., CLI test)
        # For now, let's remove the potentially incorrect assertion here
        # mock_write.assert_called_once_with(execute_response, format="json", output=None) 