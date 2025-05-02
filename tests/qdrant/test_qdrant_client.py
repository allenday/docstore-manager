import pytest
from unittest.mock import patch, MagicMock
import uuid
from qdrant_client.http.models import VectorParams, PointStruct, Distance
import qdrant_client.http.models as models # Import models

# Import the class to be tested
from docstore_manager.qdrant.client import QdrantDocumentStore, QdrantClient
# Import relevant exceptions
from docstore_manager.core.exceptions import (
    ConfigurationError, ConnectionError, CollectionError, DocumentError
)

# --- Fixtures ---

@pytest.fixture
def qdrant_store():
    """Provides a QdrantDocumentStore instance for testing."""
    return QdrantDocumentStore()

# --- Test Cases ---

# === Test validate_config ===

def test_validate_config_success_url(qdrant_store):
    """Test validate_config passes with a valid URL."""
    config = {'url': 'http://localhost:6333'}
    try:
        qdrant_store.validate_config(config)
    except ConfigurationError as e:
        pytest.fail(f"validate_config raised ConfigurationError unexpectedly: {e}")

def test_validate_config_success_host_port(qdrant_store):
    """Test validate_config passes with host and port."""
    config = {'host': 'localhost', 'port': 6333}
    try:
        qdrant_store.validate_config(config)
    except ConfigurationError as e:
        pytest.fail(f"validate_config raised ConfigurationError unexpectedly: {e}")

def test_validate_config_success_cloud(qdrant_store):
    """Test validate_config passes with cloud URL and API key."""
    config = {'cloud_url': 'https://xyz.qdrant.cloud', 'api_key': 'testkey'}
    try:
        qdrant_store.validate_config(config)
    except ConfigurationError as e:
        pytest.fail(f"validate_config raised ConfigurationError unexpectedly: {e}")

def test_validate_config_failure_missing_all(qdrant_store):
    """Test validate_config fails when no connection info is provided."""
    config = {'some_other_key': 'value'}
    with pytest.raises(ConfigurationError, match="Connection configuration is missing."):
        qdrant_store.validate_config(config)

def test_validate_config_failure_missing_port(qdrant_store):
    """Test validate_config fails when host is provided but port is missing."""
    config = {'host': 'localhost'}
    with pytest.raises(ConfigurationError, match="Both host and port must be provided"):
        qdrant_store.validate_config(config)

def test_validate_config_failure_missing_host(qdrant_store):
    """Test validate_config fails when port is provided but host is missing."""
    config = {'port': 6333}
    with pytest.raises(ConfigurationError, match="Both host and port must be provided"):
        qdrant_store.validate_config(config)

def test_validate_config_failure_missing_cloud_key(qdrant_store):
    """Test validate_config fails when cloud_url is provided but api_key is missing."""
    config = {'cloud_url': 'https://xyz.qdrant.cloud'}
    # Use regex= instead of match= for potentially multiline errors or complex matching
    with pytest.raises(ConfigurationError, 
                       match="Both cloud_url and api_key must be provided for Cloud connection."):
        qdrant_store.validate_config(config)

def test_validate_config_failure_missing_cloud_url(qdrant_store):
    """Test validate_config fails when api_key is provided but cloud_url is missing."""
    config = {'api_key': 'testkey'}
    with pytest.raises(ConfigurationError, 
                       match="Both cloud_url and api_key must be provided for Cloud connection."):
        qdrant_store.validate_config(config)

def test_validate_config_prefer_url(qdrant_store):
    """Test validate_config uses url even if host/port/cloud are present."""
    config = {
        'url': 'http://main-url:6333',
        'host': 'other-host',
        'port': 1234,
        'cloud_url': 'https://cloud.xyz',
        'api_key': 'cloudkey'
    }
    try:
        # Should not raise error if url is valid
        qdrant_store.validate_config(config)
    except ConfigurationError as e:
        pytest.fail(f"validate_config raised ConfigurationError unexpectedly: {e}")

def test_validate_config_prefer_host_port(qdrant_store):
    """Test validate_config uses host/port if url is absent but cloud is present."""
    config = {
        'host': 'main-host',
        'port': 6333,
        'cloud_url': 'https://cloud.xyz',
        'api_key': 'cloudkey'
    }
    try:
        # Should not raise error if host/port are valid
        qdrant_store.validate_config(config)
    except ConfigurationError as e:
        pytest.fail(f"validate_config raised ConfigurationError unexpectedly: {e}")

# === Test create_client ===

def test_create_client_success_url(qdrant_store):
    """Test create_client successful with URL (manual patch via class globals)."""
    config = {
        'url': 'http://test-url:6333',
        'api_key': 'test-key',
        'prefer_grpc': False
    }
    mock_client_instance = MagicMock()
    mock_local_qdrant_client = MagicMock(return_value=mock_client_instance)

    # Manual patch
    method_to_patch = QdrantDocumentStore.create_client
    method_globals = method_to_patch.__globals__
    original_qdrant_client = method_globals.get('QdrantClient')
    if original_qdrant_client is None: pytest.fail("Could not find QdrantClient in globals")
    method_globals['QdrantClient'] = mock_local_qdrant_client

    try:
        client = qdrant_store.create_client(config)

        assert client == mock_client_instance
        mock_local_qdrant_client.assert_called_once_with(
            url=config['url'],
            api_key=config['api_key'],
            prefer_grpc=config['prefer_grpc']
        )
    finally:
        if original_qdrant_client: method_globals['QdrantClient'] = original_qdrant_client

def test_create_client_success_host_port(qdrant_store):
    """Test create_client successful with host/port (manual patch via class globals)."""
    # NOTE: QdrantDocumentStore.create_client now handles host/port
    config = {
        'host': 'test-host',
        'port': 1234,
        'api_key': 'test-key'
    }
    mock_client_instance = MagicMock()
    mock_local_qdrant_client = MagicMock(return_value=mock_client_instance)

    # Manual patch
    method_to_patch = QdrantDocumentStore.create_client
    method_globals = method_to_patch.__globals__
    original_qdrant_client = method_globals.get('QdrantClient')
    if original_qdrant_client is None: pytest.fail("Could not find QdrantClient in globals")
    method_globals['QdrantClient'] = mock_local_qdrant_client

    try:
        client = qdrant_store.create_client(config)
        assert client == mock_client_instance
        # Assert URL is constructed correctly
        mock_local_qdrant_client.assert_called_once_with(
            url=f"http://{config['host']}:{config['port']}",
            api_key=config['api_key'],
            prefer_grpc=True # Default
        )
    finally:
        if original_qdrant_client: method_globals['QdrantClient'] = original_qdrant_client

def test_create_client_success_cloud(qdrant_store):
    """Test create_client successful with cloud URL/key (manual patch via class globals)."""
    config = {
        'cloud_url': 'https://test-cloud.qdrant.cloud',
        'api_key': 'cloud-api-key'
    }
    mock_client_instance = MagicMock()
    mock_local_qdrant_client = MagicMock(return_value=mock_client_instance)

    # Manual patch
    method_to_patch = QdrantDocumentStore.create_client
    method_globals = method_to_patch.__globals__
    original_qdrant_client = method_globals.get('QdrantClient')
    if original_qdrant_client is None: pytest.fail("Could not find QdrantClient in globals")
    method_globals['QdrantClient'] = mock_local_qdrant_client

    try:
        client = qdrant_store.create_client(config)
        assert client == mock_client_instance
        # Assert cloud_url is passed as url
        mock_local_qdrant_client.assert_called_once_with(
            url=config['cloud_url'],
            api_key=config['api_key'],
            prefer_grpc=True # Default
        )
    finally:
        if original_qdrant_client: method_globals['QdrantClient'] = original_qdrant_client

def test_create_client_default_grpc(qdrant_store):
    """Test create_client uses prefer_grpc=True by default (manual patch via class globals)."""
    config = {'url': 'http://localhost:6333'}
    mock_client_instance = MagicMock()
    mock_local_qdrant_client = MagicMock(return_value=mock_client_instance)

    # Manual patch
    method_to_patch = QdrantDocumentStore.create_client
    method_globals = method_to_patch.__globals__
    original_qdrant_client = method_globals.get('QdrantClient')
    if original_qdrant_client is None: pytest.fail("Could not find QdrantClient in globals")
    method_globals['QdrantClient'] = mock_local_qdrant_client

    try:
        qdrant_store.create_client(config)
        mock_local_qdrant_client.assert_called_once_with(
            url=config['url'],
            api_key=None,
            prefer_grpc=True
        )
    finally:
        if original_qdrant_client: method_globals['QdrantClient'] = original_qdrant_client

def test_create_client_connection_error(qdrant_store):
    """Test create_client wraps exceptions in ConnectionError (manual patch via class globals)."""
    config = {'url': 'http://invalid-url'}
    original_exception = ValueError("Qdrant client init failed")
    mock_local_qdrant_client = MagicMock(side_effect=original_exception)

    # Manual patch
    method_to_patch = QdrantDocumentStore.create_client
    method_globals = method_to_patch.__globals__
    original_qdrant_client = method_globals.get('QdrantClient')
    if original_qdrant_client is None: pytest.fail("Could not find QdrantClient in globals")
    method_globals['QdrantClient'] = mock_local_qdrant_client

    try:
        with pytest.raises(ConnectionError) as excinfo:
            qdrant_store.create_client(config)
        
        assert str(original_exception) in str(excinfo.value)
        mock_local_qdrant_client.assert_called_once_with(
            url=config['url'], 
            api_key=None, 
            prefer_grpc=True
        )
    finally:
        if original_qdrant_client: method_globals['QdrantClient'] = original_qdrant_client

# === Tests for validate_connection ===

def test_validate_connection_success(mocker):
    """Test validate_connection success."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    mock_client.get_collections.return_value = mocker.MagicMock() # Simulate successful call

    store = QdrantDocumentStore()
    assert store.validate_connection(mock_client) is True
    mock_client.get_collections.assert_called_once()

def test_validate_connection_failure(mocker):
    """Test validate_connection failure."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    mock_client.get_collections.side_effect = Exception("Simulated connection error")

    store = QdrantDocumentStore()
    assert store.validate_connection(mock_client) is False
    mock_client.get_collections.assert_called_once()

# === Tests for close ===

def test_close_success(mocker):
    """Test close method successfully calls client.close()."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    mock_client.close.return_value = None # Simulate successful close

    store = QdrantDocumentStore()
    store.close(mock_client)

    mock_client.close.assert_called_once()

def test_close_exception(mocker):
    """Test close method handles exceptions from client.close() gracefully."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    mock_client.close.side_effect = Exception("Simulated close error")

    store = QdrantDocumentStore()
    try:
        store.close(mock_client)
    except Exception as e:
        pytest.fail(f"store.close raised an unexpected exception: {e}")

    mock_client.close.assert_called_once()

# === Tests for get_collections ===

def test_get_collections_success(qdrant_store, mocker):
    """Test get_collections successfully retrieves and formats collection names."""
    # Mock the client instance on the store
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client

    # Mock the response from client.get_collections()
    mock_collection1 = mocker.MagicMock()
    mock_collection1.name = "collection1"
    mock_collection2 = mocker.MagicMock()
    mock_collection2.name = "collection2"
    mock_response = mocker.MagicMock()
    mock_response.collections = [mock_collection1, mock_collection2]
    mock_client.get_collections.return_value = mock_response

    collections = qdrant_store.get_collections()

    assert collections == [{"name": "collection1"}, {"name": "collection2"}]
    mock_client.get_collections.assert_called_once()

def test_get_collections_failure(qdrant_store, mocker):
    """Test get_collections raises CollectionError on client exception."""
    # Mock the client instance on the store
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client

    # Mock the client call to raise an exception
    original_exception = Exception("Simulated client error")
    mock_client.get_collections.side_effect = original_exception

    with pytest.raises(CollectionError) as excinfo:
        qdrant_store.get_collections()
    
    assert "Failed to list collections" in str(excinfo.value)
    assert str(original_exception) in str(excinfo.value)
    mock_client.get_collections.assert_called_once()

# === Tests for create_collection ===

def test_create_collection_success(qdrant_store, mocker):
    """Test create_collection successfully calls client.recreate_collection."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client

    collection_name = "test-collection"
    vector_params = VectorParams(size=10, distance=Distance.COSINE)
    on_disk_payload = True

    qdrant_store.create_collection(collection_name, vector_params, on_disk_payload)

    mock_client.recreate_collection.assert_called_once_with(
        collection_name=collection_name,
        vectors_config=vector_params,
        on_disk_payload=on_disk_payload
    )

def test_create_collection_failure(qdrant_store, mocker):
    """Test create_collection raises CollectionError on client exception."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client

    collection_name = "test-collection"
    vector_params = VectorParams(size=10, distance=Distance.COSINE)
    original_exception = Exception("Simulated recreate error")
    mock_client.recreate_collection.side_effect = original_exception

    with pytest.raises(CollectionError) as excinfo:
        qdrant_store.create_collection(collection_name, vector_params)

    assert f"Failed to create collection: {str(original_exception)}" in str(excinfo.value)
    mock_client.recreate_collection.assert_called_once_with(
        collection_name=collection_name,
        vectors_config=vector_params,
        on_disk_payload=False # Default value when not provided
    )

# === Tests for delete_collection ===

def test_delete_collection_success(qdrant_store, mocker):
    """Test delete_collection successfully calls client.delete_collection."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client
    collection_name = "test-to-delete"

    qdrant_store.delete_collection(collection_name)

    mock_client.delete_collection.assert_called_once_with(collection_name=collection_name)

def test_delete_collection_failure(qdrant_store, mocker):
    """Test delete_collection raises CollectionError on client exception."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client
    collection_name = "test-fail-delete"
    original_exception = Exception("Simulated delete error")
    mock_client.delete_collection.side_effect = original_exception

    with pytest.raises(CollectionError) as excinfo:
        qdrant_store.delete_collection(collection_name)

    assert f"Failed to delete collection: {str(original_exception)}" in str(excinfo.value)
    mock_client.delete_collection.assert_called_once_with(collection_name=collection_name)

# === Tests for get_collection ===

def test_get_collection_success(qdrant_store, mocker):
    """Test get_collection successfully retrieves and formats collection details."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client
    collection_name = "test-get-collection"

    # Mock the detailed response structure from client.get_collection
    mock_response = mocker.MagicMock()
    mock_response.config.params.vectors.size = 128
    mock_response.config.params.vectors.distance = Distance.EUCLID
    mock_response.points_count = 1000
    mock_response.config.params.on_disk_payload = False
    mock_client.get_collection.return_value = mock_response

    collection_info = qdrant_store.get_collection(collection_name)

    expected_info = {
        "name": collection_name,
        "vectors": {
            "size": 128,
            "distance": Distance.EUCLID
        },
        "points_count": 1000,
        "on_disk_payload": False
    }
    assert collection_info == expected_info
    mock_client.get_collection.assert_called_once_with(collection_name=collection_name)

def test_get_collection_failure(qdrant_store, mocker):
    """Test get_collection raises CollectionError on client exception."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client
    collection_name = "test-fail-get"
    original_exception = Exception("Simulated get error")
    mock_client.get_collection.side_effect = original_exception

    with pytest.raises(CollectionError) as excinfo:
        qdrant_store.get_collection(collection_name)

    assert f"Failed to get collection: {str(original_exception)}" in str(excinfo.value)
    mock_client.get_collection.assert_called_once_with(collection_name=collection_name)

# === Tests for add_documents ===

def test_add_documents_success_single_batch(qdrant_store, mocker):
    """Test add_documents successfully uploads points in a single batch."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client
    collection_name = "test-add-docs"

    # Create some sample points (less than default batch size 100)
    points = [
        PointStruct(id=str(uuid.uuid4()), vector=[0.1, 0.2], payload={"doc": 1}),
        PointStruct(id=str(uuid.uuid4()), vector=[0.3, 0.4], payload={"doc": 2})
    ]

    qdrant_store.add_documents(collection_name, points)

    mock_client.upsert.assert_called_once_with(
        collection_name=collection_name,
        points=points # The whole list since it's one batch
    )

def test_add_documents_success_multiple_batches(qdrant_store, mocker):
    """Test add_documents correctly handles multiple batches."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client
    collection_name = "test-add-docs-multi"
    batch_size = 5 # Use a small batch size for testing

    # Create points exceeding batch size (e.g., 7 points for batch size 5)
    points = [PointStruct(id=str(uuid.uuid4()), vector=[i/10, (i+1)/10]) for i in range(7)]

    qdrant_store.add_documents(collection_name, points, batch_size=batch_size)

    # Check that upsert was called twice
    assert mock_client.upsert.call_count == 2

    # Check the first call (first batch_size points)
    mock_client.upsert.assert_any_call(
        collection_name=collection_name,
        points=points[:batch_size]
    )
    # Check the second call (remaining points)
    mock_client.upsert.assert_any_call(
        collection_name=collection_name,
        points=points[batch_size:]
    )

def test_add_documents_failure(qdrant_store, mocker):
    """Test add_documents raises DocumentError on client upsert exception."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client
    collection_name = "test-fail-add"

    points = [PointStruct(id=str(uuid.uuid4()), vector=[0.1, 0.2])]
    original_exception = Exception("Simulated upsert error")
    mock_client.upsert.side_effect = original_exception

    with pytest.raises(DocumentError) as excinfo:
        qdrant_store.add_documents(collection_name, points)

    assert f"Failed to add documents: {str(original_exception)}" in str(excinfo.value)
    # assert excinfo.value.collection_name == collection_name # DocumentError has collection_name
    mock_client.upsert.assert_called_once_with(
        collection_name=collection_name,
        points=points
    )

# === Tests for delete_documents ===

def test_delete_documents_success(qdrant_store, mocker):
    """Test delete_documents successfully calls client.delete with correct PointIdsList."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client
    collection_name = "test-delete-docs"
    doc_ids = [str(uuid.uuid4()), str(uuid.uuid4())]

    qdrant_store.delete_documents(collection_name, doc_ids)

    # Check that delete was called with the correct PointIdsList
    mock_client.delete.assert_called_once()
    call_args = mock_client.delete.call_args
    assert call_args.kwargs["collection_name"] == collection_name
    assert isinstance(call_args.kwargs["points_selector"], models.PointIdsList)
    assert call_args.kwargs["points_selector"].points == doc_ids

def test_delete_documents_failure(qdrant_store, mocker):
    """Test delete_documents raises DocumentError on client delete exception."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client
    collection_name = "test-fail-delete-docs"
    doc_ids = [str(uuid.uuid4())]
    original_exception = Exception("Simulated delete error")
    mock_client.delete.side_effect = original_exception

    with pytest.raises(DocumentError) as excinfo:
        qdrant_store.delete_documents(collection_name, doc_ids)

    assert f"Failed to delete documents: {str(original_exception)}" in str(excinfo.value)
    # assert excinfo.value.collection_name == collection_name # DocumentError has collection_name

    # Check that delete was still called once with the correct args before exception
    mock_client.delete.assert_called_once()
    call_args = mock_client.delete.call_args
    assert call_args.kwargs["collection_name"] == collection_name
    assert isinstance(call_args.kwargs["points_selector"], models.PointIdsList)
    assert call_args.kwargs["points_selector"].points == doc_ids

# === Tests for search_documents ===

def test_search_documents_success(qdrant_store, mocker):
    """Test search_documents successfully calls client.search and formats results."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client
    collection_name = "test-search-docs"
    query_vector = [0.5, 0.6]
    limit = 5

    # Mock the response from client.search()
    mock_hit1 = models.ScoredPoint(id=str(uuid.uuid4()), version=0, score=0.9, vector=[0.51, 0.61], payload={"text": "doc1"})
    mock_hit2 = models.ScoredPoint(id=str(uuid.uuid4()), version=0, score=0.8, vector=[0.52, 0.62], payload={"text": "doc2", "meta": "data"})
    mock_client.search.return_value = [mock_hit1, mock_hit2]

    search_query = {"vector": query_vector}
    results = qdrant_store.search_documents(collection_name, search_query, limit=limit)

    expected_results = [
        {
            "id": mock_hit1.id,
            "score": mock_hit1.score,
            "vector": mock_hit1.vector,
            "text": "doc1"
        },
        {
            "id": mock_hit2.id,
            "score": mock_hit2.score,
            "vector": mock_hit2.vector,
            "text": "doc2",
            "meta": "data"
        }
    ]
    assert results == expected_results
    mock_client.search.assert_called_once_with(
        collection_name=collection_name,
        query_vector=query_vector,
        query_filter=None, # Default when not provided in query dict
        limit=limit
    )

def test_search_documents_failure(qdrant_store, mocker):
    """Test search_documents raises DocumentError on client search exception."""
    mock_client = mocker.MagicMock(spec=QdrantClient)
    qdrant_store.client = mock_client
    collection_name = "test-fail-search"
    query_vector = [0.1, 0.9]
    limit = 10
    original_exception = Exception("Simulated search error")
    mock_client.search.side_effect = original_exception

    search_query = {"vector": query_vector}
    with pytest.raises(DocumentError) as excinfo:
        qdrant_store.search_documents(collection_name, search_query, limit=limit)

    assert f"Failed to search documents: {str(original_exception)}" in str(excinfo.value)
    # assert excinfo.value.collection_name == collection_name # Check collection name
    mock_client.search.assert_called_once_with(
        collection_name=collection_name,
        query_vector=query_vector,
        query_filter=None,
        limit=limit
    )

# === TODO: Add tests for get_document_count ===
# === TODO: Add tests for scroll_documents ===

# Removed extraneous tag

# === TODO: Add tests for get_document_count ===
# === TODO: Add tests for scroll_documents === 