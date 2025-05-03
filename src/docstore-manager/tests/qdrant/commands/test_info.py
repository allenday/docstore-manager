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

# Mock Qdrant models if needed for info object structure
from qdrant_client.http import models as rest 

@pytest.fixture
def mock_client():
    """Fixture for mocked QdrantClient."""
    return Mock(spec=QdrantClient)

@pytest.fixture
def mock_args():
    """Fixture for basic command line arguments."""
    return Namespace(
        collection="test_collection",
        output_format="json"
    )

@pytest.fixture
def mock_collection_info_obj():
    """Fixture for a mock CollectionInfo object (using Namespace)."""
    # Simulate the structure returned by client.get_collection
    return Namespace(
        status=rest.CollectionStatus.GREEN, # Use actual enum if possible
        optimizer_status=rest.OptimizersStatusOneOf.OK,
        vectors_count=100, # Example field name
        indexed_vectors_count=90,
        points_count=100, # Use this field
        segments_count=1, 
        config=Namespace(
            params=Namespace(
                vectors=rest.VectorParams(size=128, distance=rest.Distance.COSINE),
                shard_number=1,
                replication_factor=1,
                write_consistency_factor=1,
                on_disk_payload=True
            ),
            hnsw_config=rest.HnswConfigDiff(m=16, ef_construct=100),
            optimizer_config=rest.OptimizersConfigDiff(deleted_threshold=0.2),
            wal_config=rest.WalConfigDiff(wal_capacity_mb=32)
        ),
        payload_schema={ # Example payload schema - Use dict, not model
            "field1": {"data_type": "keyword"} # Simplified
        }
        # Add .dict() and .model_dump() mocks if format_collection_info relies heavily on them
        # dict=MagicMock(return_value={... serializable dict ...}), 
        # model_dump=MagicMock(return_value={... serializable dict ...})
    )

def test_collection_info_success(mock_client, mock_args, mock_collection_info_obj, caplog):
    """Test successful retrieval and formatting of collection info."""
    caplog.set_level(logging.INFO)
    mock_client.get_collection.return_value = mock_collection_info_obj

    collection_info(client=mock_client, collection_name=mock_args.collection)

    mock_client.get_collection.assert_called_once_with(collection_name=mock_args.collection)
    # Check the log for the final formatted output (JSON by default)
    assert "Getting information for collection" in caplog.text
    # Check for key fields in the logged JSON string
    assert '"points_count": 100' in caplog.text
    # The formatter simplifies status/optimizer_status, check the simplified value
    assert '"status": "green"' in caplog.text # Assuming GREEN maps to 'green'
    assert '"hnsw_config":' in caplog.text

def test_collection_info_minimal(mock_client, mock_args, caplog):
    """Test info retrieval with minimal data returned."""
    caplog.set_level(logging.INFO)
    # Simulate a minimal object return
    minimal_info_obj = Namespace(
        status=rest.CollectionStatus.YELLOW,
        points_count=0,
        config=Namespace(
             params=Namespace(
                 vectors=rest.VectorParams(size=4, distance=rest.Distance.DOT)
             )
        ),
        optimizer_status=None # Explicitly None
    )
    mock_client.get_collection.return_value = minimal_info_obj

    collection_info(client=mock_client, collection_name=mock_args.collection)

    mock_client.get_collection.assert_called_once_with(collection_name=mock_args.collection)
    # Check logs for JSON output
    assert '"points_count": 0' in caplog.text
    assert '"status": "yellow"' in caplog.text # Assuming YELLOW maps to 'yellow'
    assert 'optimizer_status' not in caplog.text # Should be omitted or null
    assert '"distance": "Dot"' in caplog.text # Check nested value (title case as per actual enum value)

def test_collection_info_no_data(mock_client, mock_args, caplog):
    """Test info retrieval when command returns None (should probably error)."""
    caplog.set_level(logging.ERROR) # Expecting an error now
    mock_client.get_collection.return_value = None # Simulate client returning None

    # The command should raise an error if None is returned unexpectedly
    with pytest.raises(CollectionError, match="Unexpected error getting collection info"):
        collection_info(client=mock_client, collection_name=mock_args.collection)
    
    # Update log assertion to match the explicit None check message
    expected_log = f"Client returned None when fetching info for collection '{mock_args.collection}'."
    assert expected_log in caplog.text

def test_collection_info_missing_name(mock_client, mock_args):
    """Test calling info command without collection name."""
    mock_args.collection = None
    # This check might happen in the CLI layer, but the command itself might also check
    # Assuming the command function itself doesn't explicitly check for None/empty name
    # and relies on the client call failing if name is invalid.
    # If the function *does* check, adjust the test.
    # Let's assume client raises an error for None/empty name:
    mock_client.get_collection.side_effect = ValueError("Collection name cannot be empty")
    with pytest.raises(CollectionError, match="Unexpected error getting collection info"):
        collection_info(client=mock_client, collection_name=mock_args.collection)
    # If the function has its own check:
    # with pytest.raises(InvalidInputError, match="Collection name is required"):
    #     collection_info(client=mock_client, collection_name=mock_args.collection)

def test_collection_info_not_found(mock_client, mock_args, caplog):
    """Test info retrieval for a non-existent collection."""
    caplog.set_level(logging.ERROR)
    # Simulate client raising UnexpectedResponse for 404
    mock_client.get_collection.side_effect = UnexpectedResponse(
        status_code=404, reason_phrase="Not Found", content=b"Collection not found", headers={}
    )

    # Expect CollectionDoesNotExistError from our refined exception handling
    with pytest.raises(CollectionDoesNotExistError) as exc_info:
        collection_info(client=mock_client, collection_name=mock_args.collection)

    assert f"Collection '{mock_args.collection}' not found" in str(exc_info.value)
    assert f"Collection '{mock_args.collection}' not found" in caplog.text
    mock_client.get_collection.assert_called_once_with(collection_name=mock_args.collection)

def test_collection_info_failure(mock_client, mock_args, caplog):
    """Test handling failure from the underlying client (e.g., 500 error)."""
    caplog.set_level(logging.ERROR)
    error_msg = "Internal Qdrant Error"
    # Simulate client raising UnexpectedResponse for 500
    mock_client.get_collection.side_effect = UnexpectedResponse(
        status_code=500, reason_phrase="Server Error", content=error_msg.encode(), headers={}
    )
    
    # Expect CollectionError from our refined handling
    with pytest.raises(CollectionError) as exc_info:
        collection_info(client=mock_client, collection_name=mock_args.collection)

    assert "API error during info retrieval" in str(exc_info.value)
    # Update assertion to include status code and reason phrase
    expected_log = f"API error getting collection info for '{mock_args.collection}': Status 500 - Server Error - {error_msg}"
    assert expected_log in caplog.text
    assert error_msg in exc_info.value.details # Check details field
    mock_client.get_collection.assert_called_once_with(collection_name=mock_args.collection)

def test_collection_info_unexpected_error(mock_client, mock_args, caplog):
    """Test handling unexpected exceptions during info retrieval."""
    caplog.set_level(logging.ERROR)
    error_msg = "Unexpected timeout"
    # Simulate an unexpected non-API error
    mock_client.get_collection.side_effect = TimeoutError(error_msg)

    # Expect CollectionError from the final catch block
    with pytest.raises(CollectionError) as exc_info:
        collection_info(client=mock_client, collection_name=mock_args.collection)

    assert f"Unexpected error getting collection info: {error_msg}" in str(exc_info.value)
    assert mock_args.collection == exc_info.value.collection
    # Check details passed in the final exception handler
    assert exc_info.value.details['error_type'] == 'TimeoutError' 
    assert exc_info.value.details['message'] == error_msg
    assert f"Unexpected error getting collection info for '{mock_args.collection}': {error_msg}" in caplog.text
