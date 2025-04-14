"""Tests for Qdrant count command."""

import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace
import logging
import json

from docstore_manager.qdrant.commands.count import count_documents, _parse_query
from docstore_manager.qdrant.command import QdrantCommand
from docstore_manager.common.exceptions import (
    CollectionError,
    DocumentError,
    QueryError
)

# --- Tests for _parse_query ---

def test_parse_query_valid():
    """Test parsing a valid JSON query string."""
    query_dict = {"filter": {"must": [{"key": "field", "match": {"value": "val"}}]}}
    query_str = json.dumps(query_dict)
    assert _parse_query(query_str) == query_dict

def test_parse_query_invalid():
    """Test parsing an invalid JSON query string."""
    with pytest.raises(QueryError) as exc_info:
        _parse_query('{"filter": }')
    assert "Invalid query JSON" in str(exc_info.value)

def test_parse_query_none():
    """Test parsing None query string."""
    assert _parse_query(None) is None

# --- Tests for count_documents ---

@pytest.fixture
def mock_command():
    """Fixture for mocked QdrantCommand."""
    return MagicMock(spec=QdrantCommand)

@pytest.fixture
def mock_args():
    """Fixture for mocked command line arguments."""
    return Namespace(
        collection="count_collection",
        query=None
    )

def test_count_success_no_query(mock_command, mock_args, caplog, capsys):
    """Test successful count with no query."""
    caplog.set_level(logging.INFO)
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.message = "Counted 123 documents"
    mock_response.data = 123
    mock_response.error = None
    mock_command.count_documents.return_value = mock_response

    count_documents(mock_command, mock_args)

    mock_command.count_documents.assert_called_once_with(collection="count_collection", query=None)
    assert "Counted 123 documents" in caplog.text
    captured = capsys.readouterr()
    assert captured.err == ""
    output_json = json.loads(captured.out.strip())
    assert output_json == {"count": 123}

def test_count_success_with_query(mock_command, mock_args, caplog, capsys):
    """Test successful count with a query."""
    caplog.set_level(logging.INFO)
    query_dict = {"filter": {"must": [{"key": "field", "match": {"value": "val"}}]}}
    mock_args.query = json.dumps(query_dict)
    
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.message = "Counted 45 documents matching query"
    mock_response.data = 45
    mock_response.error = None
    mock_command.count_documents.return_value = mock_response

    count_documents(mock_command, mock_args)

    mock_command.count_documents.assert_called_once_with(collection="count_collection", query=query_dict)
    assert "Counted 45 documents" in caplog.text # Check appropriate message if query applied
    captured = capsys.readouterr()
    assert captured.err == ""
    output_json = json.loads(captured.out.strip())
    assert output_json == {"count": 45}

def test_count_missing_collection(mock_command, mock_args):
    """Test count attempt with missing collection name."""
    mock_args.collection = None
    with pytest.raises(CollectionError) as exc_info:
        count_documents(mock_command, mock_args)
    assert exc_info.match(r"Collection name is required")
    mock_command.count_documents.assert_not_called()

def test_count_invalid_query_json(mock_command, mock_args):
    """Test count attempt with invalid query JSON."""
    mock_args.query = '{"filter": }'
    with pytest.raises(QueryError) as exc_info:
        count_documents(mock_command, mock_args)
    assert "Invalid query JSON" in str(exc_info.value)
    mock_command.count_documents.assert_not_called()

def test_count_command_failure(mock_command, mock_args):
    """Test handling failure from QdrantCommand.count_documents."""
    mock_response = MagicMock()
    mock_response.success = False
    mock_response.error = "Collection not found"
    mock_response.data = None
    mock_command.count_documents.return_value = mock_response

    with pytest.raises(DocumentError) as exc_info:
        count_documents(mock_command, mock_args)

    assert "Failed to count documents: Collection not found" in str(exc_info.value)
    assert exc_info.value.collection == "count_collection"
    mock_command.count_documents.assert_called_once_with(collection="count_collection", query=None)

def test_count_unexpected_exception(mock_command, mock_args):
    """Test handling unexpected exception during count."""
    mock_command.count_documents.side_effect = TimeoutError("Qdrant timed out")

    with pytest.raises(DocumentError) as exc_info:
        count_documents(mock_command, mock_args)

    assert "Unexpected error counting documents: Qdrant timed out" in str(exc_info.value)
    assert exc_info.value.collection == "count_collection"
    mock_command.count_documents.assert_called_once_with(collection="count_collection", query=None) 