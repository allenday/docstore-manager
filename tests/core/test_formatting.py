import io
import json
import pytest
# from docstore_manager.core.formatting import format_json, write_json, write_csv, format_table # Removed
from docstore_manager.core.utils import write_output # Use write_output from utils

# Removed test_format_json_* tests as write_output covers JSON formatting

def test_write_json_to_file():
    """Test writing JSON to a file using write_output."""
    data = {'name': 'test', 'value': 123}
    output = io.StringIO()
    # Use write_output with format='json'
    write_output(data, output=output, format='json')
    output.seek(0)
    result = output.read()
    # write_output adds indent=2 by default and a newline
    expected = json.dumps(data, indent=2) + '\n'
    assert result == expected

# Commenting out custom indent test as write_output default indent is 2 and not configurable via args here
# def test_write_json_custom_indent():
#     """Test writing JSON with custom indentation."""
#     data = {'name': 'test'}
#     output = io.StringIO()
#     write_json(data, file=output, indent=4)
#     output.seek(0)
#     result = output.read()
#     expected = json.dumps(data, indent=4) + '\n'
#     assert result == expected

def test_write_csv_basic():
    """Test writing basic CSV data using write_output."""
    data = [
        {'name': 'test1', 'value': 123},
        {'name': 'test2', 'value': 456}
    ]
    # Fieldnames are inferred by write_output
    output = io.StringIO()
    # Use write_output with format='csv'
    write_output(data, output=output, format='csv')
    output.seek(0)
    result = output.read().strip().split('\n')
    assert result[0].rstrip('\r') == 'name,value'
    assert result[1].rstrip('\r') == 'test1,123'
    assert result[2].rstrip('\r') == 'test2,456'

def test_write_csv_missing_fields():
    """Test writing CSV with missing fields using write_output."""
    data = [
        {'name': 'test1'},
        {'name': 'test2', 'value': 456}
    ]
    # Fieldnames are inferred by write_output based on the first dict usually
    # csv.DictWriter handles missing keys by writing empty strings
    output = io.StringIO()
    # Use write_output with format='csv'
    write_output(data, output=output, format='csv')
    output.seek(0)
    result = output.read().strip().split('\n')
    # Check that both headers are present now
    assert result[0].rstrip('\r') == 'name,value'
    # Check data rows (empty string for missing value)
    assert result[1].rstrip('\r') == 'test1,'
    assert result[2].rstrip('\r') == 'test2,456'

# Removed test_format_table_* tests as format_table function seems removed
# def test_format_table_basic():
#     ...
# def test_format_table_empty():
#     ...
# def test_format_table_custom_padding():
#     ...
# def test_format_table_varying_widths():
#     ... 