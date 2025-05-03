"""Tests for Qdrant scroll command."""

import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace
import logging
import json

# Import the actual function being tested
from docstore_manager.qdrant.commands.scroll import scroll_documents
# Import QdrantClient for mocking
from qdrant_client import QdrantClient
# Import necessary exceptions and models
from docstore_manager.core.exceptions import (
    CollectionError,
    DocumentError,
    InvalidInputError,
    CollectionDoesNotExistError
)
from qdrant_client.http import models as rest
from qdrant_client.http.exceptions import UnexpectedResponse

# --- Tests for scroll_documents ---

@pytest.fixture
def mock_client(): # Renamed from mock_command
    """Fixture for mocked QdrantClient."""
    # Mock QdrantClient directly
    mock = MagicMock(spec=QdrantClient)
    # Ensure the scroll method exists on the mock
    mock.scroll = MagicMock()
    return mock

@pytest.fixture
def mock_args():
    """Fixture for mocked command line arguments (less relevant now)."""
    # Keep args simple, as most logic is now in scroll_documents parameters
    return Namespace(
        collection='scroll_collection',
        filter=None, # Using scroll_filter_json parameter now
        limit=10,
        offset=None,
        output_format='json',
        with_vectors=False,
        # Removed args less relevant to direct function call
        # query=None,
        # batch_size=10, # Replaced by limit
        # with_payload=True # Implicit in scroll
    )

@pytest.fixture
def mock_scroll_data():
    """Fixture for mock scroll response points."""
    # Use PointStruct as returned by client.scroll
    return [
        rest.PointStruct(id="s1", vector=[0.1], payload={"field": "val1"}),
        rest.PointStruct(id="s2", vector=[0.2], payload={"field": "val2"})
    ]

@pytest.fixture
def mock_scroll_result(mock_scroll_data):
    """Fixture for the tuple returned by client.scroll."""
    return (mock_scroll_data, "next_offset_123") # points, next_page_offset

def test_scroll_success_defaults(mock_client, mock_args, mock_scroll_result, mock_scroll_data, caplog, capsys): # Added mock_scroll_result
    """Test successful scroll with default arguments."""
    caplog.set_level(logging.INFO)
    # Set the return value for the mock client's scroll method
    mock_client.scroll.return_value = mock_scroll_result

    # Call the function directly with parameters derived from args
    scroll_documents(
        client=mock_client,
        collection_name=mock_args.collection,
        limit=mock_args.limit, # Use limit from args
        # Other params use defaults
    )

    # Assert the mock client's scroll method was called correctly
    mock_client.scroll.assert_called_once_with(
        collection_name="scroll_collection",
        limit=10,
        offset=None,
        with_payload=True, # Default in scroll_documents
        with_vectors=False, # Default in scroll_documents
        scroll_filter=None # Default in scroll_documents
    )
    # Check logs
    assert f"Scrolling documents in collection '{mock_args.collection}' (limit=10, offset=None)" in caplog.text
    assert f"Successfully scrolled {len(mock_scroll_data)} documents" in caplog.text
    assert f"Next page offset: {mock_scroll_result[1]}" in caplog.text
    # Check stdout log (where formatted output goes)
    # Reformat expected output based on QdrantFormatter
    expected_output_dict = [{"id": p.id, "payload": p.payload} for p in mock_scroll_data]
    assert json.dumps(expected_output_dict, indent=2) in caplog.text

def test_scroll_success_with_args(mock_client, mock_args, mock_scroll_result, caplog, capsys): # Added mock_scroll_result
    """Test successful scroll with specific arguments."""
    caplog.set_level(logging.INFO)
    filter_dict = {"must": [{"key": "field", "match": {"value": "val1"}}]}
    scroll_filter_json = json.dumps(filter_dict)
    limit = 5
    offset = "start_id_abc"
    with_vectors = True
    output_format = "yaml" # Test different format

    # Modify mock result if necessary (e.g., filter applied)
    # For simplicity, assume the mock result still applies
    mock_client.scroll.return_value = mock_scroll_result
    points, next_offset = mock_scroll_result

    scroll_documents(
        client=mock_client,
        collection_name=mock_args.collection,
        scroll_filter=scroll_filter_json,
        limit=limit,
        offset=offset,
        with_vectors=with_vectors,
        output_format=output_format
    )

    # Assert mock call with updated args
    mock_client.scroll.assert_called_once_with(
        collection_name="scroll_collection",
        limit=limit,
        offset=offset,
        with_payload=True, # Still True internally
        with_vectors=with_vectors,
        # Use QdrantClient's Filter model for assertion
        scroll_filter=rest.Filter(**filter_dict)
    )

    # Check logs
    assert f"Scrolling documents in collection '{mock_args.collection}' (limit={limit}, offset={offset})" in caplog.text
    assert f"Applying scroll filter: {scroll_filter_json}" in caplog.text
    assert f"Successfully scrolled {len(points)} documents" in caplog.text
    assert f"Next page offset: {next_offset}" in caplog.text
    # Check YAML output in logs (simplified check)
    assert "id: s1" in caplog.text
    assert "payload:" in caplog.text
    assert "vector:" in caplog.text # Since with_vectors=True

# Removed test_scroll_missing_collection - Function doesn't take args directly anymore
# Removed test_scroll_invalid_filter_json - Parsing happens inside scroll_documents

def test_scroll_invalid_filter_json_inside_function(mock_client, mock_args, caplog):
    """Test scroll attempt with invalid filter JSON, caught inside function."""
    caplog.set_level(logging.ERROR)
    invalid_filter_json = '{"must": }' # Invalid JSON

    with pytest.raises(SystemExit): # Exits on invalid filter parse
        scroll_documents(
            client=mock_client,
            collection_name=mock_args.collection,
            scroll_filter=invalid_filter_json
        )

    mock_client.scroll.assert_not_called()
    assert "Invalid scroll filter JSON" in caplog.text

def test_scroll_collection_not_found(mock_client, mock_args, caplog):
    """Test handling 404 error from client.scroll."""
    caplog.set_level(logging.ERROR)
    collection_name = "non_existent_collection"
    # Simulate QdrantClient raising UnexpectedResponse for 404
    mock_client.scroll.side_effect = UnexpectedResponse(
        status_code=404, reason_phrase="Not Found", content=b"Collection not found", headers={}
    )

    with pytest.raises(CollectionDoesNotExistError) as exc_info:
        scroll_documents(client=mock_client, collection_name=collection_name)

    assert f"Collection '{collection_name}' not found" in str(exc_info.value)
    assert f"Collection '{collection_name}' not found" in caplog.text
    mock_client.scroll.assert_called_once_with(
        collection_name=collection_name,
        limit=10, offset=None, with_payload=True, with_vectors=False, scroll_filter=None
    )


def test_scroll_api_error(mock_client, mock_args, caplog):
    """Test handling general API error from client.scroll."""
    caplog.set_level(logging.ERROR)
    collection_name = "api_error_collection"
    # Simulate QdrantClient raising UnexpectedResponse for 500
    error_content = b"Internal Server Error Details"
    mock_client.scroll.side_effect = UnexpectedResponse(
        status_code=500, reason_phrase="Internal Server Error", content=error_content, headers={}
    )

    with pytest.raises(DocumentError) as exc_info:
        scroll_documents(client=mock_client, collection_name=collection_name)

    assert "API error during scroll" in str(exc_info.value)
    assert f"API error scrolling documents in '{collection_name}': 500 - Internal Server Error - {error_content.decode()}" in caplog.text
    mock_client.scroll.assert_called_once_with(
        collection_name=collection_name,
        limit=10, offset=None, with_payload=True, with_vectors=False, scroll_filter=None
    )


def test_scroll_unexpected_exception(mock_client, mock_args, caplog):
    """Test handling unexpected exception during scroll."""
    caplog.set_level(logging.ERROR)
    collection_name = "unexpected_error_collection"
    error_message = "Something went wrong"
    mock_client.scroll.side_effect = TimeoutError(error_message) # Example unexpected error

    with pytest.raises(DocumentError) as exc_info:
        scroll_documents(client=mock_client, collection_name=collection_name)

    assert f"Unexpected error scrolling documents: {error_message}" in str(exc_info.value)
    assert f"Unexpected error scrolling documents in '{collection_name}': {error_message}" in caplog.text
    mock_client.scroll.assert_called_once_with(
        collection_name=collection_name,
        limit=10, offset=None, with_payload=True, with_vectors=False, scroll_filter=None
    )


def test_scroll_no_results(mock_client, mock_args, caplog, capsys):
    """Test scroll when no documents are found."""
    caplog.set_level(logging.INFO)
    collection_name = "empty_collection"
    # Simulate client returning empty list and no next offset
    mock_client.scroll.return_value = ([], None)

    scroll_documents(client=mock_client, collection_name=collection_name)

    mock_client.scroll.assert_called_once_with(
        collection_name=collection_name,
        limit=10, offset=None, with_payload=True, with_vectors=False, scroll_filter=None
    )
    assert "No documents found matching the scroll criteria." in caplog.text
    # Check that empty list is logged as info
    assert "[]" in caplog.text


# --- Removing old tests that used QdrantCommand structure ---
# test_scroll_documents_success_no_filter
# test_scroll_documents_success_with_filter
# test_scroll_command_failure (replaced by API/Not Found tests)

# test_scroll_success_defaults
# test_scroll_success_with_args
# test_scroll_missing_collection
# test_scroll_invalid_filter_json
# test_scroll_command_failure
# test_scroll_unexpected_exception
# test_scroll_documents_success_no_filter
# test_scroll_documents_success_with_filter
