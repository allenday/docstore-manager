"""Tests for Qdrant utility functions."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from qdrant_client.http import models

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
    file_path = tmp_path / "docs.json"
    with open(file_path, "w") as f:
        json.dump(docs, f)
    
    result = load_documents(file_path=file_path)
    assert result == docs

def test_load_documents_from_string():
    """Test loading documents from a string."""
    docs = [
        {"id": "1", "text": "test1"},
        {"id": "2", "text": "test2"}
    ]
    docs_str = json.dumps(docs)
    
    result = load_documents(docs_str=docs_str)
    assert result == docs

def test_load_documents_single_doc():
    """Test loading a single document."""
    doc = {"id": "1", "text": "test"}
    docs_str = json.dumps(doc)
    
    result = load_documents(docs_str=docs_str)
    assert result == [doc]

def test_load_documents_invalid():
    """Test loading documents with invalid input."""
    with pytest.raises(ValueError) as exc_info:
        load_documents(file_path=Path("nonexistent.json"))
    assert "Failed to load documents" in str(exc_info.value)
    
    with pytest.raises(ValueError) as exc_info:
        load_documents(docs_str="invalid json")
    assert "Failed to load documents" in str(exc_info.value)
    
    with pytest.raises(ValueError):
        load_documents()  # No input specified
    
    with pytest.raises(ValueError):
        load_documents(file_path=Path("test.json"), docs_str="test")  # Both inputs specified

def test_load_ids_from_file(tmp_path):
    """Test loading IDs from a file."""
    ids = ["1", "2", "3"]
    file_path = tmp_path / "ids.txt"
    with open(file_path, "w") as f:
        f.write("\n".join(ids))
    
    result = load_ids(file_path=file_path)
    assert result == ids

def test_load_ids_from_string():
    """Test loading IDs from a string."""
    ids_str = "1,2,3"
    result = load_ids(ids_str=ids_str)
    assert result == ["1", "2", "3"]

def test_load_ids_with_whitespace():
    """Test loading IDs with whitespace."""
    ids_str = " 1 , 2 , 3 "
    result = load_ids(ids_str=ids_str)
    assert result == ["1", "2", "3"]

def test_load_ids_invalid():
    """Test loading IDs with invalid input."""
    with pytest.raises(ValueError) as exc_info:
        load_ids(file_path=Path("nonexistent.txt"))
    assert "Failed to load IDs" in str(exc_info.value)
    
    with pytest.raises(ValueError):
        load_ids()  # No input specified
    
    with pytest.raises(ValueError):
        load_ids(file_path=Path("test.txt"), ids_str="test")  # Both inputs specified

def test_write_output_to_file(tmp_path):
    """Test writing output to a file."""
    data = {"test": "value"}
    output_path = tmp_path / "output.json"
    
    write_output(data, str(output_path))
    
    with open(output_path) as f:
        result = json.load(f)
    assert result == data

def test_write_output_to_stdout():
    """Test writing output to stdout."""
    data = {"test": "value"}
    
    with patch("builtins.print") as mock_print:
        write_output(data)
        mock_print.assert_called_once_with(json.dumps(data, indent=2))

def test_write_output_invalid_format():
    """Test writing output with invalid format."""
    with pytest.raises(ValueError) as exc_info:
        write_output({}, format="invalid")
    assert "Unsupported output format" in str(exc_info.value)

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
    assert "Invalid distance function" in str(exc_info.value)

def test_format_collection_info():
    """Test formatting collection information."""
    mock_info = Mock()
    mock_info.name = "test"
    mock_info.config.params.vectors.size = 128
    mock_info.config.params.vectors.distance = models.Distance.COSINE
    mock_info.points_count = 100
    mock_info.config.params.on_disk_payload = False
    
    result = format_collection_info(mock_info)
    
    assert result["name"] == "test"
    assert result["vectors"]["size"] == 128
    assert result["vectors"]["distance"] == models.Distance.COSINE
    assert result["points_count"] == 100
    assert result["on_disk_payload"] is False 