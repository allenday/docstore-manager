"""Tests for delete collection command."""

import pytest
from unittest.mock import Mock, patch

from docstore_manager.common.exceptions import (
    CollectionError,
    CollectionNotFoundError
)
from docstore_manager.qdrant.commands.delete import delete_collection

@pytest.fixture
def mock_client():
    """Create a mock QdrantClient."""
    return Mock()

@pytest.fixture
def mock_command():
    """Create a mock QdrantCommand."""
    with patch("docstore_manager.qdrant.commands.delete.QdrantCommand") as mock:
        yield mock.return_value

@pytest.fixture
def mock_args():
    """Create mock command line arguments."""
    args = Mock()
    args.collection = "test_collection"
    return args

def test_delete_collection_success(mock_client, mock_command, mock_args):
    """Test successful collection deletion."""
    # Setup mock response
    mock_command.delete_collection.return_value.success = True
    mock_command.delete_collection.return_value.message = "Collection deleted"
    mock_command.delete_collection.return_value.error = None

    # Call the function
    delete_collection(mock_client, mock_args)

    # Verify
    mock_command.delete_collection.assert_called_once_with(name="test_collection")

def test_delete_collection_missing_name(mock_client, mock_command, mock_args):
    """Test collection deletion with missing name."""
    mock_args.collection = None

    with pytest.raises(CollectionError) as exc_info:
        delete_collection(mock_client, mock_args)
    
    assert "Collection name is required" in str(exc_info.value)
    mock_command.delete_collection.assert_not_called()

def test_delete_collection_not_found(mock_client, mock_command, mock_args):
    """Test handling when collection does not exist."""
    # Setup mock response
    mock_command.delete_collection.return_value.success = False
    mock_command.delete_collection.return_value.error = "Collection not found"

    with pytest.raises(CollectionNotFoundError) as exc_info:
        delete_collection(mock_client, mock_args)
    
    assert "Collection 'test_collection' does not exist" in str(exc_info.value)
    assert exc_info.value.collection == "test_collection"
    mock_command.delete_collection.assert_called_once()

def test_delete_collection_failure(mock_client, mock_command, mock_args):
    """Test handling of failed collection deletion."""
    # Setup mock response
    mock_command.delete_collection.return_value.success = False
    mock_command.delete_collection.return_value.error = "Test error"

    with pytest.raises(CollectionError) as exc_info:
        delete_collection(mock_client, mock_args)
    
    assert "Failed to delete collection" in str(exc_info.value)
    assert exc_info.value.collection == "test_collection"
    mock_command.delete_collection.assert_called_once()

def test_delete_collection_unexpected_error(mock_client, mock_command, mock_args):
    """Test handling of unexpected errors."""
    # Setup mock to raise an unexpected error
    mock_command.delete_collection.side_effect = ValueError("Unexpected error")

    with pytest.raises(CollectionError) as exc_info:
        delete_collection(mock_client, mock_args)
    
    assert "Unexpected error deleting collection" in str(exc_info.value)
    assert exc_info.value.collection == "test_collection"
    mock_command.delete_collection.assert_called_once() 