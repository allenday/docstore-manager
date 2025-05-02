"""Tests for document store exceptions."""

import pytest
from docstore_manager.core.exceptions import (
    DocumentStoreError,
    ConfigurationError,
    ConnectionError,
    CollectionError,
    CollectionAlreadyExistsError,
    CollectionDoesNotExistError,
    CollectionOperationError,
    DocumentError,
    DocumentOperationError,
    InvalidInputError
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
    """Test collection not found error (using CollectionDoesNotExistError)."""
    error = CollectionDoesNotExistError("test_collection", "not found")
    assert str(error) == "not found"
    details = {"collection": "test_collection"}
    error_with_details = CollectionDoesNotExistError("custom message", details=details)
    assert error_with_details.details == details

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

def test_exception_hierarchy():
    """Test the basic exception hierarchy."""
    assert issubclass(CollectionError, DocumentStoreError)
    assert issubclass(CollectionDoesNotExistError, CollectionError)
    assert issubclass(DocumentError, DocumentStoreError)
    assert issubclass(InvalidInputError, DocumentStoreError)

def test_exception_with_details():
    """Test creating an exception with details."""
    details = {"collection": "test_coll", "reason": "not found"}
    exc = CollectionDoesNotExistError("Collection missing", details=details)
    assert str(exc) == "Collection missing"
    assert exc.details == details

def test_exception_without_details():
    """Test creating an exception without details."""
    exc = DocumentError("Doc error")
    assert str(exc) == "Doc error"
    assert exc.details is None

def test_raise_and_catch():
    """Test raising and catching specific exceptions."""
    try:
        raise CollectionDoesNotExistError("Not here")
    except CollectionDoesNotExistError as e:
        assert isinstance(e, CollectionError)
        assert isinstance(e, DocumentStoreError)
        assert str(e) == "Not here"
    except Exception:
        pytest.fail("Caught wrong exception type")

    try:
        raise InvalidInputError("Bad format")
    except InvalidInputError as e:
        assert isinstance(e, DocumentStoreError)
        assert str(e) == "Bad format"
    except Exception:
        pytest.fail("Caught wrong exception type") 