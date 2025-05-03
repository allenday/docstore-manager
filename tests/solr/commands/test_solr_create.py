"""Tests for Solr create command."""

import pytest
from unittest.mock import patch, MagicMock
import logging
import json

from docstore_manager.solr.commands.create import create_collection
from docstore_manager.solr.client import SolrClient
from docstore_manager.core.exceptions import DocumentStoreError, CollectionError

@pytest.fixture
def mock_client():
    """Fixture for mocked SolrClient."""
    client = MagicMock(spec=SolrClient)
    # Pre-configure list_collections to return an empty list by default for overwrite checks
    client.list_collections.return_value = [] 
    return client

def test_create_collection_success_defaults(mock_client, caplog):
    """Test successful creation with default arguments."""
    caplog.set_level(logging.INFO)
    collection_name = "new_collection"
    
    # Mock the methods called within create_collection
    mock_client.create_collection.return_value = None # Assume void on success

    success, message = create_collection(
        client=mock_client, 
        collection_name=collection_name,
        num_shards=None,
        replication_factor=None,
        config_name=None,
        overwrite=False
    )

    assert success is True
    assert message == f"Successfully created Solr collection '{collection_name}'."
    mock_client.list_collections.assert_called_once_with() # Check existence check
    mock_client.create_collection.assert_called_once_with(
        name=collection_name,
        num_shards=None,
        replication_factor=None,
        config_name=None
    )
    assert f"Attempting to create/recreate Solr collection '{collection_name}'" in caplog.text
    assert message in caplog.text

def test_create_collection_success_with_args(mock_client, caplog):
    """Test successful creation with specific arguments."""
    caplog.set_level(logging.INFO)
    collection_name = "new_collection_args"
    num_shards = 2
    replication_factor = 2
    config_name = "my_config"
    
    mock_client.create_collection.return_value = None # Assume void on success

    success, message = create_collection(
        client=mock_client, 
        collection_name=collection_name,
        num_shards=num_shards,
        replication_factor=replication_factor,
        config_name=config_name,
        overwrite=False
    )

    assert success is True
    assert message == f"Successfully created Solr collection '{collection_name}'."
    mock_client.list_collections.assert_called_once_with() # Check existence check
    mock_client.create_collection.assert_called_once_with(
        name=collection_name,
        num_shards=num_shards,
        replication_factor=replication_factor,
        config_name=config_name
    )
    assert message in caplog.text

def test_create_collection_overwrite_success(mock_client, caplog):
    """Test successful overwrite when collection exists."""
    caplog.set_level(logging.INFO)
    collection_name = "existing_collection"
    
    # Simulate collection existing
    mock_client.list_collections.return_value = [collection_name, "other_collection"]
    mock_client.delete_collection.return_value = None # Assume void
    mock_client.create_collection.return_value = None # Assume void
    
    success, message = create_collection(
        client=mock_client, 
        collection_name=collection_name,
        overwrite=True
    )
    
    assert success is True
    assert message == f"Successfully created Solr collection '{collection_name}'."
    mock_client.list_collections.assert_called_once_with()
    mock_client.delete_collection.assert_called_once_with(collection_name)
    mock_client.create_collection.assert_called_once_with(
        name=collection_name,
        num_shards=None,
        replication_factor=None,
        config_name=None
    )
    assert f"Collection '{collection_name}' exists and overwrite=True. Deleting first..." in caplog.text
    assert f"Successfully deleted existing collection '{collection_name}'" in caplog.text
    assert message in caplog.text

def test_create_collection_exists_no_overwrite(mock_client, caplog):
    """Test failure when collection exists and overwrite is False."""
    caplog.set_level(logging.WARNING)
    collection_name = "existing_collection"
    
    # Simulate collection existing
    mock_client.list_collections.return_value = [collection_name, "other_collection"]
    
    success, message = create_collection(
        client=mock_client, 
        collection_name=collection_name,
        overwrite=False
    )
    
    assert success is False
    assert message == f"Collection '{collection_name}' already exists. Use --overwrite to replace it."
    mock_client.list_collections.assert_called_once_with()
    mock_client.delete_collection.assert_not_called()
    mock_client.create_collection.assert_not_called()
    assert message in caplog.text

def test_create_collection_overwrite_delete_fails(mock_client, caplog):
    """Test failure when overwrite delete fails."""
    caplog.set_level(logging.ERROR)
    collection_name = "existing_collection"
    
    mock_client.list_collections.return_value = [collection_name]
    mock_client.delete_collection.side_effect = DocumentStoreError("Delete permission denied")
    
    with pytest.raises(CollectionError, match="Failed to delete existing collection .* Delete permission denied"):
        create_collection(
            client=mock_client, 
            collection_name=collection_name,
            overwrite=True
        )
        
    mock_client.list_collections.assert_called_once_with()
    mock_client.delete_collection.assert_called_once_with(collection_name)
    mock_client.create_collection.assert_not_called()
    assert f"Failed to delete existing collection '{collection_name}' before overwrite" in caplog.text

def test_create_collection_command_failure(mock_client, caplog):
    """Test handling failure from SolrClient.create_collection."""
    caplog.set_level(logging.ERROR)
    collection_name = "fail_collection"
    
    mock_client.list_collections.return_value = [] # Ensure it doesn't exist
    mock_client.create_collection.side_effect = CollectionError(collection_name="fail_collection", message="Invalid config name")

    with pytest.raises(CollectionError, match="Invalid config name"):
        create_collection(
            client=mock_client, 
            collection_name=collection_name
        )

    mock_client.list_collections.assert_called_once_with()
    mock_client.create_collection.assert_called_once_with(
        name=collection_name,
        num_shards=None,
        replication_factor=None,
        config_name=None
    )
    assert f"Error creating collection '{collection_name}': Invalid config name" in caplog.text

def test_create_collection_unexpected_exception(mock_client, caplog):
    """Test handling unexpected exception during creation."""
    caplog.set_level(logging.ERROR)
    collection_name = "crash_collection"
    
    mock_client.list_collections.return_value = []
    # Simulate unexpected error during create call
    mock_client.create_collection.side_effect = ConnectionError("Solr down") 

    with pytest.raises(DocumentStoreError, match="Unexpected error creating collection .* Solr down"):
        create_collection(
            client=mock_client, 
            collection_name=collection_name
        )

    mock_client.list_collections.assert_called_once_with()
    mock_client.create_collection.assert_called_once_with(
        name=collection_name,
        num_shards=None,
        replication_factor=None,
        config_name=None
    )
    assert f"Unexpected error creating collection '{collection_name}'" in caplog.text 