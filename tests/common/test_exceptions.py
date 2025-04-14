"""Tests for document store exceptions."""

import pytest
from docstore_manager.common.exceptions import (
    DocumentStoreError,
    ConfigurationError,
    ConnectionError,
    CollectionError,
    CollectionNotFoundError,
    CollectionAlreadyExistsError,
    CollectionOperationError,
    DocumentError,
    DocumentNotFoundError,
    DocumentValidationError,
    BatchOperationError,
    FileOperationError,
    FileNotFoundError,
    FileParseError,
    QueryError,
    QueryParseError,
    QueryValidationError
)

def test_document_store_error():
    """Test base document store error."""
    error = DocumentStoreError("test message")
    assert str(error) == "test message"
    assert error.details == {}

    error_with_details = DocumentStoreError("test message", {"key": "value"})
    assert error_with_details.details == {"key": "value"}

def test_configuration_error():
    """Test configuration error."""
    error = ConfigurationError("config error")
    assert str(error) == "config error"
    assert error.details == {}

def test_connection_error():
    """Test connection error."""
    error = ConnectionError("connection error")
    assert str(error) == "connection error"
    assert error.details == {}

def test_collection_error():
    """Test collection error."""
    error = CollectionError("test_collection", "collection error")
    assert str(error) == "collection error"
    assert error.collection == "test_collection"
    assert error.details == {}

def test_collection_not_found_error():
    """Test collection not found error."""
    error = CollectionNotFoundError("test_collection", "not found")
    assert str(error) == "not found"
    assert error.collection == "test_collection"

def test_collection_already_exists_error():
    """Test collection already exists error."""
    error = CollectionAlreadyExistsError("test_collection", "already exists")
    assert str(error) == "already exists"
    assert error.collection == "test_collection"

def test_collection_operation_error():
    """Test collection operation error."""
    error = CollectionOperationError("test_collection", "operation failed")
    assert str(error) == "operation failed"
    assert error.collection == "test_collection"

def test_document_error():
    """Test document error."""
    error = DocumentError("test_collection", "document error")
    assert str(error) == "document error"
    assert error.collection == "test_collection"
    assert error.details == {}

def test_document_not_found_error():
    """Test document not found error."""
    error = DocumentNotFoundError("test_collection", "doc123")
    assert "Document 'doc123' not found in collection 'test_collection'" in str(error)
    assert error.collection == "test_collection"
    assert error.doc_id == "doc123"
    assert error.details == {"doc_id": "doc123"}

    # Test with custom message
    error = DocumentNotFoundError("test_collection", "doc123", "custom message")
    assert str(error) == "custom message"

def test_document_validation_error():
    """Test document validation error."""
    validation_errors = {"field": "invalid value"}
    error = DocumentValidationError("test_collection", validation_errors)
    assert "Document validation failed for collection 'test_collection'" in str(error)
    assert error.collection == "test_collection"
    assert error.validation_errors == validation_errors
    assert error.details == {"validation_errors": validation_errors}

    # Test with custom message
    error = DocumentValidationError("test_collection", validation_errors, "custom message")
    assert str(error) == "custom message"

def test_batch_operation_error():
    """Test batch operation error."""
    failed_items = {"id1": "error1", "id2": "error2"}
    error = BatchOperationError("test_collection", "update", failed_items)
    assert "Batch update operation failed for collection 'test_collection'" in str(error)
    assert error.collection == "test_collection"
    assert error.operation == "update"
    assert error.failed_items == failed_items
    assert error.details == {"failed_items": failed_items}

    # Test with custom message
    error = BatchOperationError("test_collection", "update", failed_items, "custom message")
    assert str(error) == "custom message"

def test_file_operation_error():
    """Test file operation error."""
    error = FileOperationError("test.txt", "file error")
    assert str(error) == "file error"
    assert error.file_path == "test.txt"
    assert error.details == {}

def test_file_not_found_error():
    """Test file not found error."""
    error = FileNotFoundError("test.txt")
    assert str(error) == "File not found: test.txt"
    assert error.file_path == "test.txt"

def test_file_parse_error():
    """Test file parse error."""
    error = FileParseError("test.txt", "JSON", "invalid format")
    assert str(error) == "invalid format"
    assert error.file_path == "test.txt"
    assert error.format_type == "JSON"
    assert error.parse_error == "invalid format"
    assert error.details == {"format": "JSON"}

def test_query_error():
    """Test query error."""
    query = {"field": "value"}
    error = QueryError(query, "query error")
    assert str(error) == "query error"
    assert error.query == query
    assert error.details == {}

def test_query_parse_error():
    """Test query parse error."""
    query = "invalid query"
    error = QueryParseError(query, "parse error")
    assert str(error) == "parse error"
    assert error.query == query

def test_query_validation_error():
    """Test query validation error."""
    query = {"field": "invalid"}
    error = QueryValidationError(query, "validation error")
    assert str(error) == "validation error"
    assert error.query == query 