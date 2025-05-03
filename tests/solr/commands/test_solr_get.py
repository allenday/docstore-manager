"""Tests for Solr get command."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import logging
import json
import csv
import io

from docstore_manager.solr.commands.get import get_documents
from docstore_manager.solr.client import SolrClient
from docstore_manager.core.exceptions import (
    DocumentStoreError,
    InvalidInputError
)

# Helper to simulate pysolr.Results
class MockSolrResults:
    def __init__(self, docs, hits):
        self.docs = docs
        self.hits = hits

@pytest.fixture
def mock_client():
    """Fixture for mocked SolrClient."""
    client = MagicMock(spec=SolrClient)
    # Configure search to return an empty result by default
    client.search.return_value = MockSolrResults([], 0)
    return client

@pytest.fixture
def mock_docs():
    return [
        {"id": "doc1", "field_a": "value1", "field_b": 10},
        {"id": "doc2", "field_a": "value2", "field_b": 20}
    ]

def test_get_documents_success_defaults(mock_client, mock_docs, caplog, capsys):
    """Test successful get with default query and JSON to stdout."""
    caplog.set_level(logging.INFO)
    collection_name = "get_collection_defaults"
    doc_ids_to_get = [doc['id'] for doc in mock_docs]
    mock_client.search.return_value = MockSolrResults(mock_docs, len(mock_docs))

    get_documents(
        client=mock_client,
        collection_name=collection_name,
        doc_ids=doc_ids_to_get
    )

    mock_client.search.assert_called_once()
    args, kwargs = mock_client.search.call_args
    assert args[0] == collection_name
    expected_query = f"id:({' OR '.join(doc_ids_to_get)})"
    assert isinstance(args[1], dict)
    assert args[1]['q'] == expected_query
    
    # Check log for JSON output
    assert "[" in caplog.text
    assert "doc1" in caplog.text
    assert "doc2" in caplog.text
    # Check stdout is empty
    captured = capsys.readouterr()
    assert captured.out.strip() == ""

def test_get_documents_success_args_json(mock_client, mock_docs, caplog, capsys):
    """Test successful get with specific args and JSON to stdout."""
    caplog.set_level(logging.INFO)
    collection_name = "get_collection_args"
    doc_ids_to_get = [mock_docs[0]['id']]
    mock_client.search.return_value = MockSolrResults([mock_docs[0]], 1)

    get_documents(
        client=mock_client,
        collection_name=collection_name,
        doc_ids=doc_ids_to_get
    )

    mock_client.search.assert_called_once()
    args, kwargs = mock_client.search.call_args
    assert args[0] == collection_name
    expected_query = f"id:({' OR '.join(doc_ids_to_get)})"
    assert isinstance(args[1], dict)
    assert args[1]['q'] == expected_query
    
    # Check log for JSON output (only doc1)
    assert "[" in caplog.text
    assert "doc1" in caplog.text
    assert "doc2" not in caplog.text
    # Check stdout is empty
    captured = capsys.readouterr()
    assert captured.out.strip() == ""

def test_get_documents_success_json_file(mock_client, mock_docs, caplog):
    """Test successful get with JSON output to file."""
    caplog.set_level(logging.INFO)
    collection_name = "get_json_file"
    output_file = "output.json"
    doc_ids_to_get = [doc['id'] for doc in mock_docs]
    mock_client.search.return_value = MockSolrResults(mock_docs, len(mock_docs))

    m_open = mock_open()
    with patch("builtins.open", m_open):
        get_documents(
            client=mock_client,
            collection_name=collection_name,
            doc_ids=doc_ids_to_get,
            output_path=output_file
        )

    mock_client.search.assert_called_once()
    args, kwargs = mock_client.search.call_args
    assert args[0] == collection_name
    expected_query = f"id:({' OR '.join(doc_ids_to_get)})"
    assert isinstance(args[1], dict)
    assert args[1]['q'] == expected_query
    m_open.assert_called_once_with(output_file, "w")
    handle = m_open()
    handle.write.assert_called_once()
    written_content = handle.write.call_args[0][0]
    assert "doc1" in written_content
    assert "doc2" in written_content
    assert "Output saved to output.json" in caplog.text

def test_get_documents_no_results(mock_client, caplog, capsys):
    """Test get when no documents are found."""
    caplog.set_level(logging.INFO)
    collection_name = "get_no_results"
    doc_ids_to_get = ['missing_id']
    mock_client.search.return_value = MockSolrResults([], 0)

    get_documents(
        client=mock_client,
        collection_name=collection_name,
        doc_ids=doc_ids_to_get
    )

    mock_client.search.assert_called_once()
    args, kwargs = mock_client.search.call_args
    assert args[0] == collection_name
    expected_query = f"id:({' OR '.join(doc_ids_to_get)})"
    assert isinstance(args[1], dict)
    assert args[1]['q'] == expected_query
    assert "No documents found for the provided IDs" in caplog.text
    # Check log for empty list output
    assert "[]" in caplog.text
    # Check stdout is empty
    captured = capsys.readouterr()
    assert captured.out.strip() == ""

def test_get_documents_command_failure(mock_client):
    """Test handling failure from SolrClient.search."""
    collection_name = "get_fail"
    error_message = "Invalid query syntax"
    doc_ids_to_get = ['doc1']
    mock_client.search.side_effect = DocumentStoreError("Solr API error during retrieval", details=error_message)
    
    with pytest.raises(DocumentStoreError, match="Solr API error during retrieval"):
        get_documents(
            client=mock_client,
            collection_name=collection_name,
            doc_ids=doc_ids_to_get
        )

    mock_client.search.assert_called_once()

def test_get_documents_write_error(mock_client, mock_docs, caplog):
    """Test handling error when writing output file."""
    caplog.set_level(logging.ERROR)
    collection_name = "get_write_error"
    output_file = "output.json"
    doc_ids_to_get = [doc['id'] for doc in mock_docs]
    mock_client.search.return_value = MockSolrResults(mock_docs, len(mock_docs))

    m_open = mock_open()
    m_open.side_effect = IOError("Permission denied")
    with patch("builtins.open", m_open):
        get_documents(
            client=mock_client,
            collection_name=collection_name,
            doc_ids=doc_ids_to_get,
            output_path=output_file
        )

    mock_client.search.assert_called_once()
    args, kwargs = mock_client.search.call_args
    assert args[0] == collection_name
    expected_query = f"id:({' OR '.join(doc_ids_to_get)})"
    assert isinstance(args[1], dict)
    assert args[1]['q'] == expected_query
    assert "Error formatting or writing output: Permission denied" in caplog.text

def test_get_documents_unexpected_exception(mock_client):
    """Test handling unexpected exception during get."""
    collection_name = "get_crash"
    original_exception = ValueError("Unexpected format")
    doc_ids_to_get = ['doc1']
    mock_client.search.side_effect = original_exception

    with pytest.raises(DocumentStoreError, match="Unexpected error retrieving documents: Unexpected format") as exc_info:
        get_documents(
            client=mock_client,
            collection_name=collection_name,
            doc_ids=doc_ids_to_get
        )

    mock_client.search.assert_called_once()
    assert exc_info.value.__cause__ is original_exception 