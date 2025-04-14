"""Tests for batch operations command."""

import pytest
from unittest.mock import patch, mock_open, MagicMock
from argparse import Namespace
import json

from docstore_manager.qdrant.commands.batch import (
    add_documents,
    delete_documents,
    _load_documents_from_file,
    _load_ids_from_file
)
from docstore_manager.common.exceptions import (
    CollectionError,
    DocumentError,
    FileOperationError,
    FileParseError,
    BatchOperationError
)
from docstore_manager.qdrant.command import QdrantCommand

@pytest.fixture
def mock_command():
    return MagicMock()

@pytest.fixture
def mock_args():
    return Namespace(
        collection="test_collection",
        file=None,
        docs=None,
        ids=None,
        batch_size=100
    )

def test_load_documents_from_file_success():
    """Test successful loading of documents from file."""
    docs = [{"id": 1}, {"id": 2}]
    with patch("builtins.open", mock_open(read_data=json.dumps(docs))):
        result = _load_documents_from_file("docs.json")
    assert result == docs

def test_load_documents_from_file_not_list():
    """Test error when documents file doesn't contain a list."""
    with patch("builtins.open", mock_open(read_data='{"key": "value"}')):
        with pytest.raises(FileParseError) as exc_info:
            _load_documents_from_file("docs.json")
    assert "Documents must be a JSON array" in str(exc_info.value)

def test_load_documents_from_file_not_found():
    """Test error when documents file is not found."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileOperationError) as exc_info:
            _load_documents_from_file("nonexistent.json")
    assert "File not found" in str(exc_info.value)

def test_load_documents_from_file_invalid_json():
    """Test error when documents file contains invalid JSON."""
    with patch("builtins.open", mock_open(read_data='invalid json')):
        with pytest.raises(FileParseError) as exc_info:
            _load_documents_from_file("docs.json")
    assert "Expecting value" in str(exc_info.value)

def test_load_ids_from_file_success():
    """Test successful loading of IDs from file."""
    with patch("builtins.open", mock_open(read_data="id1\nid2\nid3\n")):
        result = _load_ids_from_file("ids.txt")
    assert result == ["id1", "id2", "id3"]

def test_load_ids_from_file_empty():
    """Test error when ID file is empty."""
    with patch("builtins.open", mock_open(read_data="")):
        with pytest.raises(FileOperationError) as exc_info:
            _load_ids_from_file("ids.txt")
    assert "No valid IDs found" in str(exc_info.value)

def test_load_ids_from_file_not_found():
    """Test error when ID file is not found."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileOperationError) as exc_info:
            _load_ids_from_file("nonexistent.txt")
    assert "File not found" in str(exc_info.value)

def test_batch_add_missing_collection(mock_command, mock_args):
    """Test batch add with missing collection name."""
    mock_args.collection = None
    with pytest.raises(CollectionError) as exc_info:
        add_documents(mock_command, mock_args)
    assert "Collection name is required" in str(exc_info.value)

def test_batch_add_no_docs(mock_command, mock_args):
    """Test batch add with no documents provided."""
    with pytest.raises(DocumentError) as exc_info:
        add_documents(mock_command, mock_args)
    assert "Either --file or --docs must be specified" in str(exc_info.value)

def test_batch_add_from_string_success(mock_command, mock_args):
    """Test successful batch add from JSON string."""
    docs = [{"id": 1}, {"id": 2}]
    mock_args.docs = json.dumps(docs)
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.message = "Added 2 documents"
    mock_command.add_documents.return_value = mock_response

    add_documents(mock_command, mock_args)

    mock_command.add_documents.assert_called_once_with(
        collection="test_collection",
        documents=docs,
        batch_size=100
    )

def test_batch_add_from_file_success(mock_command, mock_args):
    """Test successful batch add from file."""
    docs = [{"id": 1}, {"id": 2}]
    mock_args.file = "docs.json"
    mock_args.docs_file = None
    mock_args.docs = None
    
    mock_response = {"success": True, "message": "Added 2 documents", "data": {}}
    mock_command.add_documents.return_value = mock_response

    with patch("builtins.open", mock_open(read_data=json.dumps(docs))):
        add_documents(mock_command, mock_args)

    mock_command.add_documents.assert_called_once_with(
        collection="test_collection",
        documents=docs,
        batch_size=100
    )

def test_batch_add_invalid_json_string(mock_command, mock_args):
    """Test batch add with invalid JSON string."""
    mock_args.docs = "invalid json"
    with pytest.raises(DocumentError) as exc_info:
        add_documents(mock_command, mock_args)
    assert "Invalid JSON in documents string" in str(exc_info.value)

def test_batch_add_failure(mock_command, mock_args):
    """Test handling of batch add failure."""
    docs = [{"id": 1}]
    mock_args.docs = json.dumps(docs)
    mock_response = {"success": False, "error": "Failed to add documents"}
    mock_command.add_documents.return_value = mock_response

    with pytest.raises(BatchOperationError) as exc_info:
        add_documents(mock_command, mock_args)
    
    assert "Failed to add documents" in str(exc_info.value)
    assert exc_info.value.collection == "test_collection"
    assert exc_info.value.operation == "add"

def test_batch_delete_missing_collection(mock_command, mock_args):
    """Test batch delete with missing collection name."""
    mock_args.collection = None
    with pytest.raises(CollectionError) as exc_info:
        delete_documents(mock_command, mock_args)
    assert "Collection name is required" in str(exc_info.value)

def test_batch_delete_no_ids_or_filter(mock_command, mock_args):
    """Test batch delete with no IDs or filter provided."""
    with pytest.raises(DocumentError) as exc_info:
        delete_documents(mock_command, mock_args)
    assert "Either --file, --ids, or --filter must be specified" in str(exc_info.value)

def test_batch_delete_from_string_success(mock_command, mock_args):
    """Test successful batch delete from ID string."""
    mock_args.ids = "id1,id2,id3"
    mock_args.file = None
    mock_args.filter = None

    mock_response = {"success": True, "message": "Deleted 3 documents", "data": {}}
    mock_command.delete_documents.return_value = mock_response

    delete_documents(mock_command, mock_args)

    mock_command.delete_documents.assert_called_once_with(
        collection="test_collection",
        ids=["id1", "id2", "id3"],
        filter=None,
        batch_size=100
    )

def test_batch_delete_from_file_success(mock_command, mock_args):
    """Test successful batch delete from file."""
    mock_args.file = "ids.txt"
    mock_args.ids_file = None
    mock_args.ids = None
    mock_args.filter = None

    mock_response = {"success": True, "message": "Deleted 3 documents", "data": {}}
    mock_command.delete_documents.return_value = mock_response

    with patch("builtins.open", mock_open(read_data="id1\nid2\nid3\n")):
        delete_documents(mock_command, mock_args)

    mock_command.delete_documents.assert_called_once_with(
        collection="test_collection",
        ids=["id1", "id2", "id3"],
        filter=None,
        batch_size=100
    )

def test_batch_delete_with_filter(mock_command, mock_args):
    """Test batch delete with filter."""
    filter_dict = {"field": "value"}
    mock_args.filter = json.dumps(filter_dict)
    mock_args.ids = None
    mock_args.file = None
    
    mock_response = {"success": True, "message": "Deleted documents based on filter", "data": {}}
    mock_command.delete_documents.return_value = mock_response

    delete_documents(mock_command, mock_args)

    mock_command.delete_documents.assert_called_once_with(
        collection="test_collection",
        ids=None,
        filter=filter_dict,
        batch_size=100
    )

def test_batch_delete_failure(mock_command, mock_args):
    """Test handling of batch delete failure."""
    mock_args.ids = "id1,id2"
    mock_args.file = None
    mock_args.filter = None

    mock_response = {"success": False, "error": "Failed to delete documents"}
    mock_command.delete_documents.return_value = mock_response

    with pytest.raises(BatchOperationError) as exc_info:
        delete_documents(mock_command, mock_args)
        
    assert "Failed to delete documents" in str(exc_info.value)
    assert exc_info.value.collection == "test_collection"
    assert exc_info.value.operation == "delete" 