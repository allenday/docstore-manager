"""Tests for Solr delete command."""

import pytest
from unittest.mock import patch, MagicMock
import logging

from docstore_manager.solr.commands.delete import delete_collection
from docstore_manager.solr.client import SolrClient
from docstore_manager.core.exceptions import (
    CollectionError,
    CollectionDoesNotExistError,
    DocumentStoreError
)

@pytest.fixture
def mock_client():
    """Fixture for mocked SolrClient."""
    return MagicMock(spec=SolrClient)

def test_delete_collection_success(mock_client, caplog):
    """Test successful deletion."""
    caplog.set_level(logging.INFO)
    collection_name = "delete_me"
    mock_client.delete_collection.return_value = None

    delete_collection(client=mock_client, collection_name=collection_name)

    mock_client.delete_collection.assert_called_once_with(collection_name)
    assert f"Attempting to delete Solr collection '{collection_name}'" in caplog.text
    assert f"Successfully submitted request to delete collection '{collection_name}'." in caplog.text

def test_delete_collection_not_found(mock_client):
    """Test handling collection not found failure."""
    collection_name = "delete_me_not_found"
    mock_client.delete_collection.side_effect = CollectionDoesNotExistError(collection_name)

    with pytest.raises(CollectionDoesNotExistError) as exc_info:
        delete_collection(client=mock_client, collection_name=collection_name)

    mock_client.delete_collection.assert_called_once_with(collection_name)

def test_delete_collection_command_failure(mock_client):
    """Test handling other failure from SolrClient.delete_collection."""
    collection_name = "delete_fail"
    error_message = "Some other Solr error"
    mock_client.delete_collection.side_effect = DocumentStoreError(error_message)

    with pytest.raises(DocumentStoreError, match=error_message):
        delete_collection(client=mock_client, collection_name=collection_name)

    mock_client.delete_collection.assert_called_once_with(collection_name)

def test_delete_collection_unexpected_exception(mock_client):
    """Test handling unexpected exception during deletion."""
    collection_name = "delete_crash"
    original_exception = TimeoutError("Request timed out")
    mock_client.delete_collection.side_effect = original_exception

    with pytest.raises(DocumentStoreError, match="An unexpected error occurred: Request timed out") as exc_info:
        delete_collection(client=mock_client, collection_name=collection_name)

    assert exc_info.value.__cause__ is original_exception
    mock_client.delete_collection.assert_called_once_with(collection_name) 