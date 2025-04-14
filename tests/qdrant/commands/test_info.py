"""Tests for collection info command."""

import pytest
from unittest.mock import Mock, patch

from docstore_manager.common.exceptions import (
    CollectionError,
    CollectionNotFoundError
)
from docstore_manager.qdrant.commands.info import collection_info

@pytest.fixture
def mock_client():
    """Create a mock QdrantClient."""
    return Mock()

@pytest.fixture
def mock_command():
    """Create a mock QdrantCommand."""
    with patch("docstore_manager.qdrant.commands.info.QdrantCommand") as mock:
        yield mock.return_value

@pytest.fixture
def mock_args():
    """Create mock command line arguments."""
    args = Mock()
    args.collection = "test_collection"
    return args

@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    with patch("docstore_manager.qdrant.commands.info.logger") as mock:
        yield mock

def test_collection_info_success(mock_client, mock_command, mock_args, capsys):
    """Test successful collection info retrieval."""
    # Setup mock response
    mock_command.get_collection_info.return_value.success = True
    mock_command.get_collection_info.return_value.data = {
        'vector_size': 128,
        'distance': 'cosine',
        'status': 'green',
        'vectors_count': 1000,
        'segments_count': 5,
        'on_disk': True,
        'payload_schema': {
            'text': 'string',
            'score': 'float'
        }
    }
    mock_command.get_collection_info.return_value.error = None

    # Call the function
    collection_info(mock_client, mock_args)

    # Verify
    mock_command.get_collection_info.assert_called_once_with(name="test_collection")
    
    # Check output
    captured = capsys.readouterr()
    assert "Collection: test_collection" in captured.out
    assert "Vector size: 128" in captured.out
    assert "Distance: cosine" in captured.out
    assert "Status: green" in captured.out
    assert "Indexed vectors: 1000" in captured.out
    assert "Segments: 5" in captured.out
    assert "On disk: True" in captured.out
    assert "Payload Schema:" in captured.out
    assert "text: string" in captured.out
    assert "score: float" in captured.out

def test_collection_info_minimal(mock_client, mock_command, mock_args, capsys):
    """Test collection info with minimal data."""
    # Setup mock response
    mock_command.get_collection_info.return_value.success = True
    mock_command.get_collection_info.return_value.data = {
        'vector_size': 128,
        'distance': 'cosine'
    }
    mock_command.get_collection_info.return_value.error = None

    # Call the function
    collection_info(mock_client, mock_args)

    # Verify
    mock_command.get_collection_info.assert_called_once_with(name="test_collection")
    
    # Check output
    captured = capsys.readouterr()
    assert "Collection: test_collection" in captured.out
    assert "Vector size: 128" in captured.out
    assert "Distance: cosine" in captured.out
    assert "Status: N/A" in captured.out
    assert "Indexed vectors: 0" in captured.out
    assert "Segments: 0" in captured.out
    assert "On disk: False" in captured.out

def test_collection_info_no_data(mock_client, mock_command, mock_args, mock_logger):
    """Test collection info with no data."""
    # Setup mock response
    mock_command.get_collection_info.return_value.success = True
    mock_command.get_collection_info.return_value.data = None
    mock_command.get_collection_info.return_value.error = None

    # Call the function
    collection_info(mock_client, mock_args)

    # Verify
    mock_command.get_collection_info.assert_called_once_with(name="test_collection")
    mock_logger.info.assert_any_call("No collection information available.")

def test_collection_info_missing_name(mock_client, mock_command, mock_args):
    """Test collection info with missing name."""
    mock_args.collection = None

    with pytest.raises(CollectionError) as exc_info:
        collection_info(mock_client, mock_args)
    
    assert "Collection name is required" in str(exc_info.value)
    mock_command.get_collection_info.assert_not_called()

def test_collection_info_not_found(mock_client, mock_command, mock_args):
    """Test handling when collection does not exist."""
    # Setup mock response
    mock_command.get_collection_info.return_value.success = False
    mock_command.get_collection_info.return_value.error = "Collection not found"

    with pytest.raises(CollectionNotFoundError) as exc_info:
        collection_info(mock_client, mock_args)
    
    assert "Collection 'test_collection' does not exist" in str(exc_info.value)
    assert exc_info.value.collection == "test_collection"
    mock_command.get_collection_info.assert_called_once()

def test_collection_info_failure(mock_client, mock_command, mock_args):
    """Test handling of failed collection info retrieval."""
    # Setup mock response
    mock_command.get_collection_info.return_value.success = False
    mock_command.get_collection_info.return_value.error = "Test error"

    with pytest.raises(CollectionError) as exc_info:
        collection_info(mock_client, mock_args)
    
    assert "Failed to get collection info" in str(exc_info.value)
    assert exc_info.value.collection == "test_collection"
    assert exc_info.value.details == {'error': 'Test error'}
    mock_command.get_collection_info.assert_called_once()

def test_collection_info_unexpected_error(mock_client, mock_command, mock_args):
    """Test handling of unexpected errors."""
    # Setup mock to raise an unexpected error
    mock_command.get_collection_info.side_effect = ValueError("Unexpected error")

    with pytest.raises(CollectionError) as exc_info:
        collection_info(mock_client, mock_args)
    
    assert "Unexpected error getting collection info" in str(exc_info.value)
    assert exc_info.value.collection == "test_collection"
    assert exc_info.value.details == {'error_type': 'ValueError'}
    mock_command.get_collection_info.assert_called_once() 