"""Tests for Solr info command."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import logging
import json

from docstore_manager.solr.commands.info import collection_info
from docstore_manager.solr.client import SolrClient
from docstore_manager.core.exceptions import DocumentStoreError, CollectionDoesNotExistError

@pytest.fixture
def mock_client():
    """Fixture for mocked SolrClient."""
    client = MagicMock(spec=SolrClient)
    client.client = MagicMock()
    client.client.ping.return_value = None
    client.client.url = "http://mock-solr/solr/info_collection"
    return client

@pytest.fixture
def mock_info_data():
    return {"status": "ok", "name": "info_collection", "client_url": "http://mock-solr/solr/info_collection"}

def test_info_success_stdout(mock_client, mock_info_data, caplog, capsys):
    """Test successful info retrieval to stdout."""
    caplog.set_level(logging.INFO)
    collection_name = "info_collection"
    
    collection_info(client=mock_client, collection_name=collection_name, output_path=None)

    mock_client.client.ping.assert_called_once()
    assert f"Fetching information for collection '{collection_name}'" in caplog.text
    assert f"Successfully retrieved basic info for collection '{collection_name}'" in caplog.text
    
    captured = capsys.readouterr()
    assert captured.err == ""
    output_json = json.loads(captured.out.strip())
    assert output_json == mock_info_data

def test_info_success_file(mock_client, mock_info_data, caplog):
    """Test successful info retrieval to file."""
    caplog.set_level(logging.INFO)
    collection_name = "info_collection"
    output_file = "info.json"

    m_open = mock_open()
    with patch("builtins.open", m_open):
        collection_info(client=mock_client, collection_name=collection_name, output_path=output_file)

    mock_client.client.ping.assert_called_once()
    m_open.assert_called_once_with(output_file, "w")
    handle = m_open()
    written_data = "".join(call.args[0] for call in handle.write.call_args_list)
    assert json.loads(written_data) == mock_info_data
    assert f"Collection info saved to: {output_file}" in caplog.text

def test_info_collection_not_found(mock_client):
    """Test handling CollectionDoesNotExistError."""
    collection_name = "not_found_collection"
    mock_client.client.ping.side_effect = CollectionDoesNotExistError(collection_name)

    with pytest.raises(CollectionDoesNotExistError) as exc_info:
        collection_info(client=mock_client, collection_name=collection_name)

    mock_client.client.ping.assert_called_once()

def test_info_command_failure(mock_client):
    """Test handling other DocumentStoreError."""
    collection_name = "fail_collection"
    error_message = "Solr connection failed"
    mock_client.client.ping.side_effect = DocumentStoreError(error_message)

    with pytest.raises(DocumentStoreError, match=error_message):
        collection_info(client=mock_client, collection_name=collection_name)

    mock_client.client.ping.assert_called_once()

def test_info_unexpected_exception(mock_client):
    """Test handling unexpected exception during info retrieval."""
    collection_name = "crash_collection"
    original_exception = TypeError("Bad data")
    mock_client.client.ping.side_effect = original_exception

    with pytest.raises(DocumentStoreError, match="An unexpected error occurred: Bad data") as exc_info:
        collection_info(client=mock_client, collection_name=collection_name)

    assert exc_info.value.__cause__ is original_exception
    mock_client.client.ping.assert_called_once() 