"""Tests for Solr info command."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from argparse import Namespace
import logging
import json

from docstore_manager.solr.commands.info import collection_info
from docstore_manager.solr.command import SolrCommand
from docstore_manager.core.exceptions import ConfigurationError

@pytest.fixture
def mock_command():
    """Fixture for mocked SolrCommand."""
    return MagicMock(spec=SolrCommand)

@pytest.fixture
def mock_args():
    """Fixture for mocked command line arguments."""
    return Namespace(
        collection="info_collection",
        output=None
    )

@pytest.fixture
def mock_info_data():
    return {"configName": "_default", "shards": {"shard1": {}}}

def test_info_success_stdout(mock_command, mock_args, mock_info_data, caplog, capsys):
    """Test successful info retrieval to stdout."""
    caplog.set_level(logging.INFO)
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = mock_info_data
    mock_response.error = None
    mock_command.get_collection_info.return_value = mock_response

    collection_info(mock_command, mock_args)

    mock_command.get_collection_info.assert_called_once_with("info_collection")
    assert "Retrieving information for collection 'info_collection'" in caplog.text
    
    captured = capsys.readouterr()
    assert captured.err == ""
    # Check stdout is valid JSON and matches data
    output_json = json.loads(captured.out.strip())
    assert output_json == mock_info_data

def test_info_success_file(mock_command, mock_args, mock_info_data, caplog):
    """Test successful info retrieval to file."""
    caplog.set_level(logging.INFO)
    mock_args.output = "info.json"
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = mock_info_data
    mock_response.error = None
    mock_command.get_collection_info.return_value = mock_response

    m_open = mock_open()
    with patch("builtins.open", m_open):
        collection_info(mock_command, mock_args)

    mock_command.get_collection_info.assert_called_once_with("info_collection")
    m_open.assert_called_once_with("info.json", "w")
    handle = m_open()
    written_data = "".join(call.args[0] for call in handle.write.call_args_list)
    assert json.loads(written_data) == mock_info_data
    assert "Collection info written to info.json" in caplog.text

def test_info_missing_collection(mock_command, mock_args, caplog):
    """Test info attempt with missing collection name."""
    caplog.set_level(logging.ERROR)
    mock_args.collection = None

    collection_info(mock_command, mock_args)

    mock_command.get_collection_info.assert_not_called()
    assert "Collection name is required" in caplog.text

def test_info_command_failure(mock_command, mock_args):
    """Test handling failure from SolrCommand.get_collection_info."""
    mock_response = MagicMock()
    mock_response.success = False
    mock_response.error = "Collection not found"
    mock_command.get_collection_info.return_value = mock_response

    with pytest.raises(ConfigurationError) as exc_info:
        collection_info(mock_command, mock_args)

    assert "Failed to get collection info: Collection not found" in str(exc_info.value)
    assert exc_info.value.details == {
        'collection': 'info_collection',
        'error': 'Collection not found'
    }
    mock_command.get_collection_info.assert_called_once_with("info_collection")

def test_info_unexpected_exception(mock_command, mock_args):
    """Test handling unexpected exception during info retrieval."""
    mock_command.get_collection_info.side_effect = ValueError("Unexpected error")

    with pytest.raises(ConfigurationError) as exc_info:
        collection_info(mock_command, mock_args)

    assert "Unexpected error getting collection info: Unexpected error" in str(exc_info.value)
    assert exc_info.value.details == {
        'collection': 'info_collection',
        'error_type': 'ValueError'
    }
    mock_command.get_collection_info.assert_called_once_with("info_collection") 