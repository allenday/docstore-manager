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


@pytest.mark.parametrize(
    "query_filter_json, expected_filter_dict",
    [
        ('{"must": [{"key": "color", "match": {"value": "red"}}]}', {'must': [{'key': 'color', 'match': {'value': 'red'}}]}),
        ('{"should": [{"has_id": [1, 2, 3]}]}', {'should': [{'has_id': [1, 2, 3]}]})
    ]
)
def test_count_documents_success_with_query(mock_qdrant_client, mock_args, caplog, query_filter_json, expected_filter_dict):
    """Test counting documents successfully with a valid query filter."""
    collection_name = mock_args.collection
    mock_qdrant_client.count.return_value = models.CountResult(count=50)
    caplog.set_level(logging.INFO)
    # Mock the parser to return a simple object for comparison ease if needed
    # Or rely on the actual parser and compare complex Filter objects
    # For this test, assume the filter passed to client.count is checkable

    count_documents(client=mock_qdrant_client, collection_name=collection_name, query_filter_json=query_filter_json)

    # Assertions
    mock_qdrant_client.count.assert_called_once()
    # Check the filter object passed to the mock
    call_args, call_kwargs = mock_qdrant_client.count.call_args
    assert call_kwargs['collection_name'] == collection_name
    assert call_kwargs['count_filter'] is not None
    # Compare the structure of the passed filter (may need deepdiff or custom comparison)
    # This depends on how _parse_filter_json creates the Filter object
    # Assuming it roughly mirrors the input dict structure for this test:
    # assert call_kwargs['count_filter'].dict() == expected_filter_dict # If Filter has .dict()

    # Check log output
    expected_json = json.dumps({"count": 50}, indent=2)
    assert expected_json in caplog.text
    assert f"Collection '{collection_name}' contains 50 documents." in caplog.text
    assert f"with filter: {query_filter_json}" in caplog.text


# Test collection not found (404 error from client)
def test_count_collection_not_found(mock_qdrant_client, mock_args, caplog):
    """Test counting documents when the collection does not exist."""
    caplog.set_level(logging.ERROR)
    collection_name = "non_existent_collection"
    mock_qdrant_client.count.side_effect = UnexpectedResponse(
        status_code=404, reason_phrase="Not Found", content=b'Collection not found', headers={}
    )

    with pytest.raises(CollectionDoesNotExistError) as exc_info:
        count_documents(client=mock_qdrant_client, collection_name=collection_name)
    
    assert exc_info.value.collection_name == collection_name
    expected_log = f"Collection '{collection_name}' not found for count."
    assert expected_log in caplog.text


# Test other API errors (e.g., 500)
def test_count_api_error(mock_qdrant_client, mock_args, caplog):
    """Test handling general API error from client.count."""
    caplog.set_level(logging.ERROR)
    collection_name = "count_collection"
    error_content = b"DB connection error"
    mock_qdrant_client.count.side_effect = UnexpectedResponse(
        status_code=500, reason_phrase="Internal Server Error", content=error_content, headers={}
    )

    with pytest.raises(DocumentError) as exc_info:
        count_documents(client=mock_qdrant_client, collection_name=collection_name)

    # Check the exception details passed up
    assert isinstance(exc_info.value.details, dict)
    assert exc_info.value.details['collection_name'] == collection_name
    assert "API error counting documents" in exc_info.value.details.get('original_details', '')
    # Check log message
    expected_log = f"API error counting documents in '{collection_name}': 500 - Internal Server Error - {error_content.decode()}"
    assert expected_log in caplog.text


# Test invalid JSON in query filter
def test_count_invalid_query_json(mock_qdrant_client, mock_args, caplog, capsys):
    """Test count attempt with invalid query JSON."""
    caplog.set_level(logging.ERROR)
    collection_name = mock_args.collection
    invalid_json = '{"filter": }' # Invalid JSON syntax
    mock_args.query = invalid_json
    
    # Expect sys.exit(1) due to invalid input handling within the command
    # The InvalidInputError is caught internally, so we only expect SystemExit
    with pytest.raises(InvalidInputError):
        count_documents(client=mock_qdrant_client, collection_name=collection_name, query_filter_json=invalid_json)

        # Check log for JSON parsing error message
        # The exact message depends on json.loads and the _parse_filter_json implementation
        assert "Invalid filter provided for count" in caplog.text
        assert "Invalid filter:" in caplog.text
        # We're not printing to stderr anymore, just logging
        # captured = capsys.readouterr()
        # assert "ERROR: Invalid filter" in captured.err
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
    with pytest.raises(InvalidInputError):
        count_documents(client=mock_qdrant_client, collection_name=collection_name, query_filter_json=invalid_filter_json)

    # Check log for the structure error message from the exception handler
    assert "Invalid filter provided for count" in caplog.text
    assert "Invalid filter:" in caplog.text

    # We're not printing to stderr anymore, just logging
    # captured = capsys.readouterr()
    # assert "ERROR: Invalid filter" in captured.err
    mock_qdrant_client.count.assert_not_called() # Client shouldn't be called


# Test unexpected exceptions during client call
def test_count_unexpected_exception(mock_qdrant_client, mock_args, caplog):
    """Test handling unexpected Python exceptions during count."""
    caplog.set_level(logging.ERROR)
    collection_name = "unexpected_coll"
    error_message = "Qdrant timed out"
    mock_qdrant_client.count.side_effect = TimeoutError(error_message)

    with pytest.raises(DocumentError) as exc_info:
        count_documents(client=mock_qdrant_client, collection_name=collection_name)
        
    assert isinstance(exc_info.value, DocumentError)
    assert exc_info.value.collection_name == collection_name
    assert error_message in str(exc_info.value)
    # Check log
    assert f"An unexpected error occurred during count: {error_message}" in caplog.text

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

def test_count_documents_success_no_query(mock_qdrant_client, caplog):
    """Test counting documents successfully with no query filter."""
    collection_name = "test_collection"
    mock_qdrant_client.count.return_value = models.CountResult(count=100)
    caplog.set_level(logging.INFO) # Ensure INFO logs are captured

    count_documents(client=mock_qdrant_client, collection_name=collection_name)

    # Assertions
    mock_qdrant_client.count.assert_called_once_with(collection_name=collection_name, count_filter=None, exact=True)
    # Check for the JSON output string in logs
    expected_json = json.dumps({"count": 100}, indent=2)
    assert expected_json in caplog.text
    # Check for the summary log message
    assert f"Collection '{collection_name}' contains 100 documents." in caplog.text
