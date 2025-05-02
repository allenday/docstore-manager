"""Tests for Solr get command."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from argparse import Namespace
import logging
import json
import csv
import io

from docstore_manager.solr.commands.get import get_documents, _parse_query
from docstore_manager.solr.command import SolrCommand
from docstore_manager.core.command.base import CommandResponse
from docstore_manager.core.exceptions import (
    DocumentError,
    CollectionError,
    InvalidInputError
)

@pytest.fixture
def mock_command():
    """Fixture for mocked SolrCommand."""
    return MagicMock(spec=SolrCommand)

@pytest.fixture
def mock_args():
    """Fixture for mocked command line arguments."""
    return Namespace(
        collection="get_collection",
        query=None,
        fields=None,
        limit=None,
        output=None,
        format='json'
    )

@pytest.fixture
def mock_docs():
    return [
        {"id": "doc1", "field_a": "value1", "field_b": 10},
        {"id": "doc2", "field_a": "value2", "field_b": 20}
    ]

def test_get_documents_success_defaults(mock_command, mock_args, mock_docs, caplog, capsys):
    """Test successful get with default query and JSON to stdout."""
    caplog.set_level(logging.INFO)
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = mock_docs
    mock_response.error = None
    mock_command.search_documents.return_value = mock_response

    get_documents(mock_command, mock_args)

    expected_query = {'q': '*:*'} # Corrected default query
    mock_command.search_documents.assert_called_once_with(collection="get_collection", query=expected_query)
    assert "Retrieving documents from collection 'get_collection'" in caplog.text
    assert f"Query parameters: {expected_query}" in caplog.text
    assert f"Retrieved {len(mock_docs)} documents" in caplog.text
    
    captured = capsys.readouterr()
    assert captured.err == ""
    # Check stdout is valid JSON and matches data
    output_json = json.loads(captured.out.strip())
    assert output_json == mock_docs

def test_get_documents_success_args_json(mock_command, mock_args, mock_docs, caplog, capsys):
    """Test successful get with specific args and JSON to stdout."""
    caplog.set_level(logging.INFO)
    mock_args.query = "field_a:value1"
    mock_args.fields = "id,field_a"
    mock_args.limit = 1

    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = [mock_docs[0]] # Only first doc matches
    mock_response.error = None
    mock_command.search_documents.return_value = mock_response

    get_documents(mock_command, mock_args)

    expected_query = {'q': 'field_a:value1', 'fl': 'id,field_a', 'rows': 1}
    mock_command.search_documents.assert_called_once_with(collection="get_collection", query=expected_query)
    assert f"Query parameters: {expected_query}" in caplog.text
    assert f"Retrieved {len(mock_response.data)} documents" in caplog.text
    
    captured = capsys.readouterr()
    assert captured.err == ""
    output_json = json.loads(captured.out.strip())
    assert output_json == [mock_docs[0]]

def test_get_documents_success_csv_stdout(mock_command, mock_args, mock_docs, caplog, capsys):
    """Test successful get with CSV output to stdout."""
    caplog.set_level(logging.INFO)
    mock_args.format = 'csv'
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = mock_docs
    mock_response.error = None
    mock_command.search_documents.return_value = mock_response

    get_documents(mock_command, mock_args)

    captured = capsys.readouterr()
    assert captured.err == ""
    # Check CSV output
    output_lines = captured.out.strip().splitlines()
    assert len(output_lines) == 3 # Header + 2 rows
    assert output_lines[0].rstrip('\r') == "id,field_a,field_b"
    assert output_lines[1].rstrip('\r') == "doc1,value1,10"
    assert output_lines[2].rstrip('\r') == "doc2,value2,20"

def test_get_documents_success_json_file(mock_command, mock_args, mock_docs, caplog):
    """Test successful get with JSON output to file."""
    caplog.set_level(logging.INFO)
    mock_args.output = "output.json"
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = mock_docs
    mock_response.error = None
    mock_command.search_documents.return_value = mock_response

    m_open = mock_open()
    with patch("builtins.open", m_open):
        get_documents(mock_command, mock_args)

    m_open.assert_called_once_with("output.json", "w")
    # Check what was written to the mock file handle
    handle = m_open()
    written_data = "".join(call.args[0] for call in handle.write.call_args_list)
    assert json.loads(written_data) == mock_docs
    assert "Output written to output.json" in caplog.text

def test_get_documents_success_csv_file(mock_command, mock_args, mock_docs, caplog):
    """Test successful get with CSV output to file."""
    caplog.set_level(logging.INFO)
    mock_args.output = "output.csv"
    mock_args.format = 'csv'
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = mock_docs
    mock_response.error = None
    mock_command.search_documents.return_value = mock_response

    m_open = mock_open()
    with patch("builtins.open", m_open):
        get_documents(mock_command, mock_args)

    m_open.assert_called_once_with("output.csv", "w")
    # Check CSV content written to the mock file handle
    handle = m_open()
    # Collect all arguments passed to handle.write()
    written_content = "".join(call.args[0] for call in handle.write.call_args_list)
    written_data = written_content.strip().splitlines()

    assert len(written_data) == 3 # Header + 2 rows
    assert written_data[0].rstrip('\r') == "id,field_a,field_b"
    assert written_data[1].rstrip('\r') == "doc1,value1,10"
    assert written_data[2].rstrip('\r') == "doc2,value2,20"
    assert "Output written to output.csv" in caplog.text

def test_get_documents_no_results(mock_command, mock_args, caplog, capsys):
    """Test get when no documents are found."""
    caplog.set_level(logging.INFO)
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = [] # Empty list for no results
    mock_response.error = None
    mock_command.search_documents.return_value = mock_response

    get_documents(mock_command, mock_args)

    assert "No documents found" in caplog.text
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

def test_get_documents_missing_collection(mock_command, mock_args):
    """Test get attempt with missing collection name."""
    mock_args.collection = None
    with pytest.raises(CollectionError) as exc_info:
        get_documents(mock_command, mock_args)
    assert exc_info.match(r"Collection name is required")
    # assert exc_info.value.collection == "unknown"
    # assert exc_info.value.details == {'command': 'get'}

def test_get_documents_command_failure(mock_command, mock_args):
    """Test handling failure from SolrCommand.search_documents."""
    mock_response = MagicMock()
    mock_response.success = False
    mock_response.error = "Invalid query syntax"
    mock_command.search_documents.return_value = mock_response
    expected_query = {'q': '*:*'}

    with pytest.raises(InvalidInputError) as exc_info:
        get_documents(mock_command, mock_args)

    assert "Failed to retrieve documents: Invalid query syntax" in str(exc_info.value)
    assert exc_info.value.query == expected_query # Check query attribute is set
    assert exc_info.value.details == {
        'collection': 'get_collection',
        # 'query': expected_query, # Query is not in details
        'error': 'Invalid query syntax'
    }

def test_get_documents_write_error(mock_command, mock_args, mock_docs):
    """Test handling error when writing output file."""
    mock_args.output = "output.json"
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = mock_docs
    mock_response.error = None
    mock_command.search_documents.return_value = mock_response

    m_open = mock_open()
    m_open.side_effect = IOError("Permission denied")
    with patch("builtins.open", m_open):
        with pytest.raises(InvalidInputError) as exc_info:
            get_documents(mock_command, mock_args)

    assert "Failed to write output: Permission denied" in str(exc_info.value)
    assert exc_info.value.file_path == 'output.json' # Check file_path attribute
    assert exc_info.value.details == {
        'format': 'json', # Corrected details
        'error': 'Permission denied'
    }

def test_get_documents_unexpected_exception(mock_command, mock_args):
    """Test handling unexpected exception during get."""
    mock_command.search_documents.side_effect = ValueError("Unexpected error")

    with pytest.raises(InvalidInputError) as exc_info:
        get_documents(mock_command, mock_args)

    assert "Unexpected error retrieving documents: Unexpected error" in str(exc_info.value)
    assert exc_info.value.query == {'q': '*:*'} # Check query attribute is set
    assert exc_info.value.details == {
        'collection': 'get_collection',
        'error_type': 'ValueError'
    } 