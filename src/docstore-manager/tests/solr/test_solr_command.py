"""Tests for the Solr command module."""
import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace

from docstore_manager.solr.command import SolrCommand
from docstore_manager.core.exceptions import ConfigurationError, CollectionError, DocumentError

@pytest.fixture
def command():
    """Create a SolrCommand instance."""
    return SolrCommand(solr_url="http://localhost:8983/solr")

@pytest.fixture
def mock_args():
    """Create mock command line arguments."""
    return Namespace(
        collection="test_collection",
        name="test_collection",
        num_shards=1,
        replication_factor=1,
        configset="default",
        overwrite=False,
        output=None,
        format="json"
    )

def test_command_initialization():
    """Test command initialization."""
    cmd = SolrCommand(solr_url="http://localhost:8983/solr")
    assert cmd.solr_url == "http://localhost:8983/solr"
    assert cmd.zk_hosts is None

    cmd = SolrCommand(solr_url="http://localhost:8983/solr", zk_hosts="zk1:2181,zk2:2181/solr")
    assert cmd.solr_url == "http://localhost:8983/solr"
    assert cmd.zk_hosts == "zk1:2181,zk2:2181/solr"

def test_command_initialization_error():
    """Test command initialization error."""
    with pytest.raises(TypeError) as exc_info:
        SolrCommand()
    assert "missing 1 required positional argument: 'solr_url'" in str(exc_info.value)

def test_create_collection(command):
    """Test create collection."""
    with patch("requests.get") as mock_request:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        response = command.create_collection("test_collection", numShards=1, replicationFactor=1, config_set="_default")
        assert response.success
        assert "test_collection" in response.message
        assert response.data == {"name": "test_collection"}

def test_delete_collection(command):
    """Test delete collection."""
    with patch("requests.get") as mock_request:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        response = command.delete_collection("test_collection")
        assert response.success
        assert "test_collection" in response.message

def test_list_collections(command):
    """Test list collections."""
    with patch("requests.get") as mock_request:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"collections": ["coll1", "coll2"]}
        mock_request.return_value = mock_response
        
        response = command.list_collections()
        assert response.success
        assert response.data == ["coll1", "coll2"]

def test_get_collection_info(command):
    """Test get collection info."""
    with patch("requests.get") as mock_request:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "cluster": {
                "collections": {
                    "test_collection": {"config": "test_config"}
                }
            }
        }
        mock_request.return_value = mock_response
        
        response = command.get_collection_info("test_collection")
        assert response.success
        assert response.data == {"config": "test_config"}

def test_add_documents(command):
    """Test add documents."""
    docs = [{"id": "1", "field": "value"}]
    with patch("docstore_manager.solr.command.SolrCommand._get_core") as mock_get_core:
        mock_solr = MagicMock()
        mock_get_core.return_value = mock_solr
        
        response = command.add_documents("test_collection", docs, batch_size=100)
        assert response.success
        assert response.data == {"count": 1}
        mock_solr.add.assert_called_once_with(docs)
        mock_solr.commit.assert_called_once()

def test_delete_documents(command):
    """Test delete documents."""
    ids = ["1", "2", "3"]
    with patch("docstore_manager.solr.command.SolrCommand._get_core") as mock_get_core:
        mock_solr = MagicMock()
        mock_get_core.return_value = mock_solr
        
        response = command.delete_documents("test_collection", ids=ids)
        assert response.success
        mock_solr.delete.assert_called_once_with(id=ids)

def test_get_documents(command):
    """Test get documents."""
    ids = ["1", "2", "3"]
    with patch("docstore_manager.solr.command.SolrCommand._get_core") as mock_get_core:
        mock_solr = MagicMock()
        mock_docs = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        # Create mock Solr documents that behave like dictionaries
        class MockSolrDoc:
            def __init__(self, doc):
                self._doc = doc
            def __iter__(self):
                return iter(self._doc.items())
            def items(self):
                return self._doc.items()
            def __getitem__(self, key):
                return self._doc[key]
            def __eq__(self, other):
                if isinstance(other, dict):
                    return self._doc == other
                return False
        
        mock_results = [MockSolrDoc(doc) for doc in mock_docs]
        mock_solr.search.return_value = mock_results
        mock_get_core.return_value = mock_solr
        
        response = command.get_documents("test_collection", ids=ids)
        assert response.success
        assert len(response.data) == len(mock_docs)
        for actual, expected in zip(response.data, mock_docs):
            assert actual == expected
        # Verify search was called with correct ID query
        expected_query = " OR ".join([f"id:{id}" for id in ids])
        mock_solr.search.assert_called_once_with(expected_query, fl="*", rows=10)

def test_search_documents(command):
    """Test search documents."""
    query = {"q": "*:*"}
    with patch("docstore_manager.solr.command.SolrCommand._get_core") as mock_get_core:
        mock_solr = MagicMock()
        mock_docs = [{"id": "1"}, {"id": "2"}]
        # Create mock Solr documents that behave like dictionaries
        class MockSolrDoc:
            def __init__(self, doc):
                self._doc = doc
            def __iter__(self):
                return iter(self._doc.items())
            def items(self):
                return self._doc.items()
            def __getitem__(self, key):
                return self._doc[key]
            def __eq__(self, other):
                if isinstance(other, dict):
                    return self._doc == other
                return False
        
        mock_results = [MockSolrDoc(doc) for doc in mock_docs]
        mock_solr.search.return_value = mock_results
        mock_get_core.return_value = mock_solr
        
        response = command.search_documents("test_collection", query)
        assert response.success
        assert len(response.data) == len(mock_docs)
        for actual, expected in zip(response.data, mock_docs):
            assert actual == expected
        mock_solr.search.assert_called_once_with(**query)

def test_get_documents_no_criteria(command):
    """Test get documents with no criteria."""
    response = command.get_documents("test_collection")
    assert not response.success
    assert "Either ids or query must be provided" in response.message

def test_delete_documents_no_criteria(command):
    """Test delete documents with no criteria."""
    response = command.delete_documents("test_collection")
    assert not response.success
    assert "Either ids or query must be provided" in response.message

def test_delete_documents_by_query(command):
    """Test delete documents by query."""
    with patch("docstore_manager.solr.command.SolrCommand._get_core") as mock_get_core:
        mock_solr = MagicMock()
        mock_get_core.return_value = mock_solr
        
        response = command.delete_documents("test_collection", query="*:*")
        assert response.success
        mock_solr.delete.assert_called_once_with(q="*:*")
        mock_solr.commit.assert_called_once()

def test_get_documents_by_query(command):
    """Test get documents by query."""
    with patch("docstore_manager.solr.command.SolrCommand._get_core") as mock_get_core:
        mock_solr = MagicMock()
        mock_docs = [{"id": "1"}, {"id": "2"}]
        class MockSolrDoc:
            def __init__(self, doc):
                self._doc = doc
            def __iter__(self):
                return iter(self._doc.items())
            def items(self):
                return self._doc.items()
            def __getitem__(self, key):
                return self._doc[key]
            def __eq__(self, other):
                if isinstance(other, dict):
                    return self._doc == other
                return False
        
        mock_results = [MockSolrDoc(doc) for doc in mock_docs]
        mock_solr.search.return_value = mock_results
        mock_get_core.return_value = mock_solr
        
        response = command.get_documents("test_collection", query="*:*", fields=["id"], limit=5)
        assert response.success
        assert len(response.data) == len(mock_docs)
        mock_solr.search.assert_called_once_with("*:*", fl="id", rows=5)

def test_get_documents_error(command):
    """Test get documents error handling."""
    with patch("docstore_manager.solr.command.SolrCommand._get_core") as mock_get_core:
        mock_solr = MagicMock()
        mock_solr.search.side_effect = Exception("Search failed")
        mock_get_core.return_value = mock_solr
        
        response = command.get_documents("test_collection", query="*:*")
        assert not response.success
        assert "Failed to retrieve documents" in response.message
        assert "Search failed" in response.error

def test_search_documents_error(command):
    """Test search documents error handling."""
    with patch("docstore_manager.solr.command.SolrCommand._get_core") as mock_get_core:
        mock_solr = MagicMock()
        mock_solr.search.side_effect = Exception("Search failed")
        mock_get_core.return_value = mock_solr
        
        response = command.search_documents("test_collection", {"q": "*:*"})
        assert not response.success
        assert "Failed to search documents" in response.message
        assert "Search failed" in response.error

def test_get_config(command):
    """Test get config."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"version": "8.11.2"}
        mock_get.return_value = mock_response
        
        response = command.get_config()
        assert response.success
        assert response.data == {
            "solr_url": "http://localhost:8983/solr",
            "zk_hosts": None,
            "system_info": {"version": "8.11.2"}
        }
        mock_get.assert_called_once_with(f"{command.solr_url}/admin/info/system", params={"wt": "json"})

def test_get_config_error(command):
    """Test get config error handling."""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception("Failed to get system info")
        
        response = command.get_config()
        assert not response.success
        assert "Failed to retrieve configuration" in response.message
        assert "Failed to get system info" in response.error

def test_update_config(command):
    """Test update config."""
    response = command.update_config({"key": "value"})
    assert not response.success
    assert "Configuration updates not supported for Solr" in response.message 