"""Tests for base command functionality."""

import pytest
from unittest.mock import Mock, patch, mock_open
import json
from typing import Dict, Any, List
from pytest import raises
from unittest.mock import MagicMock

from docstore_manager.core.command.base import CommandResponse, DocumentStoreCommand
from docstore_manager.core.exceptions import (
    DocumentError,
    InvalidInputError,
    DocumentStoreError,
    CollectionError,
    CollectionDoesNotExistError
)

@pytest.fixture
def command():
    """Create a test command instance."""
    return DocumentStoreCommand()

def test_command_response_creation():
    """Test creating a command response."""
    response = CommandResponse(
        success=True,
        message="Test message",
        data={"test": "data"},
        error=None,
        details={"extra": "info"}
    )
    assert response.success
    assert response.message == "Test message"
    assert response.data == {"test": "data"}
    assert response.error is None
    assert response.details == {"extra": "info"}

class TestDocumentStoreCommand:
    """Tests for DocumentStoreCommand."""

    def test_create_response(self, command):
        """Test response creation helper."""
        response = command._create_response(
            success=True,
            message="Test",
            data={"test": "data"},
            error=None,
            details={"extra": "info"}
        )
        assert isinstance(response, CommandResponse)
        assert response.success
        assert response.message == "Test"
        assert response.data == {"test": "data"}
        assert response.error is None
        assert response.details == {"extra": "info"}

    def test_load_documents_from_string(self, command):
        """Test loading documents from string."""
        docs = [{"id": 1}, {"id": 2}]
        result = command._load_documents("test", docs_str=json.dumps(docs))
        assert result == docs

    def test_load_documents_invalid_json(self, command):
        """Test loading documents with invalid JSON."""
        with pytest.raises(InvalidInputError) as exc:
            command._load_documents("test", docs_str="{invalid json}")
        assert "Failed to parse" in str(exc.value)

    def test_load_documents_not_list(self, command):
        """Test loading documents with non-list JSON."""
        with pytest.raises(InvalidInputError) as exc:
            command._load_documents("test", docs_str='{"not": "a list"}')
        assert "Documents JSON must be an array (list), got dict" in str(exc.value)

    def test_load_documents_from_file(self, command):
        """Test loading documents from file."""
        docs = [{"id": 1}, {"id": 2}]
        mock_file = mock_open(read_data=json.dumps(docs))
        with patch("builtins.open", mock_file):
            result = command._load_documents("test", docs_file="test.json")
            assert result == docs

    def test_load_documents_file_not_found(self, command):
        """Test loading documents from non-existent file."""
        with pytest.raises(DocumentError) as exc:
            with patch("builtins.open", mock_open()) as m_open:
                m_open.side_effect = FileNotFoundError
                command._load_documents("test", docs_file="nonexistent.json")
        assert "Failed to load documents" in str(exc.value)
        assert "Error reading file" in str(exc.value)

    def test_load_documents_no_source(self, command):
        """Test loading documents with no source."""
        with pytest.raises(InvalidInputError) as exc:
            command._load_documents("test")
        assert "Either --documents-file or --documents must be provided" in str(exc.value)

    def test_load_ids_from_string(self, command):
        """Test loading IDs from string."""
        result = command._load_ids("test", ids_str="id1,id2, id3")
        assert result == ["id1", "id2", "id3"]

    def test_load_ids_empty(self, command):
        """Test loading IDs with empty input."""
        with pytest.raises(InvalidInputError) as exc:
            command._load_ids("test", ids_str="  ,  ,  ")
        assert "No valid document IDs" in str(exc.value)

    def test_load_ids_from_file(self, command):
        """Test loading IDs from file."""
        mock_file = mock_open(read_data="id1\nid2\nid3\n")
        with patch("builtins.open", mock_file):
            result = command._load_ids("test", ids_file="ids.txt")
            assert result == ["id1", "id2", "id3"]

    def test_load_ids_file_not_found(self, command):
        """Test loading IDs from non-existent file."""
        with pytest.raises(DocumentError) as exc:
            with patch("builtins.open", mock_open()) as m_open:
                m_open.side_effect = FileNotFoundError
                command._load_ids("test", ids_file="nonexistent.txt")
        assert "Failed to load IDs" in str(exc.value)
        assert "Error reading file" in str(exc.value)

    def test_load_ids_no_source(self, command):
        """Test loading IDs with no source."""
        assert command._load_ids("test") is None

    def test_parse_query_valid(self, command):
        """Test parsing valid query."""
        query = {"field": "value"}
        result = command._parse_query("test", json.dumps(query))
        assert result == query

    def test_parse_query_invalid(self, command):
        """Test parsing invalid query JSON."""
        with pytest.raises(InvalidInputError) as exc:
            command._parse_query("test", "{invalid}")
        assert "Failed to parse" in str(exc.value)

    def test_parse_query_none(self, command):
        """Test parsing None query."""
        assert command._parse_query("test", None) is None

    def test_parse_query_empty(self, command):
        """Test parsing empty query string."""
        assert command._parse_query("test", "") is None

    def test_write_output_success(self, command):
        """Test successful output writing."""
        data = {"test": "data"}
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            command._write_output(data, "test.json")
        mock_file().write.assert_called()

    def test_write_output_error(self, command):
        """Test output writing with error."""
        with patch("docstore_manager.core.command.base.write_output", 
                  side_effect=DocumentStoreError("Write failed")):
            with pytest.raises(DocumentStoreError) as exc:
                command._write_output({"test": "data"}, "test.json")
            assert "Write failed" in str(exc.value)

    def test_write_output_stdout(self, command):
        """Test writing output to stdout."""
        data = {"test": "data"}
        with patch("sys.stdout") as mock_stdout:
            command._write_output(data)
        assert mock_stdout.write.called

    def test_write_output_csv(self, command):
        """Test writing CSV output."""
        data = [{"id": 1, "name": "test"}]
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            command._write_output(data, "test.csv", format="csv")
        mock_file().write.assert_called()

    def test_write_output_invalid_format(self, command):
        """Test writing with invalid format."""
        with pytest.raises(InvalidInputError) as exc:
            command._write_output({"test": "data"}, format="invalid")
        assert "Unsupported output format" in str(exc.value)

    def test_write_output_success_with_patch(self, command):
        """Test successful output writing with patch."""
        sample_data = {"test": "data"}
        mock_response = CommandResponse(success=True, message="Success", data=sample_data)
        with patch("docstore_manager.core.command.base.write_output",
                   MagicMock()) as mock_write:
            command._write_output(mock_response, format='json', output=None)
            mock_write.assert_called_once_with(sample_data, None, 'json')

    def test_write_output_file_with_patch(self, command):
        """Test writing output to file with patch."""
        sample_data = {"test": "data"}
        mock_response_file = CommandResponse(success=True, message="Success", data=sample_data)
        with patch("docstore_manager.core.command.base.write_output",
                   MagicMock()) as mock_write_file:
            command._write_output(mock_response_file,
                                   format='csv',
                                   output="test.csv")
            mock_write_file.assert_called_once_with(sample_data, "test.csv", 'csv') 