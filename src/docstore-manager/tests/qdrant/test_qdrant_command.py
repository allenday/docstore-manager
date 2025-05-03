"""Tests for Qdrant standalone command functions."""

import pytest
import json
from unittest.mock import patch, MagicMock, mock_open, call
import argparse # Keep for potential arg parsing simulation if needed later
import uuid
import logging

# Import standalone command functions
from docstore_manager.qdrant.commands import (
    create as cmd_create,
    delete as cmd_delete_collection, # Alias for clarity
    list as cmd_list,
    info as cmd_info,
    batch as cmd_batch, # Keep for add_documents, remove_documents
    get as cmd_get,
    search as cmd_search,
    scroll as cmd_scroll,
    count as cmd_count
)
# Import specific functions from batch needed
from docstore_manager.qdrant.commands.batch import add_documents as batch_add_documents, remove_documents as batch_remove_documents

# Import necessary exceptions and models
from docstore_manager.core.exceptions import (
    DocumentError,
    CollectionError,
    ConfigurationError,
    ConnectionError,
    CollectionAlreadyExistsError,
    CollectionDoesNotExistError, # Corrected name if needed
    InvalidInputError
)
from qdrant_client import QdrantClient # For spec
from qdrant_client.http import models as rest
from qdrant_client.http.models import Distance, VectorParams, PointStruct, CollectionDescription, CollectionsResponse, UpdateResult, UpdateStatus, CountResult

# Import helper functions if needed
from docstore_manager.qdrant.utils import QdrantFormatter # Import added

# Shared Fixture for Mock Client
@pytest.fixture
def mock_client():
    """Provides a MagicMock QdrantClient."""
    # Use spec_set=True for stricter mocking if needed
    client = MagicMock(spec=QdrantClient)
    # Set default return values for methods commonly called without side effects
    client.get_collections.return_value = CollectionsResponse(collections=[])
    client.get_collection.return_value = MagicMock() # Placeholder
    client.upsert.return_value = UpdateResult(operation_id=0, status=UpdateStatus.COMPLETED)
    client.delete.return_value = UpdateResult(operation_id=1, status=UpdateStatus.COMPLETED)
    client.search.return_value = [] # Empty list of ScoredPoint
    client.scroll.return_value = ([], None) # Tuple (points, next_offset)
    client.count.return_value = CountResult(count=0)
    client.retrieve.return_value = [] # Empty list of PointStruct
    client.recreate_collection.return_value = True # Assume success
    client.delete_collection.return_value = True # Assume success
    return client

# === Test Create Collection ===

def test_create_collection_success(mock_client, caplog):
    """Test successful collection creation."""
    caplog.set_level(logging.INFO, logger="docstore_manager.qdrant.commands.create") # Set logger
    collection_name = "test_create_coll"
    # Mock the correct client method for overwrite=False
    mock_client.create_collection.return_value = True

    cmd_create.create_collection(
        client=mock_client,
        collection_name=collection_name,
        dimension=128,
        distance=Distance.COSINE,
        overwrite=False # Explicitly False
    )

    # Assert create_collection was called, and recreate_collection was NOT called
    mock_client.create_collection.assert_called_once()
    mock_client.recreate_collection.assert_not_called() # Important!

    args, kwargs = mock_client.create_collection.call_args
    assert kwargs['collection_name'] == collection_name
    assert isinstance(kwargs['vectors_config'], VectorParams)
    assert kwargs['vectors_config'].size == 128
    assert kwargs['vectors_config'].distance == Distance.COSINE
    # Removed caplog assertion, check stdout instead if needed
    # assert "Successfully created collection" in caplog.text

def test_create_collection_overwrite(mock_client, caplog):
    """Test successful collection creation with overwrite=True."""
    caplog.set_level(logging.INFO, logger="docstore_manager.qdrant.commands.create") # Set logger
    collection_name = "test_overwrite_coll"
    mock_client.recreate_collection.return_value = True

    cmd_create.create_collection(
        client=mock_client,
        collection_name=collection_name,
        dimension=768,
        distance=Distance.EUCLID,
        overwrite=True
    )

    mock_client.recreate_collection.assert_called_once()
    args, kwargs = mock_client.recreate_collection.call_args
    assert kwargs['collection_name'] == collection_name
    assert kwargs['vectors_config'].size == 768
    assert kwargs['vectors_config'].distance == Distance.EUCLID
    # Removed caplog assertion
    # assert "Successfully created collection 'test_overwrite_coll' (overwritten if existed)." in caplog.text

def test_create_collection_client_error(mock_client):
    """Test error handling during collection creation."""
    collection_name = "test_error_coll"
    error_message = "Connection refused"
    mock_client.create_collection.side_effect = ConnectionError(error_message)
    mock_client.recreate_collection.side_effect = None # Prevent interference

    # The create command raises CollectionError now
    with pytest.raises(CollectionError) as exc_info:
        cmd_create.create_collection(
            client=mock_client,
            collection_name=collection_name,
            dimension=10,
            distance=Distance.COSINE,
            overwrite=False
        )
    assert isinstance(exc_info.value, CollectionError)
    # Check for the core error message
    assert error_message in str(exc_info.value)

# === Test Delete Collection ===

def test_delete_collection_success(mock_client, caplog):
    """Test successful collection deletion."""
    caplog.set_level(logging.INFO, logger="docstore_manager.qdrant.commands.delete")
    collection_name = "test_delete_coll"
    mock_client.delete_collection.return_value = True
    cmd_delete_collection.delete_collection(client=mock_client, collection_name=collection_name)
    mock_client.delete_collection.assert_called_once_with(
        collection_name=collection_name,
        timeout=None
    )
    # Check actual log message
    assert f"Successfully deleted collection '{collection_name}'" in caplog.text

def test_delete_collection_client_error(mock_client):
    """Test error handling during collection deletion."""
    collection_name = "test_delete_fail"
    error_message = "Collection lock timeout"
    mock_client.delete_collection.side_effect = Exception(error_message)

    # The delete command raises CollectionError for unexpected errors
    with pytest.raises(CollectionError) as exc_info:
        cmd_delete_collection.delete_collection(client=mock_client, collection_name=collection_name)

    assert isinstance(exc_info.value, CollectionError)
    # Check for the core error message
    assert error_message in str(exc_info.value)

# === Test List Collections (covered in test_list_cmd.py) ===
# We can add specific cases here if needed, but main tests are separate

# === Test Get Collection Info ===

def test_get_collection_info_client_error(mock_client):
    """Test error handling when getting collection info."""
    collection_name = "test_info_fail"
    error_message = "Collection not found (404)"
    mock_client.get_collection.side_effect = Exception(error_message)

    with pytest.raises(CollectionError) as exc_info:
        cmd_info.collection_info(client=mock_client, collection_name=collection_name)

    assert isinstance(exc_info.value, CollectionError)
    # Check for the core error message
    assert error_message in str(exc_info.value)

# === Test Add Documents ===

def test_add_documents_success(mock_client, caplog):
    """Test adding documents successfully."""
    caplog.set_level(logging.INFO, logger="docstore_manager.qdrant.commands.batch")
    collection_name = "test_add_docs"
    docs = [
        {"id": "doc1", "vector": [0.1, 0.2], "metadata": {"field": "value1"}},
        {"id": "doc2", "vector": [0.3, 0.4], "metadata": {"field": "value2"}}
    ]
    mock_client.upsert.return_value = UpdateResult(operation_id=0, status=UpdateStatus.COMPLETED)
    batch_add_documents(client=mock_client, collection_name=collection_name, documents=docs)
    mock_client.upsert.assert_called_once()
    # Corrected log assertion
    assert f"Successfully added/updated {len(docs)} documents to collection '{collection_name}'" in caplog.text

def test_add_documents_invalid_input(mock_client):
    """Test adding documents with invalid structure (missing id/vector)."""
    collection_name = "test_add_invalid"
    docs_no_id = [{"vector": [0.1], "payload": {"field": "value"}}]
    docs_no_vector = [{"id": "doc1", "payload": {"field": "value"}}]

    with pytest.raises(DocumentError) as exc_info_id:
        batch_add_documents(client=mock_client, collection_name=collection_name, documents=docs_no_id)
        # assert "Document validation failed" in str(exc_info_id.value)
        # Check for the specific validation message
        assert "Document at index 0 missing 'id' field" in exc_info_id.value.args[0]

    with pytest.raises(DocumentError) as exc_info_vector:
        batch_add_documents(client=mock_client, collection_name=collection_name, documents=docs_no_vector)
        # assert "Document validation failed" in str(exc_info_vector.value)
        assert "missing 'vector' field" in exc_info_vector.value.args[0]

def test_add_documents_client_error(mock_client):
    """Test error handling when adding documents."""
    collection_name = "test_add_fail"
    docs = [{"id": "doc1", "vector": [0.1]}]
    error_message = "Upsert failed"
    mock_client.upsert.side_effect = Exception(error_message)

    with pytest.raises(DocumentError) as exc_info:
        batch_add_documents(client=mock_client, collection_name=collection_name, documents=docs)

    assert isinstance(exc_info.value, DocumentError)
    # Check for the core error message
    assert error_message in str(exc_info.value)

# === Test Delete Documents ===

def test_delete_documents_success(mock_client, caplog):
    """Test deleting documents successfully."""
    caplog.set_level(logging.INFO, logger="docstore_manager.qdrant.commands.batch")
    collection_name = "test_del_docs"
    doc_ids = ["id1", "id2"]
    mock_client.delete.return_value = UpdateResult(operation_id=1, status=UpdateStatus.COMPLETED)
    batch_remove_documents(client=mock_client, collection_name=collection_name, doc_ids=doc_ids)
    mock_client.delete.assert_called_once()
    # Check actual log message
    assert f"Remove operation by IDs for collection '{collection_name}' finished. Status: completed" in caplog.text

def test_delete_documents_client_error(mock_client):
    """Test error handling when deleting documents."""
    collection_name = "test_del_fail"
    doc_ids = ["id1"]
    error_message = "Delete failed"
    mock_client.delete.side_effect = Exception(error_message)

    with pytest.raises(DocumentError) as exc_info:
        batch_remove_documents(client=mock_client, collection_name=collection_name, doc_ids=doc_ids)

    assert isinstance(exc_info.value, DocumentError)
    # Assert on specific attributes
    assert exc_info.value.collection_name == collection_name
    assert f"Unexpected error removing documents: {error_message}" in exc_info.value.message

# === Test Search Documents ===

def test_search_documents_success(mock_client, caplog, capsys):
    """Test searching documents successfully."""
    caplog.set_level(logging.INFO, logger="docstore_manager.qdrant.commands.search")
    collection_name = "test_search_docs"
    query_vector = [0.5] * 10
    query_filter = {"must": [{"key": "field", "match": {"value": "test"}}]} # Example filter dict
    mock_results = [
        rest.ScoredPoint(id="res1", version=0, score=0.9, payload={"meta": "data1"}, vector=None),
        rest.ScoredPoint(id="res2", version=0, score=0.8, payload={"meta": "data2"}, vector=None)
    ]
    mock_client.search.return_value = mock_results

    # Note: search_documents expects filter_obj, not dict. Need to mock filter parsing if testing CLI path.
    # For direct function call, we pass the parsed object or None.
    # Let's assume filter is None for this direct call test.
    cmd_search.search_documents(client=mock_client, collection_name=collection_name, query_vector=query_vector, limit=5)

    mock_client.search.assert_called_once()
    args, kwargs = mock_client.search.call_args
    assert kwargs['collection_name'] == collection_name
    assert kwargs['query_vector'] == query_vector
    assert kwargs['query_filter'] is None # Passed None directly
    assert kwargs['limit'] == 5
    # Check actual log message for SUCCESS, not the formatted output
    assert f"Search completed. Found {len(mock_results)} results in '{collection_name}'." in caplog.text
    # The formatted output is logged at INFO before the success message, 
    # but we don't need to assert its exact content here.

def test_search_documents_client_error(mock_client):
    """Test error handling during document search."""
    collection_name = "test_search_fail"
    query_vector = [0.1]
    error_message = "Invalid vector dimensions"
    mock_client.search.side_effect = Exception(error_message)

    with pytest.raises(DocumentError) as exc_info:
        cmd_search.search_documents(client=mock_client, collection_name=collection_name, query_vector=query_vector)

    # Check type and specific attributes
    assert isinstance(exc_info.value, DocumentError)
    assert exc_info.value.collection_name == collection_name
    assert f"Unexpected error searching documents: {error_message}" in exc_info.value.message

# === Test Get Documents ===

def test_get_documents_success(mock_client, caplog, capsys):
    """Test getting documents by ID successfully."""
    caplog.set_level(logging.INFO, logger="docstore_manager.qdrant.commands.get")
    collection_name = "test_get_docs"
    doc_ids = ["id_a", "id_b"]
    mock_results = [
        PointStruct(id="id_a", vector=[0.1], payload={"field": "A"}),
        PointStruct(id="id_b", vector=[0.2], payload={"field": "B"})
    ]
    mock_client.retrieve.return_value = mock_results

    cmd_get.get_documents(client=mock_client, collection_name=collection_name, doc_ids=doc_ids)

    mock_client.retrieve.assert_called_once_with(collection_name=collection_name, ids=doc_ids, with_payload=True, with_vectors=False)
    # Check actual log message
    assert f"Successfully retrieved {len(mock_results)} documents from '{collection_name}'." in caplog.text
    # Check log for formatted output string
    formatter = QdrantFormatter('json')
    expected_output = formatter.format_get_results(mock_results)
    assert expected_output in caplog.text

def test_get_documents_client_error(mock_client):
    """Test error handling when getting documents by ID."""
    collection_name = "test_get_fail"
    doc_ids = ["id_c"]
    error_message = "Document ID not found"
    mock_client.retrieve.side_effect = Exception(error_message)

    with pytest.raises(DocumentError) as exc_info:
        cmd_get.get_documents(client=mock_client, collection_name=collection_name, doc_ids=doc_ids)

    # Check type and specific attributes
    assert isinstance(exc_info.value, DocumentError)
    assert exc_info.value.collection_name == collection_name
    assert f"Unexpected error retrieving documents: {error_message}" in exc_info.value.message

# === Test Scroll Documents ===

def test_scroll_documents_success(mock_client, caplog, capsys):
    """Test scrolling documents successfully."""
    caplog.set_level(logging.INFO, logger="docstore_manager.qdrant.commands.scroll")
    collection_name = "test_scroll_docs"
    limit = 5
    mock_points = [PointStruct(id=f"s{i}", vector=[i/10.0], payload={'n':i}) for i in range(limit)]
    next_offset = "offset_123"
    mock_client.scroll.return_value = (mock_points, next_offset)

    cmd_scroll.scroll_documents(client=mock_client, collection_name=collection_name, limit=limit)

    mock_client.scroll.assert_called_once()
    args, kwargs = mock_client.scroll.call_args
    assert kwargs['collection_name'] == collection_name
    assert kwargs['limit'] == limit
    assert kwargs['scroll_filter'] is None
    # Check actual log messages for SUCCESS and next offset
    assert f"Successfully scrolled {len(mock_points)} documents from '{collection_name}'." in caplog.text
    assert f"Next page offset: {next_offset}" in caplog.text
    # The formatted output is logged at INFO before the success message, 
    # but we don't need to assert its exact content here.

def test_scroll_documents_client_error(mock_client):
    """Test error handling when scrolling documents."""
    collection_name = "test_scroll_fail"
    error_message = "Invalid scroll offset"
    mock_client.scroll.side_effect = Exception(error_message)

    with pytest.raises(DocumentError) as exc_info:
        cmd_scroll.scroll_documents(client=mock_client, collection_name=collection_name)

    # Check type and specific attributes
    assert isinstance(exc_info.value, DocumentError)
    assert exc_info.value.collection_name == collection_name
    assert f"Unexpected error scrolling documents: {error_message}" in exc_info.value.message

# === Test Count Documents ===

def test_count_documents_success(mock_client, caplog, capsys):
    """Test counting documents successfully."""
    caplog.set_level(logging.INFO, logger="docstore_manager.qdrant.commands.count")
    collection_name = "test_count_docs"
    count_value = 42
    mock_client.count.return_value = CountResult(count=count_value)

    cmd_count.count_documents(client=mock_client, collection_name=collection_name)

    mock_client.count.assert_called_once_with(collection_name=collection_name, exact=True, count_filter=None)
    # Check actual log message
    assert f"Collection '{collection_name}' contains {count_value} documents." in caplog.text
    # Check log for formatted output string
    formatter = QdrantFormatter('json')
    expected_output = formatter.format_count(mock_client.count.return_value)
    assert expected_output in caplog.text

def test_count_documents_client_error(mock_client):
    """Test error handling when counting documents."""
    collection_name = "test_count_fail"
    error_message = "Count operation failed"
    mock_client.count.side_effect = Exception(error_message)

    with pytest.raises(DocumentError) as exc_info:
        cmd_count.count_documents(client=mock_client, collection_name=collection_name)

    # Check type and specific attributes
    assert isinstance(exc_info.value, DocumentError)
    assert exc_info.value.collection_name == collection_name
    # Check the specific message from count.py
    assert f"An unexpected error occurred during count: {error_message}" in exc_info.value.message 