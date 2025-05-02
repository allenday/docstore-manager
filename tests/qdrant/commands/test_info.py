"""Tests for collection info command."""

import pytest
from unittest.mock import Mock, patch
from argparse import Namespace
import json
import logging

from docstore_manager.core.exceptions import (
    CollectionError,
    CollectionDoesNotExistError
)
from docstore_manager.qdrant.commands.info import collection_info
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client import QdrantClient
from qdrant_client.models import CollectionInfo

@pytest.fixture
def mock_client():
    """Create a mock QdrantClient."""
    return Mock(spec=QdrantClient)

@pytest.fixture
def mock_args():
    """Provides a mock Namespace object for args."""
    return Namespace(collection='test_collection', output=None, format='json')

@pytest.fixture
def mock_collection_info_data():
    """Provides mock collection info data."""
    # Create a mock that behaves like the CollectionInfo object if needed
    # For simple dict return, just return a dict:
    return {
        "status": "green",
        "vectors_count": 100,
        "segments_count": 1,
        "disk_data_size": 1024,
        "ram_data_size": 512,
        "config": {
            "params": {"vectors": {"size": 128, "distance": "Cosine"}},
            "hnsw_config": {"m": 16, "ef_construct": 100}
        }
    }

def test_collection_info_success(mock_client, mock_args, mock_collection_info_data, capsys):
    """Test successful retrieval and display of collection info."""
    # Mock the client method called by collection_info
    mock_client.get_collection.return_value = mock_collection_info_data

    # Call the function with the mock client and args
    collection_info(client=mock_client, collection_name=mock_args.collection, output_path=mock_args.output, output_format=mock_args.format)

    # Verify the correct client method was called
    mock_client.get_collection.assert_called_once_with(collection_name=mock_args.collection)
    
    # Check stdout for formatted JSON
    captured = capsys.readouterr()
    assert json.loads(captured.out) == mock_collection_info_data

def test_collection_info_minimal(mock_client, mock_args, capsys):
    """Test with minimal info returned (like only status)."""
    minimal_data = {"status": "yellow"}
    mock_client.get_collection.return_value = minimal_data
    collection_info(client=mock_client, collection_name=mock_args.collection, output_path=None, output_format='json')
    mock_client.get_collection.assert_called_once_with(collection_name=mock_args.collection)
    captured = capsys.readouterr()
    assert json.loads(captured.out) == minimal_data

def test_collection_info_no_data(mock_client, mock_args, caplog):
    """Test handling when get_collection returns None or empty."""
    mock_client.get_collection.return_value = None # Simulate no data
    
    with caplog.at_level(logging.WARNING):
        collection_info(client=mock_client, collection_name=mock_args.collection, output_path=None, output_format='json')
    
    mock_client.get_collection.assert_called_once_with(collection_name=mock_args.collection)
    assert "No detailed information returned" in caplog.text

def test_collection_info_missing_name(mock_client, mock_args):
    """Test info command with missing collection name."""
    mock_args.collection = None
    with pytest.raises(CollectionError) as exc_info:
        collection_info(client=mock_client, collection_name=mock_args.collection, output_path=None, output_format='json')
    assert "Collection name is required" in str(exc_info.value)

def test_collection_info_not_found(mock_client, mock_args):
    """Test handling when collection does not exist."""
    # Simulate client raising an appropriate error for not found
    mock_client.get_collection.side_effect = ValueError(f"Collection '{mock_args.collection}' not found")
    
    # Assuming collection_info wraps this in CollectionDoesNotExistError
    with pytest.raises(CollectionDoesNotExistError) as exc_info:
        collection_info(client=mock_client, collection_name=mock_args.collection, output_path=None, output_format='json')
        
    assert f"Collection '{mock_args.collection}' not found" in str(exc_info.value)
    mock_client.get_collection.assert_called_once_with(collection_name=mock_args.collection)

def test_collection_info_failure(mock_client, mock_args):
    """Test handling of client failure during info retrieval."""
    mock_client.get_collection.side_effect = Exception("API error")

    with pytest.raises(CollectionError) as exc_info:
        collection_info(client=mock_client, collection_name=mock_args.collection, output_path=None, output_format='json')
        
    assert "Failed to retrieve info" in str(exc_info.value)
    assert "API error" in str(exc_info.value)

def test_collection_info_unexpected_error(mock_client, mock_args):
    """Test handling of unexpected errors."""
    # Setup mock to raise an unexpected error
    mock_client.get_collection.side_effect = ValueError("Unexpected error")

    with pytest.raises(CollectionError) as exc_info:
        collection_info(client=mock_client, collection_name=mock_args.collection, output_path=None, output_format='json')
    
    assert "Unexpected error getting collection info" in str(exc_info.value)
    assert exc_info.value.collection == mock_args.collection
    assert exc_info.value.details == {'error_type': 'ValueError'}
    mock_client.get_collection.assert_called_once() 