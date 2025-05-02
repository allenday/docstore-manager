"""Tests for create collection command."""

import pytest
from unittest.mock import Mock, patch
from argparse import Namespace

# Import the actual client class for type hinting and mocking spec
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

from docstore_manager.core.exceptions import (
    CollectionError,
    CollectionAlreadyExistsError,
    ConfigurationError # Added for potential config errors
)
# Import the function under test
from docstore_manager.qdrant.commands.create import create_collection

@pytest.fixture
def mock_client():
    """Create a mock QdrantClient."""
    # Use spec=QdrantClient for better mocking
    return Mock(spec=QdrantClient)

@pytest.fixture
def mock_args():
    """Provides a mock Namespace object for args."""
    # These args are passed to the create_collection function
    return Namespace(
        collection_name='test_collection', # Use a distinct name from fixture
        dimension=128,
        distance='Cosine', # Ensure case matches Distance enum
        on_disk_payload=False,
        hnsw_ef=None,
        hnsw_m=None,
        shards=None, # Added based on function signature
        replication_factor=None, # Added based on function signature
        overwrite=False
    )

def test_create_collection_success(mock_client, mock_args):
    """Test successful collection creation."""
    # Mock the specific client method called by create_collection
    # Assuming it checks existence first, then creates
    mock_client.get_collections.return_value = Mock(collections=[]) # Simulate collection doesn't exist
    mock_client.create_collection.return_value = True # Simulate successful creation

    # Call the function with the mock client and args
    create_collection(
        client=mock_client,
        collection_name=mock_args.collection_name,
        dimension=mock_args.dimension,
        distance=mock_args.distance,
        on_disk_payload=mock_args.on_disk_payload,
        hnsw_ef=mock_args.hnsw_ef,
        hnsw_m=mock_args.hnsw_m,
        shards=mock_args.shards,
        replication_factor=mock_args.replication_factor,
        overwrite=mock_args.overwrite
    )

    # Verify the correct client method was called
    mock_client.create_collection.assert_called_once()
    call_args, call_kwargs = mock_client.create_collection.call_args
    assert call_kwargs['collection_name'] == 'test_collection'
    assert isinstance(call_kwargs['vectors_config'], VectorParams)
    assert call_kwargs['vectors_config'].size == 128
    assert call_kwargs['vectors_config'].distance == Distance.COSINE

def test_create_collection_success_overwrite(mock_client, mock_args):
    """Test successful collection creation with overwrite=True."""
    mock_args.overwrite = True
    mock_client.recreate_collection.return_value = True # Simulate successful recreation

    create_collection(
        client=mock_client,
        collection_name=mock_args.collection_name,
        dimension=mock_args.dimension,
        distance=mock_args.distance,
        on_disk_payload=mock_args.on_disk_payload,
        hnsw_ef=mock_args.hnsw_ef,
        hnsw_m=mock_args.hnsw_m,
        shards=mock_args.shards,
        replication_factor=mock_args.replication_factor,
        overwrite=mock_args.overwrite
    )
    # Verify recreate was called
    mock_client.recreate_collection.assert_called_once()
    mock_client.create_collection.assert_not_called()

def test_create_collection_missing_dimension(mock_client, mock_args):
    """Test collection creation with missing dimension."""
    mock_args.dimension = None
    # The function itself raises ConfigurationError if dimension is missing
    with pytest.raises(ConfigurationError) as exc_info:
        create_collection(
            client=mock_client,
            collection_name=mock_args.collection_name,
            dimension=mock_args.dimension,
            # ... other args ...
            distance=mock_args.distance,
            on_disk_payload=mock_args.on_disk_payload,
            overwrite=mock_args.overwrite
        )
    assert "Dimension (vectors.size) is required" in str(exc_info.value)

def test_create_collection_already_exists_no_overwrite(mock_client, mock_args):
    """Test handling when collection already exists and overwrite is False."""
    mock_args.overwrite = False
    # Simulate collection exists
    mock_client.get_collections.return_value = Mock(collections=[Mock(name='test_collection')])

    with pytest.raises(CollectionAlreadyExistsError) as exc_info:
        create_collection(
            client=mock_client,
            collection_name=mock_args.collection_name,
            dimension=mock_args.dimension,
            distance=mock_args.distance,
            on_disk_payload=mock_args.on_disk_payload,
            overwrite=mock_args.overwrite
            # ... other args ...
        )
    assert "already exists and overwrite=False" in str(exc_info.value)
    mock_client.create_collection.assert_not_called()
    mock_client.recreate_collection.assert_not_called()

def test_create_collection_failure_on_create(mock_client, mock_args):
    """Test handling of client failure during create_collection."""
    mock_args.overwrite = False
    mock_client.get_collections.return_value = Mock(collections=[]) # Doesn't exist
    mock_client.create_collection.side_effect = Exception("Qdrant API error")

    with pytest.raises(CollectionError) as exc_info:
        create_collection(
            client=mock_client,
            collection_name=mock_args.collection_name,
            dimension=mock_args.dimension,
            distance=mock_args.distance,
            # ... other args ...
            overwrite=mock_args.overwrite
        )
    assert "Failed to create/recreate collection" in str(exc_info.value)
    assert "Qdrant API error" in str(exc_info.value)

def test_create_collection_failure_on_recreate(mock_client, mock_args):
    """Test handling of client failure during recreate_collection."""
    mock_args.overwrite = True
    mock_client.recreate_collection.side_effect = Exception("Qdrant Recreate error")

    with pytest.raises(CollectionError) as exc_info:
        create_collection(
            client=mock_client,
            collection_name=mock_args.collection_name,
            dimension=mock_args.dimension,
            distance=mock_args.distance,
            # ... other args ...
            overwrite=mock_args.overwrite
        )
    assert "Failed to create/recreate collection" in str(exc_info.value)
    assert "Qdrant Recreate error" in str(exc_info.value)

# Remove old tests relying on mock_command
# def test_create_collection_missing_name(...):
# def test_create_collection_already_exists(...):
# def test_create_collection_failure(...):
# def test_create_collection_unexpected_error(...): 