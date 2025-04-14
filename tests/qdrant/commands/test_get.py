"""Tests for get points command."""

import pytest
import json
from unittest.mock import patch, MagicMock, mock_open
from argparse import Namespace
import logging

from qdrant_client import QdrantClient

from docstore_manager.qdrant.commands.get import (
    get_documents,
    search_documents,
    _parse_query,
    _parse_ids_for_get
)
from docstore_manager.common.exceptions import (
    CollectionError,
    DocumentError,
    QueryError,
    FileOperationError
)
from docstore_manager.qdrant.command import QdrantCommand

@pytest.fixture
def mock_client():
    return MagicMock(spec=QdrantClient)

@pytest.fixture
def mock_command(mock_client):
    cmd = MagicMock(spec=QdrantCommand)
    cmd.client = mock_client
    return cmd

@pytest.fixture
def mock_args():
    args = MagicMock()
    args.collection = "test_collection"
    args.file = None
    args.ids = "id1,id2"
    args.with_vectors = False
    args.output = None
    args.format = "json"
    args.query = None
    args.limit = 10
    return args

def test_parse_query_valid():
    """Test parsing a valid query string."""
    query_str = '{"field": "value"}'
    result = _parse_query(query_str)
    assert result == {"field": "value"}

def test_parse_query_invalid():
    """Test parsing an invalid query string."""
    query_str = '{"field": invalid}'
    with pytest.raises(QueryError) as exc_info:
        _parse_query(query_str)
    assert "Invalid JSON in query" in str(exc_info.value)

def test_parse_ids_from_string():
    """Test parsing IDs from a comma-separated string."""
    args = MagicMock()
    args.file = None
    args.ids = "id1, id2 ,id3 "
    result = _parse_ids_for_get(args)
    assert result == ["id1", "id2", "id3"]

def test_parse_ids_from_file():
    """Test parsing IDs from a file."""
    args = MagicMock()
    args.file = "ids.txt"
    args.ids = None
    with patch("builtins.open", mock_open(read_data="id1\nid2\nid3\n")):
        result = _parse_ids_for_get(args)
    assert result == ["id1", "id2", "id3"]

def test_parse_ids_file_not_found():
    """Test handling of non-existent ID file."""
    args = MagicMock()
    args.file = "non_existent.txt"
    args.ids = None
    with patch("builtins.open", side_effect=FileNotFoundError):
        result = _parse_ids_for_get(args)
    assert result is None

def test_get_documents_missing_collection(mock_command, mock_args):
    """Test get documents with missing collection name."""
    mock_args.collection = None
    with pytest.raises(CollectionError) as exc_info:
        get_documents(mock_command, mock_args)
    assert "Collection name is required" in str(exc_info.value)

def test_get_documents_missing_ids_and_file(mock_command, mock_args):
    """Test get documents without specifying IDs or a file."""
    mock_args.ids = None
    mock_args.file = None
    with pytest.raises(DocumentError) as exc_info:
        get_documents(mock_command, mock_args)
    assert "Either --file or --ids must be specified" in str(exc_info.value)

def test_get_documents_success_from_ids(mock_command, mock_args, capsys):
    """Test successful retrieval of documents by IDs."""
    mock_args.ids = "id1,id2"
    mock_args.file = None
    mock_response = {
        "success": True,
        "data": [{"id": "id1", "payload": {"field": "value1"}}, {"id": "id2", "payload": {"field": "value2"}}],
        "message": "Retrieved 2 documents",
        "error": None
    }
    mock_command.get_documents.return_value = mock_response

    get_documents(mock_command, mock_args)

    mock_command.get_documents.assert_called_once_with(
        collection="test_collection",
        ids=["id1", "id2"],
        with_vectors=False
    )
    captured = capsys.readouterr()
    assert "value1" in captured.out
    assert "value2" in captured.out

def test_get_documents_success_from_file(mock_command, mock_args, capsys):
    """Test successful retrieval of documents from a file."""
    mock_args.ids = None
    mock_args.file = "ids.txt"
    mock_response = {
        "success": True,
        "data": [{"id": "id1", "payload": {"field": "value1"}}],
        "message": "Retrieved 1 document",
        "error": None
    }
    mock_command.get_documents.return_value = mock_response

    with patch("builtins.open", mock_open(read_data="id1\n")):
        get_documents(mock_command, mock_args)

    mock_command.get_documents.assert_called_once_with(
        collection="test_collection",
        ids=["id1"],
        with_vectors=False
    )
    captured = capsys.readouterr()
    assert "value1" in captured.out

def test_get_documents_no_results(mock_command, mock_args, caplog):
    """Test get documents with no results found."""
    mock_response = {
        "success": True,
        "data": [],
        "message": "No documents found for the given IDs",
        "error": None
    }
    mock_command.get_documents.return_value = mock_response

    with caplog.at_level(logging.INFO):
        get_documents(mock_command, mock_args)

    mock_command.get_documents.assert_called_once_with(
        collection="test_collection", ids=["id1", "id2"], with_vectors=False
    )
    assert "No documents found." in caplog.text

def test_get_documents_failure(mock_command, mock_args):
    """Test handling of failed document retrieval."""
    mock_response = {
        "success": False,
        "error": "Failed to retrieve",
        "data": None,
        "message": None
    }
    mock_command.get_documents.return_value = mock_response

    with pytest.raises(DocumentError) as exc_info:
        get_documents(mock_command, mock_args)

    assert "Failed to retrieve documents: Failed to retrieve" in str(exc_info.value)
    assert exc_info.value.collection == "test_collection"

def test_get_documents_with_output_file(mock_command, mock_args):
    """Test get documents with output to file."""
    mock_args.output = "output.json"
    mock_response = {
        "success": True,
        "data": [{"id": "id1", "payload": {}}],
        "message": "Retrieved 1 document",
        "error": None
    }
    mock_command.get_documents.return_value = mock_response

    mock_open_instance = mock_open()
    with patch("builtins.open", mock_open_instance):
        get_documents(mock_command, mock_args)

    mock_command.get_documents.assert_called_once()
    mock_open_instance.assert_called_once_with("output.json", "w")

def test_get_documents_with_csv_output(mock_command, mock_args, capsys):
    """Test get documents with CSV output format."""
    mock_args.format = "csv"
    mock_args.output = None
    mock_response = {
        "success": True,
        "data": [{"id": "id1", "payload_field": "value1"}, {"id": "id2", "payload_field": "value2"}],
        "message": "Retrieved 2 documents",
        "error": None
    }
    mock_command.get_documents.return_value = mock_response

    get_documents(mock_command, mock_args)

    mock_command.get_documents.assert_called_once()
    captured = capsys.readouterr()
    assert "id,payload_field" in captured.out
    assert "id1,value1" in captured.out
    assert "id2,value2" in captured.out

def test_get_documents_file_write_error(mock_command, mock_args):
    """Test handling of file write errors."""
    mock_args.output = "output.json"
    mock_response = {
        "success": True,
        "data": [{"id": "id1", "payload": {}}],
        "message": "Retrieved 1 document",
        "error": None
    }
    mock_command.get_documents.return_value = mock_response

    mock_open_instance = mock_open()
    mock_open_instance().write.side_effect = IOError("Disk full")
    with patch("builtins.open", mock_open_instance):
        with pytest.raises(FileOperationError) as exc_info:
            get_documents(mock_command, mock_args)

    assert "Failed to write output: Disk full" in str(exc_info.value)
    assert exc_info.value.file_path == "output.json"

def test_get_documents_unexpected_error(mock_command, mock_args):
    """Test handling of unexpected errors during get."""
    mock_command.get_documents.side_effect = Exception("Unexpected error")

    with pytest.raises(DocumentError) as exc_info:
        get_documents(mock_command, mock_args)

    assert "Unexpected error retrieving documents: Unexpected error" in str(exc_info.value)
    assert exc_info.value.collection == "test_collection"

def test_search_documents_with_query(mock_command, mock_args, capsys):
    """Test search documents with a query."""
    query_dict = {"filter": {"must": [{"key": "field", "match": {"value": "search_val"}}]}}
    mock_args.query = json.dumps(query_dict)
    mock_args.ids = None
    mock_args.file = None

    mock_response = {
        "success": True,
        "data": [{"id": "res1", "score": 0.9, "payload": {"field": "search_val"}}],
        "message": "Found 1 document",
        "error": None
    }
    mock_command.search_documents.return_value = mock_response

    search_documents(mock_command, mock_args)

    mock_command.search_documents.assert_called_once_with(
        collection="test_collection",
        query=query_dict,
        limit=10,
        with_vectors=False
    )
    captured = capsys.readouterr()
    assert "res1" in captured.out
    assert "search_val" in captured.out

def test_search_documents_invalid_query(mock_command, mock_args):
    """Test search documents with an invalid query JSON."""
    mock_args.query = "{\'invalid_json\'"
    mock_args.ids = None
    mock_args.file = None

    with pytest.raises(QueryError) as exc_info:
        search_documents(mock_command, mock_args)
        
    assert "Invalid JSON in query" in str(exc_info.value)

def test_search_documents_failure(mock_command, mock_args):
    """Test handling of failed document search."""
    query_dict = {"filter": {"must": []}}
    mock_args.query = json.dumps(query_dict)
    mock_args.ids = None
    mock_args.file = None

    mock_response = {
        "success": False,
        "error": "Search failed",
        "data": None,
        "message": None
    }
    mock_command.search_documents.return_value = mock_response

    with pytest.raises(DocumentError) as exc_info:
        search_documents(mock_command, mock_args)

    assert "Failed to search documents: Search failed" in str(exc_info.value)
    assert exc_info.value.collection == "test_collection"

def test_search_documents_unexpected_error(mock_command, mock_args):
    """Test handling of unexpected errors during search."""
    query_dict = {"filter": {"must": []}}
    mock_args.query = json.dumps(query_dict)
    mock_args.ids = None
    mock_args.file = None
    
    mock_command.search_documents.side_effect = Exception("Unexpected search error")

    with pytest.raises(DocumentError) as exc_info:
        search_documents(mock_command, mock_args)

    assert "Unexpected error searching documents: Unexpected search error" in str(exc_info.value)
    assert exc_info.value.collection == "test_collection" 