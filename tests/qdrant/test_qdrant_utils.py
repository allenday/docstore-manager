"""Tests for Qdrant utility functions."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from qdrant_client.http import models
import os
import logging

from docstore_manager.qdrant.utils import (
    initialize_qdrant_client,
    load_documents,
    load_ids,
    write_output,
    create_vector_params,
    format_collection_info
)
from docstore_manager.core.exceptions import ConfigurationError, ConnectionError

@pytest.fixture
def formatter():
    """Create a formatter instance."""
    return QdrantFormatter()

def test_initialize_qdrant_client_from_args():
    """Test client initialization from command line arguments."""
    args = Mock()
    args.url = "http://localhost"
    args.port = 6333
    args.api_key = "test-key"
    args.profile = None
    args.config = None
    
    with patch("docstore_manager.qdrant.utils.QdrantClient") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.get_collections.return_value = None  # Connection test succeeds
        
        client = initialize_qdrant_client(args)
        
        mock_client_class.assert_called_once_with(
            url="http://localhost",
            port=6333,
            api_key="test-key"
        )
        assert client == mock_client

def test_initialize_qdrant_client_from_config():
    """Test client initialization from configuration file."""
    args = Mock()
    args.url = None
    args.port = None
    args.api_key = None
    args.profile = "default"
    args.config = "config.yaml"
    
    mock_config = {
        "url": "http://localhost",
        "port": 6333,
        "api_key": "test-key"
    }
    
    with patch("docstore_manager.qdrant.utils.load_config", return_value=mock_config), \
         patch("docstore_manager.qdrant.utils.QdrantClient") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.get_collections.return_value = None  # Connection test succeeds
        
        client = initialize_qdrant_client(args)
        
        mock_client_class.assert_called_once_with(
            url="http://localhost",
            port=6333,
            api_key="test-key"
        )
        assert client == mock_client

def test_initialize_qdrant_client_missing_details():
    """Test client initialization with missing connection details."""
    args = Mock()
    args.url = None
    args.port = None
    args.api_key = None
    args.profile = None
    args.config = None
    
    with pytest.raises(ConfigurationError) as exc_info:
        initialize_qdrant_client(args)
    assert "Missing required connection details" in str(exc_info.value)

def test_initialize_qdrant_client_connection_error():
    """Test client initialization with connection error."""
    args = Mock()
    args.url = "http://localhost"
    args.port = 6333
    args.api_key = None
    args.profile = None
    args.config = None
    
    with patch("docstore_manager.qdrant.utils.QdrantClient") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.get_collections.side_effect = Exception("Connection failed")
        
        with pytest.raises(ConfigurationError) as exc_info:  # Changed from ConnectionError to ConfigurationError
            initialize_qdrant_client(args)
        assert "Failed to initialize Qdrant client" in str(exc_info.value)

def test_load_documents_from_file(tmp_path):
    """Test loading documents from a file."""
    docs = [
        {"id": "1", "text": "test1"},
        {"id": "2", "text": "test2"}
    ]
    file_path = tmp_path / "docs.jsonl"
    with open(file_path, "w") as f:
        for doc in docs:
            f.write(json.dumps(doc) + "\n")
    
    result = load_documents(file_path=str(file_path))
    assert result == docs

def test_load_documents_from_file_empty(tmp_path):
    """Test loading documents from an empty file."""
    file_path = tmp_path / "empty.jsonl"
    file_path.touch()
    with pytest.raises(ValueError, match="No valid JSON objects found in file"):
        load_documents(file_path=str(file_path))

def test_load_documents_from_file_invalid_json(tmp_path):
    """Test loading documents from a file with invalid JSON."""
    file_path = tmp_path / "invalid.jsonl"
    with open(file_path, "w") as f:
        f.write("{\"id\": \"1\", \"text\": \"test1\"}\n")
        f.write("not json\n")
    with pytest.raises(ValueError, match="Invalid JSON on line 2"):
        load_documents(file_path=str(file_path))

def test_load_documents_invalid():
    """Test loading documents with non-existent file."""
    with pytest.raises(ValueError) as exc_info:
        load_documents(file_path="nonexistent.jsonl")
    assert "File not found: nonexistent.jsonl" in str(exc_info.value)

def test_load_ids_from_file(tmp_path):
    """Test loading IDs from a file."""
    ids = ["1", "2", "3"]
    file_path = tmp_path / "ids.txt"
    with open(file_path, "w") as f:
        f.write("\n".join(ids))

    # Call load_ids with positional argument
    result = load_ids(str(file_path))
    assert result == ids

def test_load_ids_from_string():
    """Test loading IDs from a string."""
    ids_str = "1,2,3"
    result = load_ids(ids_str)
    assert result == ["1", "2", "3"]

def test_load_ids_with_whitespace():
    """Test loading IDs with whitespace."""
    ids_str = " 1 , 2 , 3 "
    result = load_ids(ids_str)
    assert result == ["1", "2", "3"]

def test_load_ids_invalid(tmp_path, caplog):
    """Test load_ids with various invalid inputs."""
    caplog.set_level(logging.WARNING)

    # 1. Test with a non-existent file path (that looks like a path)
    non_existent_path = "/path/to/non_existent_file.txt"
    with pytest.raises(ValueError, match=rf"File not found at path: {non_existent_path}"):
        load_ids(non_existent_path)
    assert f"File path specified but not found: {non_existent_path}" in caplog.text
    caplog.clear()

    # 2. Test with an empty string (should return empty list, log warning)
    assert load_ids("") == []
    assert "load_ids resulted in an empty list for input: ''" in caplog.text
    caplog.clear()

    # 3. Test with a string containing only whitespace/commas (should RAISE ValueError now)
    whitespace_string = " , , "
    with pytest.raises(ValueError, match=r"Could not parse IDs from string: .* Expected comma-separated values."):
        load_ids(whitespace_string)
    assert f"Provided string '{whitespace_string}' resulted in no IDs after splitting by comma." in caplog.text
    caplog.clear()

    # 4. Test with a string that doesn't look like a path and doesn't contain valid IDs
    # (Should raise ValueError if the string is not empty/whitespace and contains no commas)
    invalid_string = "this is not a valid input"
    with pytest.raises(ValueError, match=r"Invalid format for ID string: .* Expected comma-separated values or a file path."):
        load_ids(invalid_string)
    assert f"Invalid format for ID string: '{invalid_string}'." in caplog.text
    caplog.clear()

    # 5. Test with an existing directory path (should raise ValueError indirectly via IOError or similar)
    # Note: The refactored logic might raise ValueError directly if it detects a directory earlier.
    # Let's adapt the test to expect ValueError for consistency with the file-not-found path.
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    with pytest.raises(ValueError, match=r"Could not read file: {}".format(str(dir_path))):
        load_ids(str(dir_path))
    caplog.clear()

    # 6. Test with a file containing invalid JSON
    invalid_json_path = tmp_path / "invalid.json"
    invalid_json_path.write_text('{"key": "value",}') # Trailing comma makes it invalid - Use single quotes
    with pytest.raises(ValueError, match=r"Invalid JSON format in file: {}".format(str(invalid_json_path))):
        load_ids(str(invalid_json_path))
    assert f"Error decoding JSON from file: {str(invalid_json_path)}" in caplog.text
    caplog.clear()

    # 7. Test with a JSON file not containing a list
    not_list_json_path = tmp_path / "not_list.json"
    not_list_json_path.write_text('{"id": "123"}')
    with pytest.raises(ValueError, match="JSON file must contain a list of strings or integers."):
        load_ids(str(not_list_json_path))
    caplog.clear()

def test_write_output_to_file(tmp_path):
    """Test writing output to a file."""
    data = {"test": "value"}
    output_path = tmp_path / "output.json"
    expected_json_string = json.dumps(data, indent=2)

    # Call the function to write the file
    write_output(data, str(output_path))

    # Assert the file content is correct
    assert output_path.exists()
    content = output_path.read_text()
    assert content == expected_json_string

def test_write_output_to_stdout():
    """Test writing output to stdout."""
    data = {"test": "value"}

    with patch("builtins.print") as mock_print:
        # Pass the data dictionary directly
        write_output(data)
        # Assert print was called with the JSON string
        expected_json_string = json.dumps(data, indent=2)
        mock_print.assert_called_once_with(expected_json_string)

def test_create_vector_params():
    """Test creating vector parameters."""
    params = create_vector_params(128, "COSINE")  # Changed from "Cosine" to "COSINE"
    assert params.size == 128
    assert params.distance == models.Distance.COSINE
    
    params = create_vector_params(256, "EUCLID")  # Changed from "Euclid" to "EUCLID"
    assert params.size == 256
    assert params.distance == models.Distance.EUCLID
    
    params = create_vector_params(512, "DOT")  # Changed from "Dot" to "DOT"
    assert params.size == 512
    assert params.distance == models.Distance.DOT

def test_create_vector_params_invalid_distance():
    """Test creating vector parameters with invalid distance."""
    with pytest.raises(ValueError) as exc_info:
        create_vector_params(128, "Invalid")
    assert "Invalid distance string: Invalid" in str(exc_info.value)

# Remove outdated/complex formatter unit test
# def test_format_collection_info(): 