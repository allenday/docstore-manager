"""Tests for common utility functions."""

import pytest
import json
import tempfile
import os
from unittest.mock import mock_open, patch
from io import StringIO
import logging
import csv

# Import exceptions expected to be raised by utils
from docstore_manager.core.exceptions import DocumentStoreError, InvalidInputError

from docstore_manager.core.utils import (
    load_json_file,
    load_documents_from_file,
    load_ids_from_file,
    parse_json_string,
    write_output
)

def test_load_json_file_success():
    """Test successful JSON file loading."""
    test_data = {"key": "value"}
    mock_file = mock_open(read_data=json.dumps(test_data))
    
    with patch("builtins.open", mock_file):
        result = load_json_file("test.json")
        assert result == test_data

def test_load_json_file_not_found():
    """Test loading non-existent JSON file."""
    with pytest.raises(DocumentStoreError) as exc:
        load_json_file("nonexistent.json")
    assert "Error reading file" in str(exc.value)

def test_load_json_file_invalid():
    """Test loading invalid JSON file."""
    mock_file = mock_open(read_data="{invalid json")
    
    with patch("builtins.open", mock_file):
        with pytest.raises(InvalidInputError) as exc:
            load_json_file("test.json")
        assert "Invalid JSON in file" in str(exc.value)

def test_load_documents_from_file_success():
    """Test successful document loading."""
    test_docs = [{"id": 1}, {"id": 2}]
    mock_file = mock_open(read_data=json.dumps(test_docs))
    
    with patch("builtins.open", mock_file):
        result = load_documents_from_file("docs.json")
        assert result == test_docs

def test_load_documents_from_file_not_list():
    """Test loading non-list documents."""
    test_data = {"not": "a list"}
    mock_file = mock_open(read_data=json.dumps(test_data))
    
    with patch("builtins.open", mock_file):
        with pytest.raises(InvalidInputError) as exc:
            load_documents_from_file("docs.json")
        assert "Documents in docs.json must be a JSON array" in str(exc.value)

def test_load_ids_from_file_success():
    """Test successful ID loading."""
    test_ids = "id1\nid2\nid3"
    mock_file = mock_open(read_data=test_ids)
    
    with patch("builtins.open", mock_file):
        result = load_ids_from_file("ids.txt")
        assert result == ["id1", "id2", "id3"]

def test_load_ids_from_file_empty():
    """Test loading empty ID file."""
    mock_file = mock_open(read_data="")
    
    with patch("builtins.open", mock_file):
        with pytest.raises(DocumentStoreError) as exc:
            load_ids_from_file("ids.txt")
        assert "No valid IDs found in file" in str(exc.value)

def test_parse_json_string_success():
    """Test successful JSON string parsing."""
    test_data = {"key": "value"}
    result = parse_json_string(json.dumps(test_data))
    assert result == test_data

def test_parse_json_string_invalid():
    """Test parsing invalid JSON string."""
    with pytest.raises(InvalidInputError) as exc:
        parse_json_string("{invalid json", "test")
    assert "Invalid JSON in test" in str(exc.value)

def test_write_output_json_stdout():
    """Test writing JSON output to stdout."""
    test_data = {"key": "value"}
    mock_stdout = StringIO()
    
    with patch("sys.stdout", mock_stdout):
        write_output(test_data)
        output = mock_stdout.getvalue()
        assert json.loads(output) == test_data

def test_write_output_json_file():
    """Test writing JSON output to file."""
    test_data = {"key": "value"}
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        write_output(test_data, tmp.name)
        
    try:
        with open(tmp.name) as f:
            result = json.load(f)
            assert result == test_data
    finally:
        os.unlink(tmp.name)

def test_write_output_csv():
    """Test writing CSV output."""
    test_data = [
        {"id": 1, "name": "test1"},
        {"id": 2, "name": "test2"}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        write_output(test_data, tmp.name, format='csv')
        
    try:
        with open(tmp.name) as f:
            lines = f.readlines()
            assert lines[0].strip() == "id,name"
            assert lines[1].strip() == "1,test1"
            assert lines[2].strip() == "2,test2"
    finally:
        os.unlink(tmp.name)

def test_write_output_invalid_format():
    """Test writing with invalid format."""
    with pytest.raises(ValueError) as exc:
        write_output({}, format='invalid')
    assert "Unsupported output format" in str(exc.value)

def test_write_output_file_error():
    """Test writing with file error."""
    with pytest.raises(DocumentStoreError) as exc:
        write_output({}, "/nonexistent/path/file.json")
    assert "Failed to open output file" in str(exc.value)

def test_write_output_csv_non_list():
    """Test writing CSV output with non-list data."""
    test_data = {"id": 1, "name": "test1"}
    mock_stdout = StringIO()
    
    with patch("sys.stdout", mock_stdout):
        write_output(test_data, format='csv')
        output = mock_stdout.getvalue()
        assert "id,name" in output
        assert "1,test1" in output

def test_write_output_csv_stdout():
    """Test writing CSV output to stdout."""
    test_data = [{"id": 1, "name": "test1"}]
    mock_stdout = StringIO()
    
    with patch("sys.stdout", mock_stdout):
        write_output(test_data, format='csv')
        output = mock_stdout.getvalue()
        assert "id,name" in output
        assert "1,test1" in output

def test_write_output_error_handling():
    """Test error handling during output writing."""
    test_data = {"key": "value"}
    
    class BrokenFile:
        def write(self, _):
            raise IOError("Write error")
        
        @property
        def name(self):
            return "broken.json"
    
    with pytest.raises(DocumentStoreError) as exc:
        write_output(test_data, BrokenFile())
    assert "Error writing output" in str(exc.value)

def test_write_output_empty_csv():
    """Test writing empty list to CSV."""
    test_data = []
    mock_stdout = StringIO()
    
    with patch("sys.stdout", mock_stdout):
        write_output(test_data, format='csv')
        output = mock_stdout.getvalue()
        assert output.strip() == ""

def test_write_output_json_stdout_with_logger(caplog):
    """Test writing JSON output to stdout with logger message."""
    caplog.set_level(logging.INFO)
    
    test_data = {"key": "value"}
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        write_output(test_data, tmp.name)
        assert f"Output written to {tmp.name}" in caplog.text
    
    os.unlink(tmp.name) 