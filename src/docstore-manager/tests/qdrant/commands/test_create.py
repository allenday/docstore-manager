"""Tests for create collection command."""

import pytest
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from qdrant_client.http.exceptions import UnexpectedResponse
from unittest.mock import Mock, patch
from argparse import Namespace
import logging
from pydantic import ValidationError

# Import the actual client class for type hinting and mocking spec
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, HnswConfigDiff

from docstore_manager.core.exceptions import (
    CollectionError,
    CollectionAlreadyExistsError,
    ConfigurationError, # Added for potential config errors
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

def test_create_collection_success(mock_client, caplog):
    """Test successful collection creation (overwrite=False)."""
    caplog.set_level(logging.INFO)
    collection_name = "test_collection"
    dimension = 128
    distance = Distance.COSINE
    # Simulate successful creation
    mock_client.create_collection.return_value = True

    create_collection(
        client=mock_client,
        collection_name=collection_name,
        dimension=dimension,
        distance=distance,
        overwrite=False, # Testing the create path
    )

    # Assert based on the actual parameters passed to create_collection
    expected_vectors_config = VectorParams(size=dimension, distance=distance, on_disk=False)
    mock_client.create_collection.assert_called_once_with(
        collection_name=collection_name,
        vectors_config=expected_vectors_config,
        shard_number=None,
        replication_factor=None,
        write_consistency_factor=None,
        hnsw_config=None,
        optimizers_config=None,
        wal_config=None,
        quantization_config=None,
        timeout=None
    )
    mock_client.recreate_collection.assert_not_called()
    assert f"Successfully created collection '{collection_name}'" in caplog.text # Updated message

def test_create_collection_success_overwrite(mock_client, caplog):
    """Test successful collection creation with overwrite."""
    caplog.set_level(logging.INFO)
    collection_name = "overwrite_collection"
    dimension = 64
    distance = Distance.EUCLID
    on_disk = True
    shards = 2
    hnsw_ef = 100 # Test HNSW config
    hnsw_m = 32
    mock_client.recreate_collection.return_value = True # Simulate success

    create_collection(
        client=mock_client,
        collection_name=collection_name,
        dimension=dimension,
        distance=distance,
        on_disk=on_disk,
        overwrite=True,
        shards=shards,
        hnsw_ef=hnsw_ef, # Pass HNSW params
        hnsw_m=hnsw_m
    )

    expected_vectors_config = VectorParams(size=dimension, distance=distance, on_disk=on_disk)
    expected_hnsw_config = HnswConfigDiff(ef_construct=hnsw_ef, m=hnsw_m)
    mock_client.recreate_collection.assert_called_once_with(
        collection_name=collection_name,
        vectors_config=expected_vectors_config,
        shard_number=shards,
        replication_factor=None,
        write_consistency_factor=None,
        hnsw_config=expected_hnsw_config, # Check HNSW config
        optimizers_config=None,
        wal_config=None,
        quantization_config=None,
        timeout=None
    )
    mock_client.create_collection.assert_not_called()
    assert f"Successfully recreated collection '{collection_name}'" in caplog.text # Updated message

def test_create_collection_missing_dimension(mock_client):
    """Test failure when dimension is None."""
    collection_name = "missing_dim_collection"
    distance = Distance.COSINE

    # Passing dimension=None should now raise ValidationError inside VectorParams creation
    with pytest.raises(ValidationError) as exc_info:
        create_collection(
            client=mock_client,
            collection_name=collection_name,
            dimension=None,
            distance=distance,
        )

    # Check Pydantic validation error message
    assert "validation error for vectorparams" in str(exc_info.value).lower()
    assert "size" in str(exc_info.value).lower() # Ensure 'size' field is mentioned
    mock_client.create_collection.assert_not_called()
    mock_client.recreate_collection.assert_not_called()

def test_create_collection_invalid_distance(mock_client):
    """Test failure when distance metric is invalid."""
    collection_name = "invalid_distance_collection"
    dimension = 128

    with pytest.raises(ConfigurationError) as exc_info:
        create_collection(
            client=mock_client,
            collection_name=collection_name,
            dimension=dimension,
            distance="INVALID_DISTANCE",
        )
    # Check for the error message - it might be in the details attribute
    error_details = getattr(exc_info.value, 'details', '')
    assert "Invalid distance metric" in str(exc_info.value)
    assert "INVALID_DISTANCE" in error_details
    mock_client.create_collection.assert_not_called()
    mock_client.recreate_collection.assert_not_called()

def test_create_collection_already_exists_no_overwrite(mock_client, caplog):
    """Test failure when collection exists and overwrite is False."""
    caplog.set_level(logging.WARNING)
    collection_name = "existing_collection"
    dimension = 128
    distance = Distance.COSINE
    # Simulate UnexpectedResponse(400) from create_collection
    mock_client.create_collection.side_effect = UnexpectedResponse(
        status_code=400,
        reason_phrase="Bad Request",
        headers={},
        content=b"Collection already exists!"
    )

    with pytest.raises(CollectionAlreadyExistsError):
        create_collection(
            client=mock_client,
            collection_name=collection_name,
            dimension=dimension,
            distance=distance,
            overwrite=False
        )

    mock_client.create_collection.assert_called_once()
    mock_client.recreate_collection.assert_not_called()
    assert f"Collection '{collection_name}' already exists. Use --overwrite to replace it." in caplog.text

def test_create_collection_failure_on_create(mock_client):
    """Test failure during the client.create_collection call (overwrite=False)."""
    collection_name = "fail_create_collection"
    dimension = 128
    distance = Distance.COSINE
    mock_client.create_collection.side_effect = ConnectionError("Qdrant down")

    with pytest.raises(CollectionError) as exc_info:
        create_collection(
            client=mock_client,
            collection_name=collection_name,
            dimension=dimension,
            distance=distance,
            # on_disk_payload=True, # Removed
            overwrite=False
        )

    assert "unexpected error" in str(exc_info.value).lower()
    assert "qdrant down" in str(exc_info.value).lower()
    mock_client.create_collection.assert_called_once()
    mock_client.recreate_collection.assert_not_called()

def test_create_collection_failure_on_recreate(mock_client):
    """Test failure during the client.recreate_collection call (overwrite=True)."""
    collection_name = "fail_recreate_collection"
    dimension = 128
    distance = Distance.COSINE
    mock_client.recreate_collection.side_effect = ConnectionError("Qdrant recreate failed")

    with pytest.raises(CollectionError) as exc_info:
        create_collection(
            client=mock_client,
            collection_name=collection_name,
            dimension=dimension,
            distance=distance,
            # on_disk_payload=False, # Removed
            overwrite=True
        )

    assert "unexpected error" in str(exc_info.value).lower()
    assert "qdrant recreate failed" in str(exc_info.value).lower()
    mock_client.recreate_collection.assert_called_once()
    mock_client.create_collection.assert_not_called()

# Remove old tests relying on mock_command
# def test_create_collection_missing_name(...):
# def test_create_collection_already_exists(...):
# def test_create_collection_failure(...):
# def test_create_collection_unexpected_error(...):
