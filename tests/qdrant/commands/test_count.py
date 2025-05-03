"""Tests for Qdrant count command."""

import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace
import logging
import json
import sys

# Import QdrantClient and necessary models/exceptions
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from docstore_manager.qdrant.commands.count import count_documents, _parse_filter_json
# Remove unused QdrantCommand import
# from docstore_manager.qdrant.command import QdrantCommand
from docstore_manager.core.exceptions import (
    CollectionError,
    DocumentError,
    InvalidInputError,
    CollectionDoesNotExistError
)

# --- Tests for count_documents ---

@pytest.fixture
def mock_qdrant_client():
    """Fixture for mocked QdrantClient."""
    client = MagicMock(spec=QdrantClient)
    
    # Configure the count method to return a mock CountResult by default
    mock_count_result = MagicMock(spec=models.CountResult)
    mock_count_result.count = 0 # Default count
    client.count.return_value = mock_count_result
    
    return client

# Remove unused mock_command fixture
# @pytest.fixture
# def mock_command():
#     """Fixture for mocked QdrantCommand."""
#     return MagicMock(spec=QdrantCommand)

@pytest.fixture
def mock_args():
    """Fixture for mocked command line arguments."""
    # Use a more realistic structure for args passed to the command function
    return Namespace(
        collection="count_collection",
        query=None # This represents the --query arg from CLI
    )

# Update tests to use mock_qdrant_client
def test_count_documents_success_no_query(mock_qdrant_client, mock_args, caplog, capsys):
    """Test successful count with no query."""
    caplog.set_level(logging.INFO)
    collection_name = mock_args.collection
    
    # Configure the mock client's count method response
    mock_count_result = MagicMock(spec=models.CountResult)
    mock_count_result.count = 123
    mock_qdrant_client.count.return_value = mock_count_result

    # Pass the client and relevant args directly
    count_documents(
        client=mock_qdrant_client, 
        collection_name=collection_name,
        query_filter_json=mock_args.query # Pass the JSON string directly
    )

    # Assert the client method was called correctly
    mock_qdrant_client.count.assert_called_once_with(
        collection_name=collection_name, 
        count_filter=None, 
        exact=True
    )
    assert f"Counting documents in collection '{collection_name}'" in caplog.text
    assert f"Found 123 documents matching criteria in '{collection_name}'." in caplog.text
    
    captured = capsys.readouterr()
    assert captured.err == ""
    output_json = json.loads(captured.out.strip())
    # The output format is now handled within the command function
    assert output_json == {"collection": collection_name, "count": 123}


def test_count_documents_success_with_query(mock_qdrant_client, mock_args, caplog, capsys):
    """Test successful count with a valid query."""
    caplog.set_level(logging.INFO)
    collection_name = mock_args.collection
    query_json = '{"must": [{"key": "field", "match": {"value": "test"}}]}' # Correct structure for Filter
    mock_args.query = query_json # Set the query string on args
    
    # Configure the mock client's count method response
    mock_count_result = MagicMock(spec=models.CountResult)
    mock_count_result.count = 45
    mock_qdrant_client.count.return_value = mock_count_result
    
    # Manually parse the filter like the command would
    expected_filter = _parse_filter_json(query_json)

    count_documents(
        client=mock_qdrant_client, 
        collection_name=collection_name,
        query_filter_json=mock_args.query
    )

    # Assert the client method was called correctly with the parsed filter
    mock_qdrant_client.count.assert_called_once_with(
        collection_name=collection_name, 
        count_filter=expected_filter, # Check if the parsed filter is passed
        exact=True
    )
    assert f"Counting documents in collection '{collection_name}' with filter: {query_json}" in caplog.text
    assert f"Found 45 documents matching criteria in '{collection_name}'." in caplog.text
    
    captured = capsys.readouterr()
    assert captured.err == ""
    output_json = json.loads(captured.out.strip())
    assert output_json == {"collection": collection_name, "count": 45}


# Test collection not found (404 error from client)
def test_count_collection_not_found(mock_qdrant_client, mock_args, caplog, capsys):
    """Test handling CollectionDoesNotExistError (404)."""
    caplog.set_level(logging.ERROR)
    collection_name = "non_existent_collection"
    
    # Simulate 404 error from client.count
    mock_qdrant_client.count.side_effect = UnexpectedResponse(
        status_code=404, 
        reason_phrase="Not Found",
        content=b"Collection not found", 
        headers={'content-type': 'text/plain'}
    )

    with pytest.raises(CollectionDoesNotExistError) as exc_info:
        count_documents(
            client=mock_qdrant_client, 
            collection_name=collection_name,
            query_filter_json=None
        )

    assert exc_info.match(f"Collection '{collection_name}' not found for count.")
    assert f"Collection '{collection_name}' not found for count." in caplog.text
    captured = capsys.readouterr()
    assert f"ERROR: Collection '{collection_name}' not found for count." in captured.err
    mock_qdrant_client.count.assert_called_once_with(
        collection_name=collection_name, 
        count_filter=None, 
        exact=True
    )


# Test other API errors (e.g., 500)
def test_count_api_error(mock_qdrant_client, mock_args, caplog, capsys):
    """Test handling generic API errors (non-404)."""
    caplog.set_level(logging.ERROR)
    collection_name = mock_args.collection

    # Simulate 500 error
    mock_qdrant_client.count.side_effect = UnexpectedResponse(
        status_code=500, 
        reason_phrase="Internal Server Error",
        content=b"DB connection failed", 
        headers={'content-type': 'text/plain'}
    )

    with pytest.raises(DocumentError) as exc_info:
        count_documents(
            client=mock_qdrant_client, 
            collection_name=collection_name,
            query_filter_json=None
        )

    expected_error_msg = f"API error counting documents in '{collection_name}': 500 - Internal Server Error - DB connection failed"
    assert exc_info.match("API error during count")
    assert expected_error_msg in caplog.text
    captured = capsys.readouterr()
    assert f"ERROR: {expected_error_msg}" in captured.err
    mock_qdrant_client.count.assert_called_once_with(
        collection_name=collection_name, 
        count_filter=None, 
        exact=True
    )


# Test invalid JSON in query filter
def test_count_invalid_query_json(mock_qdrant_client, mock_args, caplog, capsys):
    """Test count attempt with invalid query JSON."""
    caplog.set_level(logging.ERROR)
    collection_name = mock_args.collection
    invalid_json = '{"filter": }' # Invalid JSON syntax
    mock_args.query = invalid_json
    
    # Expect sys.exit(1) due to invalid input handling within the command
    # The InvalidInputError is caught internally, so we only expect SystemExit
    with pytest.raises(SystemExit) as sys_exit_info:
        count_documents(
            client=mock_qdrant_client, 
            collection_name=collection_name,
            query_filter_json=invalid_json
        )
            
    # Check the exit code
    assert sys_exit_info.value.code == 1 
    
    # Verify logs and stderr messages
    assert f"Invalid filter provided for count in '{collection_name}'" in caplog.text
    captured = capsys.readouterr()
    assert "ERROR: Invalid filter" in captured.err
    mock_qdrant_client.count.assert_not_called() # Client shouldn't be called if JSON is invalid


# Test invalid filter structure (valid JSON, but wrong Qdrant filter structure)
def test_count_invalid_filter_structure(mock_qdrant_client, mock_args, caplog, capsys):
    """Test count with valid JSON but invalid Qdrant filter structure."""
    caplog.set_level(logging.ERROR)
    collection_name = mock_args.collection
    # Valid JSON, but not a valid Qdrant filter structure
    invalid_filter_json = '{"wrong_key": "some_value"}' 
    mock_args.query = invalid_filter_json
    
    # Expect sys.exit(1) due to invalid input handling within the command
    # The InvalidInputError is caught internally, so we only expect SystemExit
    with pytest.raises(SystemExit) as sys_exit_info:
        count_documents(
            client=mock_qdrant_client, 
            collection_name=collection_name,
            query_filter_json=invalid_filter_json
        )

    # Check the exit code
    assert sys_exit_info.value.code == 1 

    # Verify logs and stderr messages
    assert f"Invalid filter provided for count in '{collection_name}'" in caplog.text
    captured = capsys.readouterr()
    assert "ERROR: Invalid filter" in captured.err
    mock_qdrant_client.count.assert_not_called() # Client shouldn't be called


# Test unexpected exceptions during client call
def test_count_unexpected_exception(mock_qdrant_client, mock_args, caplog, capsys):
    """Test handling unexpected exception during count call."""
    caplog.set_level(logging.ERROR)
    collection_name = mock_args.collection
    
    # Simulate a non-API, non-Input error from the client call
    mock_qdrant_client.count.side_effect = TimeoutError("Qdrant timed out")

    with pytest.raises(DocumentError) as exc_info:
        count_documents(
            client=mock_qdrant_client, 
            collection_name=collection_name,
            query_filter_json=None
        )

    assert exc_info.match(f"Unexpected error counting documents: Qdrant timed out")
    assert f"Unexpected error counting documents in '{collection_name}': Qdrant timed out" in caplog.text
    captured = capsys.readouterr()
    assert "ERROR: An unexpected error occurred during count: Qdrant timed out" in captured.err
    mock_qdrant_client.count.assert_called_once_with(
        collection_name=collection_name, 
        count_filter=None, 
        exact=True
    )

# Remove obsolete tests that were mocking the command layer
# def test_count_missing_collection(mock_command, mock_args):
#     ...
# def test_count_command_failure(mock_command, mock_args):
#     ...

# Helper function test (if needed, usually tested implicitly)
# def test_parse_filter_json_valid():
#     ...
# def test_parse_filter_json_invalid_json():
#     ...
# def test_parse_filter_json_invalid_structure():
#     ... 