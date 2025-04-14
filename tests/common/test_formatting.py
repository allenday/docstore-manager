import io
import json
import pytest
from docstore_manager.common.formatting import format_json, write_json, write_csv, format_table

def test_format_json_dict():
    """Test formatting a dictionary as JSON."""
    data = {'name': 'test', 'value': 123}
    result = format_json(data)
    expected = json.dumps(data, indent=2)
    assert result == expected

def test_format_json_list():
    """Test formatting a list as JSON."""
    data = [{'name': 'test1'}, {'name': 'test2'}]
    result = format_json(data)
    expected = json.dumps(data, indent=2)
    assert result == expected

def test_format_json_custom_indent():
    """Test formatting JSON with custom indentation."""
    data = {'name': 'test'}
    result = format_json(data, indent=4)
    expected = json.dumps(data, indent=4)
    assert result == expected

def test_write_json_to_file():
    """Test writing JSON to a file."""
    data = {'name': 'test', 'value': 123}
    output = io.StringIO()
    write_json(data, file=output)
    output.seek(0)
    result = output.read()
    expected = json.dumps(data, indent=2) + '\n'
    assert result == expected

def test_write_json_custom_indent():
    """Test writing JSON with custom indentation."""
    data = {'name': 'test'}
    output = io.StringIO()
    write_json(data, file=output, indent=4)
    output.seek(0)
    result = output.read()
    expected = json.dumps(data, indent=4) + '\n'
    assert result == expected

def test_write_csv_basic():
    """Test writing basic CSV data."""
    data = [
        {'name': 'test1', 'value': 123},
        {'name': 'test2', 'value': 456}
    ]
    fieldnames = ['name', 'value']
    output = io.StringIO()
    write_csv(data, fieldnames, file=output)
    output.seek(0)
    result = output.read().strip().split('\n')
    assert result[0].rstrip('\r') == 'name,value'
    assert result[1].rstrip('\r') == 'test1,123'
    assert result[2].rstrip('\r') == 'test2,456'

def test_write_csv_missing_fields():
    """Test writing CSV with missing fields."""
    data = [
        {'name': 'test1'},
        {'name': 'test2', 'value': 456}
    ]
    fieldnames = ['name', 'value']
    output = io.StringIO()
    write_csv(data, fieldnames, file=output)
    output.seek(0)
    result = output.read().strip().split('\n')
    assert result[0].rstrip('\r') == 'name,value'
    assert result[1].rstrip('\r') == 'test1,'
    assert result[2].rstrip('\r') == 'test2,456'

def test_format_table_basic():
    """Test formatting a basic table."""
    headers = ['Name', 'Value']
    rows = [
        ['test1', 123],
        ['test2', 456]
    ]
    result = format_table(headers, rows)
    lines = result.split('\n')
    assert lines[0].rstrip() == "  Name   Value"
    assert len(lines[1].strip('-')) == 0  # Check that it's all dashes
    assert lines[2].rstrip() == "  test1  123"
    assert lines[3].rstrip() == "  test2  456"

def test_format_table_empty():
    """Test formatting a table with no rows."""
    headers = ['Name', 'Value']
    rows = []
    result = format_table(headers, rows)
    lines = result.split('\n')
    assert lines[0].rstrip() == "  Name  Value"
    assert len(lines[1].strip('-')) == 0  # Check that it's all dashes

def test_format_table_custom_padding():
    """Test formatting a table with custom padding."""
    headers = ['A', 'B']
    rows = [['1', '2']]
    result = format_table(headers, rows, padding=4)
    lines = result.split('\n')
    assert lines[0].rstrip() == "    A    B"
    assert len(lines[1].strip('-')) == 0  # Check that it's all dashes
    assert lines[2].rstrip() == "    1    2"

def test_format_table_varying_widths():
    """Test formatting a table with varying column widths."""
    headers = ['Short', 'Very Long Header']
    rows = [
        ['tiny', 'medium text'],
        ['microscopic', 'longer text here']
    ]
    result = format_table(headers, rows)
    lines = result.split('\n')
    assert lines[0].rstrip() == "  Short        Very Long Header"
    assert len(lines[1].strip('-')) == 0  # Check that it's all dashes
    assert lines[2].rstrip() == "  tiny         medium text"
    assert lines[3].rstrip() == "  microscopic  longer text here" 