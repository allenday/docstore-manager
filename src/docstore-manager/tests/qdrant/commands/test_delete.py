"""Tests for delete collection command."""

import pytest
from unittest.mock import Mock, patch
from argparse import Namespace

# Import the actual client class for type hinting and mocking spec
from qdrant_client import QdrantClient

from docstore_manager.core.exceptions import (
    CollectionError,
    CollectionDoesNotExistError
)
# Import the function under test
from docstore_manager.qdrant.commands.delete import delete_collection

@pytest.fixture
def mock_client():
    """Create a mock QdrantClient."""
    return Mock(spec=QdrantClient)

@pytest.fixture
def mock_args():
    """Provides a mock Namespace object for args."""
    return Namespace(collection='test_collection') # Changed name to collection

def test_delete_collection_success(mock_client, mock_args):
    """Test successful collection deletion."""
    # Mock the client method called by delete_collection
    mock_client.delete_collection.return_value = True # Assume returns True on success

    # Call the function with the mock client and args
    delete_collection(client=mock_client, collection_name=mock_args.collection)

    # Verify the correct client method was called
    mock_client.delete_collection.assert_called_once_with(collection_name=mock_args.collection, timeout=None)

def test_delete_collection_missing_name(mock_client, mock_args):
    """Test collection deletion with missing name."""
    mock_args.collection = None
    with pytest.raises(CollectionError) as exc_info:
        # Pass None for collection_name
        delete_collection(client=mock_client, collection_name=mock_args.collection)
    assert "Collection name is required" in str(exc_info.value)
    mock_client.delete_collection.assert_not_called()

def test_delete_collection_not_found(mock_client, mock_args):
    """Test handling when collection does not exist."""
    # Simulate the client raising an error (e.g., ValueError for not found in qdrant_client)
    # Adjust based on the actual exception qdrant_client might raise or how your command handles it
    mock_client.delete_collection.side_effect = ValueError("Not found: collection test_collection")

    # Assuming the delete_collection function wraps this in CollectionDoesNotExistError
    with pytest.raises(CollectionDoesNotExistError) as exc_info:
        delete_collection(client=mock_client, collection_name=mock_args.collection)
    
    assert f"Collection '{mock_args.collection}' not found" in str(exc_info.value)
    mock_client.delete_collection.assert_called_once_with(collection_name=mock_args.collection, timeout=None)

def test_delete_collection_failure(mock_client, mock_args):
    """Test handling of failed collection deletion."""
    # Simulate a generic exception from the client
    mock_client.delete_collection.side_effect = Exception("API error")

    with pytest.raises(CollectionError) as exc_info:
        delete_collection(client=mock_client, collection_name=mock_args.collection)
        
    assert "Failed to delete collection" in str(exc_info.value)
    assert "API error" in str(exc_info.value)
    mock_client.delete_collection.assert_called_once_with(collection_name=mock_args.collection, timeout=None)
