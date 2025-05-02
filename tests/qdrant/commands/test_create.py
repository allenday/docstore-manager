"""Tests for create collection command."""

import pytest
from unittest.mock import Mock, patch
from argparse import Namespace

from docstore_manager.core.exceptions import (
    CollectionError,
    CollectionAlreadyExistsError
)
from docstore_manager.qdrant.commands.create import create_collection

@pytest.fixture
def mock_client():
    """Create a mock QdrantClient."""
    return Mock()

@pytest.fixture
def mock_command():
    """Create a mock QdrantCommand."""
    with patch("docstore_manager.qdrant.commands.create.QdrantCommand") as mock:
        yield mock.return_value

@pytest.fixture
def mock_args():
    """Provides a mock Namespace object for args."""
    return Namespace(
        collection='test_collection',
        dimension=128, 
        distance='cosine', 
        on_disk=False, 
        hnsw_ef=None, 
        hnsw_m=None,
        overwrite=False
    )

def test_create_collection_success(mock_client, mock_command, mock_args):
    """Test successful collection creation."""
    # Setup mock response
    mock_response = {
        'success': True, 'message': 'Collection created', 'data': {'status': 'green'}, 'error': None
    }
    mock_command.create_collection.return_value = mock_response

    # Call the function
    create_collection(mock_command, mock_args)

    # Verify
    mock_command.create_collection.assert_called_once_with(
        name="test_collection",
        dimension=128,
        distance="cosine",
        on_disk=False,
        hnsw_ef=None,
        hnsw_m=None,
        overwrite=False
    )

def test_create_collection_missing_name(mock_client, mock_command, mock_args):
    """Test collection creation with missing name."""
    mock_args.collection = None

    with pytest.raises(CollectionError) as exc_info:
        create_collection(mock_command, mock_args)
    
    assert "Collection name is required" in str(exc_info.value)
    mock_command.create_collection.assert_not_called()

def test_create_collection_already_exists(mock_client, mock_command, mock_args):
    """Test handling when collection already exists."""
    # Setup mock response
    mock_response = {'success': False, 'error': 'Collection already exists'}
    mock_command.create_collection.return_value = mock_response

    with pytest.raises(CollectionAlreadyExistsError) as exc_info:
        create_collection(mock_command, mock_args)
    
    # Check the specific error message by converting the exception to string
    assert str(exc_info.value) == 'Collection already exists'
    mock_command.create_collection.assert_called_once()

def test_create_collection_failure(mock_client, mock_command, mock_args):
    """Test handling of failed collection creation."""
    # Mock the command's method to simulate failure
    mock_command.create_collection.return_value = {
        'success': False, 'error': "Test error"
    }
    # Client mock setup is handled by the fixture

    with pytest.raises(CollectionError) as exc_info:
        # Pass the QdrantCommand mock to the handler function
        create_collection(mock_command, mock_args)
        # Check the specific error message by converting the exception to string
        assert str(exc_info.value) == 'Test error'

def test_create_collection_unexpected_error(mock_client, mock_command, mock_args):
    """Test handling of unexpected errors."""
    # Setup command mock to raise an unexpected error
    mock_command.create_collection.side_effect = ValueError("Unexpected error")
    # Client mock setup is handled by the fixture

    with pytest.raises(CollectionError) as exc_info:
        # Pass the QdrantCommand mock to the handler function
        create_collection(mock_command, mock_args)
        
    # Check the specific error message by converting the exception to string
    assert str(exc_info.value) == 'Unexpected error: Unexpected error'
    # Check collection name from args
    assert exc_info.value.collection == "test_collection"
    # Assert the full details dictionary including error_type
    assert exc_info.value.details == {
        'params': {
            'dimension': 128,
            'distance': 'cosine',
            'on_disk': False,
            'hnsw_ef': None,
            'hnsw_m': None,
            'overwrite': False # Make sure overwrite is included if added to details
        },
        'error_type': 'ValueError' # Add the expected error type
    } 