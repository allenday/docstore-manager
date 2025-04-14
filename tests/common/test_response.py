import io
import json
import pytest
import tempfile
import os
from docstore_manager.common.response import (
    Response,
    handle_command_error,
    write_output,
    load_json_file,
    load_id_file,
    validate_collection_name
)
from docstore_manager.common.exceptions import (
    DocumentStoreError,
    CollectionError,
    FileOperationError,
    FileParseError
)

def test_command_response_init():
    """Test CommandResponse initialization."""
    response = Response(
        success=True,
        message="Test message",
        data={"key": "value"},
        error=None,
        error_details=None
    )
    assert response.success is True
    assert response.message == "Test message"
    assert response.data == {"key": "value"}
    assert response.error is None
    assert response.error_details is None

def test_handle_command_error_document_store_error():
    """Test handling DocumentStoreError."""
    error = DocumentStoreError("Test error", {"detail": "test"})
    response = handle_command_error(error)
    assert response.success is False
    assert response.message == "Test error"
    assert response.error == "DocumentStoreError"
    assert response.error_details == {"detail": "test"}

def test_handle_command_error_unexpected():
    """Test handling unexpected error."""
    error = ValueError("Test error")
    response = handle_command_error(error)
    assert response.success is False
    assert response.message == "Unexpected error: Test error"
    assert response.error == "UnexpectedError"
    assert response.error_details == {"type": "ValueError"}

def test_write_output_json_stdout(capsys):
    """Test writing JSON output to stdout."""
    data = {"test": "value"}
    write_output(data)
    captured = capsys.readouterr()
    assert json.loads(captured.out) == data

def test_write_output_json_file():
    """Test writing JSON output to file."""
    data = {"test": "value"}
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        write_output(data, tmp.name)
        with open(tmp.name, 'r') as f:
            result = json.load(f)
        assert result == data
        os.unlink(tmp.name)

def test_write_output_csv_stdout(capsys):
    """Test writing CSV output to stdout."""
    data = [{"name": "test1", "value": 123}, {"name": "test2", "value": 456}]
    write_output(data, format='csv')
    captured = capsys.readouterr()
    lines = captured.out.strip().split('\n')
    assert lines[0].rstrip('\r') == 'name,value'
    assert lines[1].rstrip('\r') == 'test1,123'
    assert lines[2].rstrip('\r') == 'test2,456'

def test_write_output_csv_file():
    """Test writing CSV output to file."""
    data = [{"name": "test1", "value": 123}, {"name": "test2", "value": 456}]
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        write_output(data, tmp.name, format='csv')
        with open(tmp.name, 'r') as f:
            lines = f.read().strip().split('\n')
        assert lines[0].rstrip('\r') == 'name,value'
        assert lines[1].rstrip('\r') == 'test1,123'
        assert lines[2].rstrip('\r') == 'test2,456'
        os.unlink(tmp.name)

def test_write_output_invalid_format():
    """Test writing output with invalid format."""
    with pytest.raises(ValueError) as exc_info:
        write_output({}, format='invalid')
    assert "Unsupported output format: invalid" in str(exc_info.value)

def test_write_output_invalid_csv_data():
    """Test writing invalid data as CSV."""
    with pytest.raises(ValueError) as exc_info:
        write_output({"not": "a list"}, format='csv')
    assert "CSV output requires list of dictionaries" in str(exc_info.value)

def test_load_json_file():
    """Test loading a JSON file."""
    data = {"test": "value"}
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        json.dump(data, tmp)
        tmp.flush()
        result = load_json_file(tmp.name)
        assert result == data
        os.unlink(tmp.name)

def test_load_json_file_not_found():
    """Test loading a non-existent JSON file."""
    with pytest.raises(FileOperationError) as exc_info:
        load_json_file("nonexistent.json")
    assert "File not found" in str(exc_info.value)

def test_load_json_file_invalid():
    """Test loading an invalid JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write("invalid json")
        tmp.flush()
        with pytest.raises(FileParseError) as exc_info:
            load_json_file(tmp.name)
        assert "Expecting value" in str(exc_info.value)
        os.unlink(tmp.name)

def test_load_json_file_read_error():
    """Test loading a JSON file with read error."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write('{"test": "value"}')
        tmp.flush()
        os.chmod(tmp.name, 0o000)  # Remove read permissions
        with pytest.raises(FileOperationError) as exc_info:
            load_json_file(tmp.name)
        assert "Error reading file" in str(exc_info.value)
        os.chmod(tmp.name, 0o666)  # Restore permissions
        os.unlink(tmp.name)

def test_load_id_file():
    """Test loading an ID file."""
    ids = ["id1", "id2", "id3"]
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write("\n".join(ids))
        tmp.flush()
        result = load_id_file(tmp.name)
        assert result == ids
        os.unlink(tmp.name)

def test_load_id_file_empty_lines():
    """Test loading an ID file with empty lines."""
    content = "id1\n\nid2\n  \nid3"
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write(content)
        tmp.flush()
        result = load_id_file(tmp.name)
        assert result == ["id1", "id2", "id3"]
        os.unlink(tmp.name)

def test_load_id_file_not_found():
    """Test loading a non-existent ID file."""
    with pytest.raises(FileOperationError) as exc_info:
        load_id_file("nonexistent.txt")
    assert "File not found" in str(exc_info.value)

def test_load_id_file_read_error():
    """Test loading an ID file with read error."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write("id1\nid2\nid3")
        tmp.flush()
        os.chmod(tmp.name, 0o000)  # Remove read permissions
        with pytest.raises(FileOperationError) as exc_info:
            load_id_file(tmp.name)
        assert "Error reading file" in str(exc_info.value)
        os.chmod(tmp.name, 0o666)  # Restore permissions
        os.unlink(tmp.name)

def test_validate_collection_name():
    """Test validating collection name."""
    validate_collection_name("test")  # Should not raise

def test_validate_collection_name_empty():
    """Test validating empty collection name."""
    with pytest.raises(CollectionError) as exc_info:
        validate_collection_name("")
    assert "Collection name is required" in str(exc_info.value)

def test_validate_collection_name_none():
    """Test validating None collection name."""
    with pytest.raises(CollectionError) as exc_info:
        validate_collection_name(None)
    assert "Collection name is required" in str(exc_info.value) 