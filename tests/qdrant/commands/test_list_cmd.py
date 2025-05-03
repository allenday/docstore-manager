"""Tests for the Qdrant list collections command function."""

import json
import pytest
import logging
from unittest.mock import MagicMock, patch, mock_open, call
import argparse

from docstore_manager.core.exceptions import CollectionError, CollectionDoesNotExistError, DocumentStoreError
from docstore_manager.qdrant.commands.list import list_collections
from qdrant_client.http.models import CollectionDescription, CollectionsResponse, Distance, VectorParams
from qdrant_client.http.exceptions import UnexpectedResponse
from docstore_manager.qdrant.utils import write_output # Import needed for patching

# Fixture for a mock Qdrant client
@pytest.fixture
def mock_client():
    return MagicMock()

def test_list_collections_success_stdout(mock_client, caplog, capsys):
    """Test successful listing of collections output to stdout."""
    caplog.set_level(logging.INFO) # Ensure INFO messages are captured
    collections_data = [
        CollectionDescription(name="collection1", vectors_config=VectorParams(size=10, distance=Distance.COSINE)),
        CollectionDescription(name="collection2", vectors_config=VectorParams(size=20, distance=Distance.EUCLID)),
    ]
    mock_response = CollectionsResponse(collections=collections_data)
    mock_client.get_collections.return_value = mock_response

    # Pass format explicitly
    list_collections(client=mock_client, output_format='json') 

    # Check stdout for the JSON string (printed by write_output)
    captured = capsys.readouterr()
    expected_output_data = [{"name": "collection1"}, {"name": "collection2"}]
    expected_output_json = json.dumps(expected_output_data, indent=2)
    assert captured.out.strip() == expected_output_json
    # Check log message confirms stdout output
    assert "Collection list output to stdout." in caplog.text

def test_list_collections_success_file_output(mock_client, caplog):
    """Test successful listing of collections written to a JSON file."""
    caplog.set_level(logging.INFO)
    collections_data = [
        CollectionDescription(name="test_coll_1", vectors_config=VectorParams(size=10, distance=Distance.COSINE)),
        CollectionDescription(name="test_coll_2", vectors_config=VectorParams(size=20, distance=Distance.EUCLID)),
    ]
    mock_response = CollectionsResponse(collections=collections_data)
    mock_client.get_collections.return_value = mock_response

    output_path = "collections_output.json"

    # Use mock_open to simulate file writing
    m = mock_open()
    with patch("builtins.open", m):
        # Pass path and format
        list_collections(client=mock_client, output_path=output_path, output_format='json') 

    # Verify open was called correctly 
    m.assert_called_once_with(output_path, 'w') 
    # Verify the file handle's write method was called (content check is complex)
    handle = m()
    handle.write.assert_called()
    # Check the log message
    assert f"Collection list saved to {output_path}" in caplog.text

def test_list_collections_empty(mock_client, caplog, capsys):
    """Test listing when no collections exist."""
    caplog.set_level(logging.INFO)
    mock_response = CollectionsResponse(collections=[])
    mock_client.get_collections.return_value = mock_response

    # Pass format explicitly
    list_collections(client=mock_client, output_format='json')

    # Check stdout for empty JSON array (printed by write_output)
    captured = capsys.readouterr()
    assert captured.out.strip() == "[]" 
    # Check log message confirms stdout output
    assert "Collection list output to stdout." in caplog.text

# --- Test Error Handling ---

def test_list_collections_unexpected_error(mock_client, caplog):
    # Test the generic exception handler
    caplog.set_level(logging.ERROR)
    error_msg = "Something unexpected broke"
    # Set side effect on the correct method
    mock_client.get_collections.side_effect = RuntimeError(error_msg) 

    # Act & Assert
    with pytest.raises(CollectionError) as exc_info:
         # Call with client directly, no args namespace
        list_collections(client=mock_client, output_format='json')

    assert f"Error listing collections: {error_msg}" in caplog.text
    # Check the final CollectionError message raised by the generic handler
    assert str(exc_info.value) == "Failed to list collections." 
    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert str(exc_info.value.__cause__) == error_msg


@patch("builtins.open", new_callable=mock_open)
@patch("docstore_manager.qdrant.commands.list.write_output")
def test_list_collections_file_output_error(mock_write_output, mock_file_open, mock_client, caplog):
    # Arrange
    caplog.set_level(logging.ERROR)
    # Simulate successful collection fetch
    collections_data = [CollectionDescription(name="test1", vectors_config=VectorParams(size=10, distance=Distance.COSINE))]
    mock_response = CollectionsResponse(collections=collections_data)
    mock_client.get_collections.return_value = mock_response
    
    output_file = "error_output.json"
    
    # Simulate write_output raising a DocumentStoreError 
    io_error_msg = "Disk full"
    document_store_error = DocumentStoreError(f"Failed to write output: {io_error_msg}")
    mock_write_output.side_effect = document_store_error

    # Act & Assert - Expect CollectionError because list_collections wraps exceptions
    with pytest.raises(CollectionError) as exc_info: 
        # Pass arguments directly
        list_collections(client=mock_client, output_path=output_file, output_format="json") 

    # Assert that write_output was called correctly before it failed
    mock_write_output.assert_called_once()
    call_args, call_kwargs = mock_write_output.call_args
    assert call_args[0] == [{'name': 'test1'}] # Check structured data passed
    assert call_args[1] == output_file
    # No format in positional args for write_output
    # assert call_kwargs.get('format_type') == 'json' # Not passed to write_output

    # Assert the specific DocumentStoreError is logged *if* write_output logs it (it doesn't currently)
    # Assert the final CollectionError is raised and logged
    assert f"Error listing collections: {document_store_error}" in caplog.text 
    assert str(exc_info.value) == "Failed to list collections." # Check the message from the generic handler
    assert isinstance(exc_info.value.__cause__, DocumentStoreError) # Check the cause
    assert str(exc_info.value.__cause__) == str(document_store_error)

    # ... existing code ... 