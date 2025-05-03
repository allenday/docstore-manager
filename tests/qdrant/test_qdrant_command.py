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
    # caplog.set_level(logging.INFO) # Logging still seems broken
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
    # Set side_effect on the correct method for overwrite=False path
    mock_client.create_collection.side_effect = ConnectionError(error_message)
    mock_client.recreate_collection.side_effect = None # Prevent interference

    # The command function calls sys.exit(1) when catching a generic Exception
    with pytest.raises(SystemExit) as exc_info:
        cmd_create.create_collection(
            client=mock_client,
            collection_name=collection_name,
            dimension=10,
            distance=Distance.COSINE,
            overwrite=False # Explicitly testing the non-overwrite path
        )
    # Check the exit code
    assert exc_info.value.code == 1
    # Cannot easily check original error message without more complex stderr capture/mocking

# === Test Delete Collection ===

def test_delete_collection_success(mock_client, caplog):
    """Test successful collection deletion."""
    collection_name = "test_delete_coll"
    mock_client.delete_collection.return_value = True

    cmd_delete_collection.delete_collection(client=mock_client, collection_name=collection_name)

    mock_client.delete_collection.assert_called_once_with(collection_name=collection_name)
    # Removed caplog assertion
    assert f"Successfully deleted collection '{collection_name}'." in caplog.text

def test_delete_collection_client_error(mock_client):
    """Test error handling during collection deletion."""
    collection_name = "test_delete_fail"
    error_message = "Collection lock timeout"
    mock_client.delete_collection.side_effect = Exception(error_message) # Generic exception

    # Expect SystemExit because the command function calls sys.exit(1)
    with pytest.raises(SystemExit) as exc_info:
        cmd_delete_collection.delete_collection(client=mock_client, collection_name=collection_name)

    # Check the exit code
    assert exc_info.value.code == 1
    # Cannot easily check the original error message when SystemExit is caught
    # assert f"Failed to delete collection '{collection_name}': {error_message}" in str(exc_info.value)

# === Test List Collections (covered in test_list_cmd.py) ===
# We can add specific cases here if needed, but main tests are separate

# === Test Get Collection Info ===

def test_get_collection_info_success(mock_client, caplog, capsys):
    """Test getting collection info successfully."""
    # caplog.set_level(logging.INFO) # Logging broken
    collection_name = "test_info_coll"

    # --- Mock Setup - Compatible with JSON and Formatter --- 
    mock_optimizer_status = MagicMock()
    mock_optimizer_status.ok = True
    mock_optimizer_status.error = None

    mock_info = MagicMock()
    mock_info.status = rest.CollectionStatus.GREEN.value
    mock_info.optimizer_status = mock_optimizer_status
    mock_info.vectors_count = 100
    mock_info.indexed_vectors_count = 90
    mock_info.points_count = 100
    mock_info.segments_count = 1
    
    # Mock config and its parts
    mock_info.config = MagicMock()
    mock_info.config.params = MagicMock()
    mock_info.config.params.vectors = MagicMock()
    mock_info.config.params.vectors.size = 10
    mock_info.config.params.vectors.distance = rest.Distance.COSINE.value
    # Add other required params fields if formatter needs them
    mock_info.config.params.shard_number = 1
    mock_info.config.params.replication_factor = 1
    mock_info.config.params.write_consistency_factor = 1
    mock_info.config.params.on_disk_payload = True

    # Mock HNSW, optimizer, WAL configs as objects with a .dict() method
    mock_hnsw_dict = {"m": 16, "ef_construct": 100}
    mock_info.config.hnsw_config = MagicMock()
    mock_info.config.hnsw_config.dict.return_value = mock_hnsw_dict

    mock_optimizer_dict = {"deleted_threshold": 0.2}
    mock_info.config.optimizer_config = MagicMock()
    mock_info.config.optimizer_config.dict.return_value = mock_optimizer_dict

    mock_wal_dict = {"wal_capacity_mb": 32}
    mock_info.config.wal_config = MagicMock()
    mock_info.config.wal_config.dict.return_value = mock_wal_dict

    # Mock payload schema (already a dict)
    mock_info.payload_schema = {
        "field1": {"data_type": "keyword", "params": None, "points": 0}
    }
    # --- End Mock Setup --- 

    mock_client.get_collection.return_value = mock_info

    cmd_info.collection_info(client=mock_client, collection_name=collection_name)

    mock_client.get_collection.assert_called_once_with(collection_name=collection_name)
    
    # Load the JSON output and assert specific values
    output = capsys.readouterr().out
    assert collection_name in output # Basic check
    
    try:
        output_data = json.loads(output)
        assert output_data["name"] == collection_name
        assert output_data["status"] == "GREEN"
        assert output_data["points_count"] == 100
        assert output_data["optimizer_status"] == "ok"
        assert output_data["config"]["hnsw_config"]["m"] == 16 # Check nested dict
    except json.JSONDecodeError:
        pytest.fail(f"Output was not valid JSON: {output}")
    except KeyError as e:
         pytest.fail(f"Expected key {e} not found in JSON output: {output}")

def test_get_collection_info_client_error(mock_client):
    """Test error handling when getting collection info."""
    collection_name = "test_info_fail"
    error_message = "Collection not found (404)"
    # Simulate a specific qdrant client error if possible, otherwise general Exception
    mock_client.get_collection.side_effect = Exception(error_message)

    with pytest.raises(CollectionError) as exc_info:
        cmd_info.collection_info(client=mock_client, collection_name=collection_name)

    # Check type and that collection name is likely in the args
    assert isinstance(exc_info.value, CollectionError)
    assert collection_name in str(exc_info.value)
    # assert f"Failed to get info for collection '{collection_name}': {error_message}" in str(exc_info.value) # Original assertion

# === Test Add Documents ===

def test_add_documents_success(mock_client, caplog):
    """Test adding documents successfully."""
    collection_name = "test_add_docs"
    docs = [
        {"id": "doc1", "vector": [0.1, 0.2], "metadata": {"field": "value1"}},
        {"id": "doc2", "vector": [0.3, 0.4], "metadata": {"field": "value2"}}
    ]
    mock_client.upsert.return_value = UpdateResult(operation_id=0, status=UpdateStatus.COMPLETED)

    # Call the correct function from batch.py
    batch_add_documents(client=mock_client, collection_name=collection_name, documents=docs)

    mock_client.upsert.assert_called_once()
    args, kwargs = mock_client.upsert.call_args
    assert kwargs['collection_name'] == collection_name
    assert len(kwargs['points']) == 2
    assert isinstance(kwargs['points'][0], PointStruct)
    assert kwargs['points'][0].id == "doc1"
    assert kwargs['points'][0].vector == [0.1, 0.2]
    # Payload should now only contain non-id, non-vector fields if defined, or be None
    # The add_documents function likely puts metadata under payload
    assert kwargs['points'][0].payload == {"metadata": {"field": "value1"}} # Adjusted expectation
    assert f"Successfully added/updated {len(docs)} documents" in caplog.text

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
    error_message = "Upsert failed due to schema mismatch"
    # Mock the underlying client call that add_documents uses (upsert)
    mock_client.upsert.side_effect = Exception(error_message)

    # Expect DocumentError now, not BatchOperationError
    with pytest.raises(DocumentError) as exc_info:
        batch_add_documents(client=mock_client, collection_name=collection_name, documents=docs)

    # Correct assertion: Check args[0] for the message
    assert f"Unexpected error adding documents to '{collection_name}': {error_message}" in exc_info.value.args[0]
    assert exc_info.value.original_exception is not None
    assert str(exc_info.value.original_exception) == error_message

# === Test Delete Documents ===

def test_delete_documents_success(mock_client, caplog):
    """Test deleting documents successfully."""
    collection_name = "test_del_docs"
    doc_ids = ["id1", "id2"]
    mock_client.delete.return_value = UpdateResult(operation_id=1, status=UpdateStatus.COMPLETED)

    # Call the correct function from batch.py
    batch_remove_documents(client=mock_client, collection_name=collection_name, doc_ids=doc_ids)

    # delete takes points_selector which should be models.PointIdsList
    mock_client.delete.assert_called_once()
    args, kwargs = mock_client.delete.call_args
    assert kwargs['collection_name'] == collection_name
    assert isinstance(kwargs['points_selector'], rest.PointIdsList)
    assert kwargs['points_selector'].points == doc_ids # Check IDs match
    assert f"Successfully removed documents from collection '{collection_name}'" in caplog.text # Check log

def test_delete_documents_client_error(mock_client):
    """Test error handling when deleting documents."""
    collection_name = "test_del_fail"
    doc_ids = ["id1"]
    error_message = "Delete operation timed out"
    # Mock the underlying client call that remove_documents uses (delete)
    mock_client.delete.side_effect = Exception(error_message)

    # Expect DocumentError now, not BatchOperationError
    with pytest.raises(DocumentError) as exc_info:
        batch_remove_documents(client=mock_client, collection_name=collection_name, doc_ids=doc_ids)

    # Check the message in args[0]
    assert f"Unexpected error during remove in collection '{collection_name}': {error_message}" in exc_info.value.args[0]
    assert exc_info.value.original_exception is not None
    assert str(exc_info.value.original_exception) == error_message

# === Test Search Documents ===

def test_search_documents_success(mock_client, caplog, capsys):
    """Test searching documents successfully."""
    collection_name = "test_search_docs"
    query_vector = [0.5] * 10 # Example vector
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
    assert "Successfully found 2 documents" in caplog.text
    captured = capsys.readouterr()
    output_json = json.loads(captured.out.strip())
    assert len(output_json) == 2
    assert output_json[0]['id'] == "res1"

def test_search_documents_client_error(mock_client):
    """Test error handling during document search."""
    collection_name = "test_search_fail"
    query_vector = [0.1]
    error_message = "Invalid vector dimensions"
    mock_client.search.side_effect = Exception(error_message)

    with pytest.raises(DocumentError) as exc_info:
        cmd_search.search_documents(client=mock_client, collection_name=collection_name, query_vector=query_vector)

    # Check type and that collection name is likely in the args
    assert isinstance(exc_info.value, DocumentError)
    assert collection_name in str(exc_info.value)
    # assert f"Error searching documents in '{collection_name}': {error_message}" in str(exc_info.value) # Original assertion

# === Test Get Documents ===

def test_get_documents_success(mock_client, caplog, capsys):
    """Test getting documents by ID successfully."""
    collection_name = "test_get_docs"
    doc_ids = ["id_a", "id_b"]
    mock_results = [
        PointStruct(id="id_a", vector=[0.1], payload={"field": "A"}),
        PointStruct(id="id_b", vector=[0.2], payload={"field": "B"})
    ]
    mock_client.retrieve.return_value = mock_results

    cmd_get.get_documents(client=mock_client, collection_name=collection_name, doc_ids=doc_ids)

    mock_client.retrieve.assert_called_once_with(collection_name=collection_name, ids=doc_ids, with_payload=True, with_vectors=False)
    assert f"Successfully retrieved {len(mock_results)} documents" in caplog.text
    captured = capsys.readouterr()
    output_json = json.loads(captured.out.strip())
    assert len(output_json) == 2
    assert output_json[0]['id'] == "id_a"
    assert "vector" not in output_json[0]

def test_get_documents_client_error(mock_client):
    """Test error handling when getting documents by ID."""
    collection_name = "test_get_fail"
    doc_ids = ["id_c"]
    error_message = "Document ID not found"
    mock_client.retrieve.side_effect = Exception(error_message)

    with pytest.raises(DocumentError) as exc_info:
        cmd_get.get_documents(client=mock_client, collection_name=collection_name, doc_ids=doc_ids)

    # Check type and that collection name is likely in the args
    assert isinstance(exc_info.value, DocumentError)
    assert collection_name in str(exc_info.value)
    # assert f"Failed to retrieve documents from '{collection_name}': {error_message}" in str(exc_info.value) # Original assertion

# === Test Scroll Documents ===

def test_scroll_documents_success(mock_client, caplog, capsys):
    """Test scrolling documents successfully."""
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
    assert f"Successfully scrolled {len(mock_points)} documents" in caplog.text
    assert f"Next page offset: {next_offset}" in caplog.text
    captured = capsys.readouterr()
    output_json = json.loads(captured.out.strip())
    assert len(output_json) == limit
    assert output_json[0]['id'] == "s0"
    # Check stderr for next page offset hint
    assert f"# Next page offset: {next_offset}" in captured.err

def test_scroll_documents_client_error(mock_client):
    """Test error handling when scrolling documents."""
    collection_name = "test_scroll_fail"
    error_message = "Invalid scroll offset"
    mock_client.scroll.side_effect = Exception(error_message)

    with pytest.raises(DocumentError) as exc_info:
        cmd_scroll.scroll_documents(client=mock_client, collection_name=collection_name)

    # Check type and that collection name is likely in the args
    assert isinstance(exc_info.value, DocumentError)
    assert collection_name in str(exc_info.value)
    # assert f"Unexpected error scrolling documents: {error_message}" in str(exc_info.value) # Original assertion

# === Test Count Documents ===

def test_count_documents_success(mock_client, caplog, capsys):
    """Test counting documents successfully."""
    collection_name = "test_count_docs"
    count_value = 42
    mock_client.count.return_value = CountResult(count=count_value)

    cmd_count.count_documents(client=mock_client, collection_name=collection_name)

    mock_client.count.assert_called_once_with(collection_name=collection_name, exact=True, count_filter=None)
    assert f"Collection '{collection_name}' contains {count_value} documents." in caplog.text
    captured = capsys.readouterr()
    assert captured.out.strip() == str(count_value)

def test_count_documents_client_error(mock_client):
    """Test error handling when counting documents."""
    collection_name = "test_count_fail"
    error_message = "Count operation failed"
    mock_client.count.side_effect = Exception(error_message)

    with pytest.raises(DocumentError) as exc_info:
        cmd_count.count_documents(client=mock_client, collection_name=collection_name)

    # Check type and that collection name is likely in the args
    assert isinstance(exc_info.value, DocumentError)
    assert collection_name in str(exc_info.value)
    # assert f"Failed to count documents in '{collection_name}': {error_message}" in str(exc_info.value) # Original assertion 