"""Tests for Solr list command."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from argparse import Namespace
import logging
import json

from docstore_manager.solr.commands.list import list_collections
from docstore_manager.solr.command import SolrCommand
from docstore_manager.common.exceptions import FileOperationError, DocumentStoreError

@pytest.fixture
def mock_command():
    """Fixture for mocked SolrCommand."""
    return MagicMock(spec=SolrCommand)

@pytest.fixture
def mock_args():
    """Fixture for mocked command line arguments."""
    return Namespace(output=None)

@pytest.fixture
def mock_collection_list():
    return ["collection_a", "collection_b"]

def test_list_success_stdout(mock_command, mock_args, mock_collection_list, caplog, capsys):
    """Test successful list retrieval to stdout."""
    caplog.set_level(logging.INFO)
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = mock_collection_list
    mock_response.error = None
    mock_command.list_collections.return_value = mock_response

    list_collections(mock_command, mock_args)

    mock_command.list_collections.assert_called_once_with()
    assert "Retrieving list of collections" in caplog.text
    assert f"Found {len(mock_collection_list)} collections" in caplog.text
    
    captured = capsys.readouterr()
    assert captured.err == ""
    # Check stdout is valid JSON and matches data
    output_json = json.loads(captured.out.strip())
    assert output_json == mock_collection_list

def test_list_success_file(mock_command, mock_args, mock_collection_list, caplog):
    """Test successful list retrieval to file."""
    caplog.set_level(logging.INFO)
    mock_args.output = "list.json"
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = mock_collection_list
    mock_response.error = None
    mock_command.list_collections.return_value = mock_response

    m_open = mock_open()
    with patch("builtins.open", m_open):
        list_collections(mock_command, mock_args)

    mock_command.list_collections.assert_called_once_with()
    m_open.assert_called_once_with("list.json", "w")
    handle = m_open()
    written_data = "".join(call.args[0] for call in handle.write.call_args_list)
    assert json.loads(written_data) == mock_collection_list
    assert "Output written to list.json" in caplog.text

def test_list_no_collections(mock_command, mock_args, caplog, capsys):
    """Test list when no collections are found."""
    caplog.set_level(logging.INFO)
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = [] # Empty list for no results
    mock_response.error = None
    mock_command.list_collections.return_value = mock_response

    list_collections(mock_command, mock_args)

    assert "No collections found" in caplog.text
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

def test_list_command_failure(mock_command, mock_args):
    """Test handling failure from SolrCommand.list_collections."""
    mock_response = MagicMock()
    mock_response.success = False
    mock_response.error = "Connection refused"
    mock_command.list_collections.return_value = mock_response

    with pytest.raises(DocumentStoreError) as exc_info:
        list_collections(mock_command, mock_args)

    assert "Failed to list collections: Connection refused" in str(exc_info.value)
    assert exc_info.value.details == {'error': 'Connection refused'}
    mock_command.list_collections.assert_called_once_with()

def test_list_write_error(mock_command, mock_args, mock_collection_list):
    """Test handling error when writing output file."""
    mock_args.output = "list.json"
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = mock_collection_list
    mock_response.error = None
    mock_command.list_collections.return_value = mock_response

    m_open = mock_open()
    m_open.side_effect = IOError("Disk full")
    with patch("builtins.open", m_open):
        with pytest.raises(FileOperationError) as exc_info:
            list_collections(mock_command, mock_args)

    assert "Failed to write output: Disk full" in str(exc_info.value)
    assert exc_info.value.details == {
        'error': 'Disk full'
    }
    mock_command.list_collections.assert_called_once_with()

def test_list_unexpected_exception(mock_command, mock_args):
    """Test handling unexpected exception during list."""
    mock_command.list_collections.side_effect = TypeError("Unexpected type")

    with pytest.raises(DocumentStoreError) as exc_info:
        list_collections(mock_command, mock_args)

    assert "Unexpected error listing collections: Unexpected type" in str(exc_info.value)
    assert exc_info.value.details == {'error_type': 'TypeError'}
    mock_command.list_collections.assert_called_once_with() 