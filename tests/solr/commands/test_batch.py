"""Tests for Solr batch operations command."""

import pytest
from unittest.mock import patch, mock_open, MagicMock
from argparse import Namespace
import json

from docstore_manager.solr.commands.batch import (
    batch_add,
    batch_delete,
    _load_documents_from_file,
    _load_ids_from_file
)
from docstore_manager.common.exceptions import (
    CollectionError,
    DocumentError,
    FileOperationError,
    FileParseError,
    DocumentStoreError
)
from docstore_manager.solr.command import SolrCommand

# --- Tests for Helper Functions ---

def test_load_documents_from_file_success():
    """Test successful loading of documents from file."""
    docs = [{"id": 1}, {"id": 2}]
    with patch("builtins.open", mock_open(read_data=json.dumps(docs))):
        result = _load_documents_from_file("docs.json")
    assert result == docs

def test_load_documents_from_file_invalid_json():
    """Test error when documents file contains invalid JSON."""
    with patch("builtins.open", mock_open(read_data='invalid json')):
        with pytest.raises(FileParseError) as exc_info:
            _load_documents_from_file("docs.json")
    assert "Invalid JSON" in str(exc_info.value)

def test_load_documents_from_file_io_error():
    """Test error when documents file cannot be read."""
    with patch("builtins.open", side_effect=IOError("Read failed")):
        with pytest.raises(FileOperationError) as exc_info:
            _load_documents_from_file("unreadable.json")
    assert "Error reading documents file" in str(exc_info.value)

def test_load_ids_from_file_success():
    """Test successful loading of IDs from file."""
    with patch("builtins.open", mock_open(read_data="id1\nid2\n  \nid3\n")):
        result = _load_ids_from_file("ids.txt")
    assert result == ["id1", "id2", "id3"]

def test_load_ids_from_file_empty():
    """Test loading an empty ID file."""
    with patch("builtins.open", mock_open(read_data="")):
        result = _load_ids_from_file("ids.txt")
    assert result == [] # Should return empty list, not raise error

def test_load_ids_from_file_io_error():
    """Test error when ID file cannot be read."""
    with patch("builtins.open", side_effect=IOError("Read failed")):
        with pytest.raises(FileOperationError) as exc_info:
            _load_ids_from_file("unreadable.txt")
    assert "Error reading ID file" in str(exc_info.value)

# --- Fixtures ---

@pytest.fixture
def mock_command():
    return MagicMock(spec=SolrCommand)

@pytest.fixture
def mock_args():
    return Namespace(
        collection="test_collection",
        doc=None, # Changed from docs to match solr batch add
        id_file=None,
        ids=None,
        query=None,
        # batch_size is not an arg for solr batch
    )

# --- Tests for batch_add ---

def test_batch_add_missing_collection(mock_command, mock_args):
    """Test batch add with missing collection name."""
    mock_args.collection = None
    with pytest.raises(CollectionError) as exc_info:
        batch_add(mock_command, mock_args)
    assert "Collection name is required" in str(exc_info.value)

def test_batch_add_no_doc_arg(mock_command, mock_args):
    """Test batch add with no document argument provided."""
    mock_args.doc = None
    with pytest.raises(DocumentError) as exc_info:
        batch_add(mock_command, mock_args)
    assert "--doc is required" in str(exc_info.value)

def test_batch_add_from_string_success(mock_command, mock_args):
    """Test successful batch add from JSON string."""
    docs = [{"id": 1}, {"id": 2}]
    mock_args.doc = json.dumps(docs)
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.message = "Added 2 documents"
    mock_response.error = None
    mock_response.data = {"count": 2}
    mock_command.add_documents.return_value = mock_response

    batch_add(mock_command, mock_args)

    mock_command.add_documents.assert_called_once_with(
        collection="test_collection",
        documents=docs,
        commit=True
    )

def test_batch_add_from_file_success(mock_command, mock_args):
    """Test successful batch add from file."""
    docs = [{"id": 1}, {"id": 2}]
    mock_args.doc = "@docs.json" # Use @ prefix for file
    
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.message = "Added 2 documents"
    mock_response.error = None
    mock_response.data = {"count": 2}
    mock_command.add_documents.return_value = mock_response

    with patch("builtins.open", mock_open(read_data=json.dumps(docs))):
        batch_add(mock_command, mock_args)

    mock_command.add_documents.assert_called_once_with(
        collection="test_collection",
        documents=docs,
        commit=True
    )

def test_batch_add_invalid_json_string(mock_command, mock_args):
    """Test batch add with invalid JSON string."""
    mock_args.doc = "invalid json"
    with pytest.raises(FileParseError) as exc_info:
        batch_add(mock_command, mock_args)
    assert "Invalid JSON in documents string" in str(exc_info.value)

def test_batch_add_non_list_string(mock_command, mock_args):
    """Test batch add with non-list JSON string."""
    mock_args.doc = '{"id": 1}'
    with pytest.raises(DocumentError) as exc_info:
        batch_add(mock_command, mock_args)
    assert "Documents must be a list" in str(exc_info.value)

def test_batch_add_command_failure(mock_command, mock_args):
    """Test handling of SolrCommand.add_documents failure."""
    docs = [{"id": 1}]
    mock_args.doc = json.dumps(docs)
    mock_response = MagicMock()
    mock_response.success = False
    mock_response.error = "Solr commit failed"
    mock_response.message = "Failed to add documents"
    mock_command.add_documents.return_value = mock_response

    with pytest.raises(DocumentStoreError) as exc_info:
        batch_add(mock_command, mock_args)
    
    assert "Failed to add documents: Solr commit failed" in str(exc_info.value)
    assert exc_info.value.details == {
        'collection': 'test_collection',
        'error': 'Solr commit failed'
    }

def test_batch_add_unexpected_exception(mock_command, mock_args):
    """Test handling of unexpected exceptions during add."""
    docs = [{"id": 1}]
    mock_args.doc = json.dumps(docs)
    mock_command.add_documents.side_effect = ValueError("Unexpected issue")

    with pytest.raises(DocumentStoreError) as exc_info:
        batch_add(mock_command, mock_args)
    
    assert "Unexpected error adding documents: Unexpected issue" in str(exc_info.value)
    assert exc_info.value.details == {
        'collection': 'test_collection',
        'error_type': 'ValueError'
    }

# --- Tests for batch_delete will go here ---

def test_batch_delete_missing_collection(mock_command, mock_args):
    """Test batch delete with missing collection name."""
    mock_args.collection = None
    with pytest.raises(CollectionError) as exc_info:
        batch_delete(mock_command, mock_args)
    assert "Collection name is required" in str(exc_info.value)

def test_batch_delete_no_criteria(mock_command, mock_args):
    """Test batch delete with no deletion criteria provided."""
    mock_args.ids = None
    mock_args.id_file = None
    mock_args.query = None
    with pytest.raises(DocumentError) as exc_info:
        batch_delete(mock_command, mock_args)
    assert "Either --ids, --id-file, or --query is required" in str(exc_info.value)

def test_batch_delete_from_string_success(mock_command, mock_args):
    """Test successful batch delete from ID string."""
    ids_list = ["id1", "id2", "id3"]
    mock_args.ids = ",".join(ids_list)
    
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.message = "Deleted 3 documents"
    mock_response.error = None
    mock_response.data = {"count": 3}
    mock_command.delete_documents.return_value = mock_response

    batch_delete(mock_command, mock_args)

    mock_command.delete_documents.assert_called_once_with(
        collection="test_collection",
        ids=ids_list,
        query=None
    )

def test_batch_delete_from_file_success(mock_command, mock_args):
    """Test successful batch delete from file."""
    ids_list = ["id1", "id2", "id3"]
    mock_args.id_file = "ids.txt"
    
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.message = "Deleted 3 documents"
    mock_response.error = None
    mock_response.data = {"count": 3}
    mock_command.delete_documents.return_value = mock_response

    with patch("builtins.open", mock_open(read_data="\n".join(ids_list))):
        batch_delete(mock_command, mock_args)

    mock_command.delete_documents.assert_called_once_with(
        collection="test_collection",
        ids=ids_list,
        query=None
    )

def test_batch_delete_by_query_success(mock_command, mock_args):
    """Test successful batch delete by query."""
    query_str = "field:value"
    mock_args.query = query_str
    
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.message = "Deleted documents matching query"
    mock_response.error = None
    mock_response.data = {"qtime": 10}
    mock_command.delete_documents.return_value = mock_response

    batch_delete(mock_command, mock_args)

    mock_command.delete_documents.assert_called_once_with(
        collection="test_collection",
        ids=None,
        query=query_str
    )

def test_batch_delete_command_failure(mock_command, mock_args):
    """Test handling of SolrCommand.delete_documents failure."""
    ids_list = ["id1"]
    mock_args.ids = ",".join(ids_list)
    mock_response = MagicMock()
    mock_response.success = False
    mock_response.error = "Solr delete failed"
    mock_response.message = "Failed to delete documents"
    mock_command.delete_documents.return_value = mock_response

    with pytest.raises(DocumentStoreError) as exc_info:
        batch_delete(mock_command, mock_args)
    
    assert "Failed to delete documents: Solr delete failed" in str(exc_info.value)
    assert exc_info.value.details == {
        'collection': 'test_collection',
        'error': 'Solr delete failed'
    }

def test_batch_delete_unexpected_exception(mock_command, mock_args):
    """Test handling of unexpected exceptions during delete."""
    ids_list = ["id1"]
    mock_args.ids = ",".join(ids_list)
    mock_command.delete_documents.side_effect = TimeoutError("Request timed out")

    with pytest.raises(DocumentStoreError) as exc_info:
        batch_delete(mock_command, mock_args)
    
    assert "Unexpected error deleting documents: Request timed out" in str(exc_info.value)
    assert exc_info.value.details == {
        'collection': 'test_collection',
        'error_type': 'TimeoutError'
    } 