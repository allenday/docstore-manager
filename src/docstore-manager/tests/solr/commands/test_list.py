"""Tests for Solr list command."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import logging
import json
import io

from docstore_manager.solr.commands.list import list_collections
from docstore_manager.solr.client import SolrClient
from docstore_manager.core.exceptions import DocumentStoreError

@pytest.fixture
def mock_client():
    """Fixture for mocked SolrClient."""
    return MagicMock(spec=SolrClient)

@pytest.fixture
def mock_collection_list():
    return ["collection_a", "collection_b"]

def test_list_success_stdout(mock_client, mock_collection_list, caplog, capsys):
    """Test successful list retrieval to stdout."""
    caplog.set_level(logging.INFO)
    mock_client.list_collections.return_value = mock_collection_list

    list_collections(client=mock_client, output_path=None)

    mock_client.list_collections.assert_called_once_with()
    assert "Successfully listed collections" in caplog.text
    
    captured = capsys.readouterr()
    assert captured.err == ""
    # Check stdout is valid JSON and matches data
    output_json = json.loads(captured.out.strip())
    assert output_json == mock_collection_list

def test_list_success_file(mock_client, mock_collection_list, caplog):
    """Test successful list retrieval to file."""
    caplog.set_level(logging.INFO)
    output_file_path = "list.json"
    mock_client.list_collections.return_value = mock_collection_list

    m_open = mock_open()
    with patch("builtins.open", m_open):
        list_collections(client=mock_client, output_path=output_file_path)

    mock_client.list_collections.assert_called_once_with()
    m_open.assert_called_once_with(output_file_path, "w")
    handle = m_open()
    written_data = "".join(call.args[0] for call in handle.write.call_args_list)
    assert json.loads(written_data) == mock_collection_list
    assert f"Collection list saved to: {output_file_path}" in caplog.text

def test_list_no_collections(mock_client, caplog, capsys):
    """Test list when no collections are found."""
    caplog.set_level(logging.INFO)
    mock_client.list_collections.return_value = []

    list_collections(client=mock_client, output_path=None)

    assert "Successfully listed collections" in caplog.text
    captured = capsys.readouterr()
    assert captured.out.strip() == "[]"
    assert captured.err == ""

def test_list_command_failure(mock_client):
    """Test handling failure from SolrClient.list_collections."""
    mock_client.list_collections.side_effect = DocumentStoreError("Connection refused")

    with pytest.raises(DocumentStoreError, match="Connection refused") as exc_info:
        list_collections(client=mock_client, output_path=None)

    mock_client.list_collections.assert_called_once_with()

def test_list_write_error(mock_client, mock_collection_list):
    """Test handling error when writing output file."""
    output_file_path = "list.json"
    mock_client.list_collections.return_value = mock_collection_list

    m_open = mock_open()
    m_open.side_effect = IOError("Disk full")
    with patch("builtins.open", m_open):
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            list_collections(client=mock_client, output_path=output_file_path)
            
            stdout_value = mock_stdout.getvalue()
            assert "Failed to write to file, printing to stdout instead:" in stdout_value
            output_json = json.loads(stdout_value.split("instead:")[-1].strip())
            assert output_json == mock_collection_list

    mock_client.list_collections.assert_called_once_with()

def test_list_unexpected_exception(mock_client):
    """Test handling unexpected exception during list."""
    mock_client.list_collections.side_effect = TypeError("Unexpected type")

    with pytest.raises(DocumentStoreError, match="An unexpected error occurred: Unexpected type") as exc_info:
        list_collections(client=mock_client, output_path=None)

    mock_client.list_collections.assert_called_once_with() 