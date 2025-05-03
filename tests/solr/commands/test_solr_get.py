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
    mock_client.search.return_value = MockSolrResults(mock_docs, len(mock_docs))

    get_documents(
        client=mock_client,
        collection_name=collection_name,
        query='*:*',  # Explicitly pass default query for clarity
    )

    expected_search_params = {'q': '*:*', 'rows': 10, 'fl': '*'}
    mock_client.search.assert_called_once_with(**expected_search_params)
    assert f"Attempting to get documents by query '*:*' from '{collection_name}'" in caplog.text
    assert f"Retrieved {len(mock_docs)} documents (total found: {len(mock_docs)})" in caplog.text
    
    captured = capsys.readouterr()
    assert captured.err == ""
    output_json = json.loads(captured.out.strip())
    assert output_json == mock_docs

def test_get_documents_success_args_json(mock_client, mock_docs, caplog, capsys):
    """Test successful get with specific args and JSON to stdout."""
    caplog.set_level(logging.INFO)
    collection_name = "get_collection_args"
    query = "field_a:value1"
    fields = "id,field_a"
    limit = 1
    mock_client.search.return_value = MockSolrResults([mock_docs[0]], 1)  # Only first doc matches

    get_documents(
        client=mock_client,
        collection_name=collection_name,
        query=query,
        fields=fields,
        limit=limit
    )

    expected_search_params = {'q': query, 'fl': fields, 'rows': limit}
    mock_client.search.assert_called_once_with(**expected_search_params)
    assert f"Attempting to get documents by query '{query}' from '{collection_name}'" in caplog.text
    assert f"Retrieved 1 documents (total found: 1)" in caplog.text
    
    captured = capsys.readouterr()
    assert captured.err == ""
    output_json = json.loads(captured.out.strip())
    assert output_json == [mock_docs[0]]

def test_get_documents_success_csv_stdout(mock_client, mock_docs, caplog, capsys):
    """Test successful get with CSV output to stdout."""
    caplog.set_level(logging.INFO)
    collection_name = "get_csv_stdout"
    mock_client.search.return_value = MockSolrResults(mock_docs, len(mock_docs))

    get_documents(
        client=mock_client,
        collection_name=collection_name,
        query='*:*',
        output_format='csv'
    )

    captured = capsys.readouterr()
    assert captured.err == ""
    output_lines = captured.out.strip().splitlines()
    assert len(output_lines) == 3
    # Order might vary, check header fields exist and rows match
    assert "id" in output_lines[0]
    assert "field_a" in output_lines[0]
    assert "field_b" in output_lines[0]
    assert "doc1,value1,10" in captured.out
    assert "doc2,value2,20" in captured.out

def test_get_documents_success_json_file(mock_client, mock_docs, caplog):
    """Test successful get with JSON output to file."""
    caplog.set_level(logging.INFO)
    collection_name = "get_json_file"
    output_file = "output.json"
    mock_client.search.return_value = MockSolrResults(mock_docs, len(mock_docs))

    m_open = mock_open()
    with patch("builtins.open", m_open):
        get_documents(
            client=mock_client,
            collection_name=collection_name,
            query='*:*',
            output_path=output_file
        )

    m_open.assert_called_once_with(output_file, "w", newline='')
    handle = m_open()
    written_data = "".join(call.args[0] for call in handle.write.call_args_list)
    assert json.loads(written_data) == mock_docs
    assert f"Output saved to {output_file} in json format" in caplog.text

def test_get_documents_success_csv_file(mock_client, mock_docs, caplog):
    """Test successful get with CSV output to file."""
    caplog.set_level(logging.INFO)
    collection_name = "get_csv_file"
    output_file = "output.csv"
    mock_client.search.return_value = MockSolrResults(mock_docs, len(mock_docs))

    m_open = mock_open()
    with patch("builtins.open", m_open):
        get_documents(
            client=mock_client,
            collection_name=collection_name,
            query='*:*',
            output_path=output_file,
            output_format='csv'
        )

    m_open.assert_called_once_with(output_file, "w", newline='')
    handle = m_open()
    written_content = "".join(call.args[0] for call in handle.write.call_args_list)
    # Basic check, more robust CSV parsing could be added
    assert "id,field_a,field_b" in written_content
    assert "doc1,value1,10" in written_content
    assert "doc2,value2,20" in written_content
    assert f"Output saved to {output_file} in csv format" in caplog.text

def test_get_documents_no_results(mock_client, caplog, capsys):
    """Test get when no documents are found."""
    caplog.set_level(logging.INFO)
    collection_name = "get_no_results"
    mock_client.search.return_value = MockSolrResults([], 0)

    get_documents(client=mock_client, collection_name=collection_name, query='missing:true')

    assert "Retrieved 0 documents (total found: 0)" in caplog.text
    captured = capsys.readouterr()
    assert captured.out.strip() == "[]"  # Should output empty JSON array
    assert captured.err == ""

def test_get_documents_command_failure(mock_client):
    """Test handling failure from SolrClient.search."""
    collection_name = "get_fail"
    error_message = "Invalid query syntax"
    mock_client.search.side_effect = DocumentStoreError(error_message)  # Simulate search error
    
    with pytest.raises(DocumentStoreError, match=error_message):
        get_documents(client=mock_client, collection_name=collection_name, query='bad_query:')

    mock_client.search.assert_called_once()

def test_get_documents_write_error(mock_client, mock_docs):
    """Test handling error when writing output file."""
    collection_name = "get_write_error"
    output_file = "output.json"
    mock_client.search.return_value = MockSolrResults(mock_docs, len(mock_docs))

    m_open = mock_open()
    m_open.side_effect = IOError("Permission denied")
    with patch("builtins.open", m_open):
        with pytest.raises(DocumentStoreError, match="Failed to write output file: Permission denied"):
            get_documents(
                client=mock_client,
                collection_name=collection_name,
                query='*:*',
                output_path=output_file
            )

def test_get_documents_unexpected_exception(mock_client):
    """Test handling unexpected exception during get."""
    collection_name = "get_crash"
    original_exception = ValueError("Unexpected format")
    mock_client.search.side_effect = original_exception

    with pytest.raises(DocumentStoreError, match="An unexpected error occurred: Unexpected format") as exc_info:
        get_documents(client=mock_client, collection_name=collection_name, query='*:*')

    assert isinstance(exc_info.value.__cause__, ValueError)  # Check cause
    mock_client.search.assert_called_once() 