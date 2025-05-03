import pytest
from unittest.mock import patch, MagicMock, Mock
import pysolr
import re
import logging
import kazoo.exceptions

from docstore_manager.core.exceptions import ConfigurationError, ConnectionError, CollectionError
from docstore_manager.solr.client import SolrClient
# Import kazoo_imported to conditionally skip ZK tests if kazoo is not installed
from docstore_manager.solr.utils import kazoo_imported
# Import NoNodeError if it's potentially raised and needs handling/assertion
# from kazoo.exceptions import NoNodeError

# Import the module directly to patch its attributes
import docstore_manager.solr.client
# Remove the alias import that pointed to the instance:
# import docstore_manager.solr.client as solr_client_module


@pytest.fixture
def solr_store():
    """Fixture to provide a SolrDocumentStore instance initialized with mock config."""
    # Provide a default mock config to satisfy __init__
    mock_config = {
        'solr_url': 'http://mock-solr:8983/solr', 
        'collection': 'mock_collection' 
    }
    # Patch create_client during instantiation for this fixture to avoid real connection attempts
    with patch.object(SolrClient, 'create_client', return_value=MagicMock()) as mock_create:
        client = SolrClient(config=mock_config)
        client._create_client_mock = mock_create # Store mock for potential assertions if needed
        return client

@pytest.fixture
def solr_store_zk_config():
    """Fixture providing a sample Zookeeper configuration."""
    return {
        'zk_hosts': 'zkhost1:2181,zkhost2:2181/solr',
        'collection': 'zk_test_collection'
    }

# --- Tests for validate_config ---

def test_validate_config_with_solr_url(solr_store):
    """Test validate_config success with solr_url."""
    config = {'solr_url': 'http://host:1234/solr'}
    try:
        solr_store.validate_config(config)
    except ConfigurationError:
        pytest.fail("validate_config raised ConfigurationError unexpectedly")

def test_validate_config_with_zk_hosts(solr_store):
    """Test validate_config success with zk_hosts."""
    config = {'zk_hosts': 'zk:2181'}
    try:
        solr_store.validate_config(config)
    except ConfigurationError:
        pytest.fail("validate_config raised ConfigurationError unexpectedly")

def test_validate_config_missing_both(solr_store):
    """Test validate_config failure when both url and zk are missing."""
    config = {'collection': 'some_coll'}
    with pytest.raises(ConfigurationError) as excinfo:
        solr_store.validate_config(config)
    assert "Either solr_url or zk_hosts must be provided" in str(excinfo.value)

# --- Tests for create_client ---

@patch('pysolr.Solr')
# Patch _get_base_solr_url to return the expected URL from config for this test
@patch('docstore_manager.solr.client.SolrClient._get_base_solr_url') 
def test_create_client_with_solr_url(mock_get_base, MockPysolr):
    """Test client creation using direct solr_url."""
    solr_url = "http://solr.example.com:8983/solr/"
    collection = "my_coll_url"
    config = {'solr_url': solr_url, 'collection': collection, 'timeout': 20}
    # Configure the mock to return the URL from the config
    mock_get_base.return_value = config['solr_url'] 
    
    client = SolrClient(config=config)
    
    # Construct expected URL based on how create_client builds it
    expected_solr_instance_url = f"{solr_url.rstrip('/')}/{collection}"

    assert client is not None
    # Assert _get_base_solr_url was called (even if it just returned the config value)
    mock_get_base.assert_called_once_with() 
    MockPysolr.assert_called_once_with(expected_solr_instance_url, timeout=20)
    assert client.client is not None

@patch('pysolr.Solr', side_effect=pysolr.SolrError("Connection failed"))
# Patch _get_base_solr_url to return the expected URL from config for this test
@patch('docstore_manager.solr.client.SolrClient._get_base_solr_url') 
def test_create_client_pysolr_fails(mock_get_base, MockPysolr):
    """Test handling of pysolr.Solr instantiation failure."""
    solr_url = "http://bad-solr:8983/solr"
    collection = "my_coll_fail"
    config = {'solr_url': solr_url, 'collection': collection}
    # Configure the mock to return the URL from the config
    mock_get_base.return_value = config['solr_url']
    
    # Construct expected URL based on how create_client builds it
    expected_solr_instance_url = f"{solr_url.rstrip('/')}/{collection}"
    
    # Now it should fail inside pysolr.Solr(), raising SolrError,
    # which should be wrapped by ConnectionError by create_client
    with pytest.raises(ConnectionError, match="Failed to create Solr client: Connection failed"):
        SolrClient(config=config)
        
    mock_get_base.assert_called_once_with() # Ensure base URL retrieval was attempted
    MockPysolr.assert_called_once_with(expected_solr_instance_url, timeout=10)

@patch('pysolr.Solr')
# Patch _get_base_solr_url now instead of _get_solr_url_via_zk
@patch('docstore_manager.solr.client.SolrClient._get_base_solr_url') 
def test_create_client_with_zk_hosts(mock_get_base_url, MockPysolr):
    """Test client creation using Zookeeper hosts."""
    zk_hosts = "zk1:2181,zk2:2181"
    collection = "my_coll_zk"
    # Simulate _get_base_solr_url returning a valid base URL
    mock_zk_derived_base_url = "http://derived-from-zk:8983/solr" 
    mock_get_base_url.return_value = mock_zk_derived_base_url
    
    config = {'zk_hosts': zk_hosts, 'collection': collection, 'timeout': 5}
    client = SolrClient(config=config)
    
    expected_solr_instance_url = f"{mock_zk_derived_base_url.rstrip('/')}/{collection}"

    assert client is not None
    # Assert _get_base_solr_url was called instead of _get_solr_url_via_zk
    mock_get_base_url.assert_called_once_with() 
    MockPysolr.assert_called_once_with(expected_solr_instance_url, timeout=5)
    assert client.client is not None

# Test failure during ZK lookup
@patch('pysolr.Solr')
# Patch _get_base_solr_url and make it raise the ConnectionError
@patch('docstore_manager.solr.client.SolrClient._get_base_solr_url', side_effect=ConnectionError("ZK lookup failed"))
def test_create_client_zk_get_url_fails(mock_get_base_url, MockPysolr):
    """Test handling failure when ZK URL retrieval fails."""
    zk_hosts = "zk-down:2181"
    collection = "my_coll_zk_fail"
    config = {'zk_hosts': zk_hosts, 'collection': collection}

    # Now expect ConnectionError directly from the failed _get_base_solr_url call
    with pytest.raises(ConnectionError, match="ZK lookup failed"): 
        SolrClient(config=config)
        
    mock_get_base_url.assert_called_once_with()
    MockPysolr.assert_not_called()

# --- Zookeeper URL Retrieval Tests ---

# Use standard patching decorator
@pytest.mark.skipif(not kazoo_imported, reason="kazoo library not installed")
@patch('docstore_manager.solr.client.KazooClient') 
def test_get_solr_url_via_zk_success(MockKazooClient):
    """Test successfully getting Solr URL from ZK."""
    mock_zk_instance = MagicMock()
    mock_zk_instance.start.return_value = None
    mock_zk_instance.get_children.return_value = ['host1:8983_solr', 'host2:7574_solr']
    # Simulate getting the node data for the first node - **Use expected format**
    mock_zk_instance.get.return_value = (b'host1:8983_solr', MagicMock()) # Return bytes and stat mock
    MockKazooClient.return_value = mock_zk_instance
    
    zk_hosts = "zk1:2181"
    config = {'zk_hosts': zk_hosts, 'collection': 'zk_test_coll'} 
    
    # Prevent __init__ from calling create_client/get_base_url during setup
    with patch.object(SolrClient, 'create_client', return_value=None): 
        client = SolrClient(config=config)
        # Now call the method directly
        base_url = client._get_solr_url_via_zk(zk_hosts) 

    # Assert base_url is derived correctly from the first node's mock data - **Adjust assertion**
    assert base_url == "http://host1:8983" 
    MockKazooClient.assert_called_once_with(hosts=zk_hosts)
    mock_zk_instance.start.assert_called_once()
    mock_zk_instance.get_children.assert_called_once_with('/live_nodes')
    mock_zk_instance.get.assert_called_once_with('/live_nodes/host1:8983_solr') # Called for the first node
    mock_zk_instance.stop.assert_called_once()
    mock_zk_instance.close.assert_called_once()

@pytest.mark.skipif(not kazoo_imported, reason="kazoo library not installed")
@patch('docstore_manager.solr.client.KazooClient')
def test_get_solr_url_via_zk_no_nodes(MockKazooClient):
    """Test getting Solr URL from ZK when no live nodes are found."""
    mock_zk_instance = MagicMock()
    mock_zk_instance.start.return_value = None
    mock_zk_instance.get_children.return_value = [] # No live nodes
    MockKazooClient.return_value = mock_zk_instance

    zk_hosts = "zk-empty:2181"
    config = {'zk_hosts': zk_hosts, 'collection': 'zk_empty_coll'}

    # Prevent __init__ from calling create_client
    with patch.object(SolrClient, 'create_client', return_value=None): 
        client = SolrClient(config=config)
        # Call the method directly and assert the expected error
        with pytest.raises(ConnectionError, match="No live Solr nodes found in ZooKeeper"):
            client._get_solr_url_via_zk(zk_hosts)

    MockKazooClient.assert_called_once_with(hosts=zk_hosts)
    mock_zk_instance.start.assert_called_once()
    mock_zk_instance.get_children.assert_called_once_with('/live_nodes')
    mock_zk_instance.get.assert_not_called()
    mock_zk_instance.stop.assert_called_once()
    mock_zk_instance.close.assert_called_once()

@pytest.mark.skipif(not kazoo_imported, reason="kazoo library not installed")
@patch('docstore_manager.solr.client.KazooClient')
def test_get_solr_url_via_zk_exception(MockKazooClient):
    """Test handling exceptions during ZK interaction."""
    mock_zk_instance = MagicMock()
    # Simulate Kazoo exception during get_children
    original_zk_exception = kazoo.exceptions.NoNodeError("Path does not exist") # Use imported exception
    mock_zk_instance.get_children.side_effect = original_zk_exception 
    MockKazooClient.return_value = mock_zk_instance

    zk_hosts = "zk-error:2181"
    config = {'zk_hosts': zk_hosts, 'collection': 'zk_error_coll'}

    # Prevent __init__ from calling create_client
    with patch.object(SolrClient, 'create_client', return_value=None):
        client = SolrClient(config=config)
        # Call the method directly and assert the expected wrapped error
        with pytest.raises(ConnectionError, match="Failed to get Solr URL from ZooKeeper: Path does not exist") as exc_info:
            client._get_solr_url_via_zk(zk_hosts)
        
        # Check that the cause is the original ZK exception
        assert exc_info.value.__cause__ is original_zk_exception

    MockKazooClient.assert_called_once_with(hosts=zk_hosts)
    mock_zk_instance.start.assert_called_once()
    mock_zk_instance.get_children.assert_called_once_with('/live_nodes')
    mock_zk_instance.stop.assert_called_once() # stop/close should still be called on error
    mock_zk_instance.close.assert_called_once()

# --- Collection Management Tests ---

# --- Tests for validate_connection ---

def test_validate_connection_success(solr_store):
    """Test validate_connection returning True on successful ping."""
    mock_client = MagicMock(spec=pysolr.Solr)
    # Assuming ping returns something truthy or doesn't raise an error on success
    mock_client.ping.return_value = "OK"

    result = solr_store.validate_connection(mock_client)

    assert result is True
    mock_client.ping.assert_called_once()

def test_validate_connection_failure(solr_store):
    """Test validate_connection returning False when ping fails."""
    mock_client = MagicMock(spec=pysolr.Solr)
    mock_client.ping.side_effect = pysolr.SolrError("Ping failed")

    result = solr_store.validate_connection(mock_client)

    assert result is False
    mock_client.ping.assert_called_once()

# --- Tests for close ---

def test_close_success(solr_store):
    """Test close successfully calls session close."""
    mock_session = MagicMock()
    mock_client = MagicMock(spec=pysolr.Solr)
    # Mock get_session() if it's called by close()
    mock_client.get_session.return_value = mock_session

    solr_store.close(mock_client)

    mock_client.get_session.assert_called_once()
    mock_session.close.assert_called_once()

def test_close_failure(solr_store):
    """Test close handles exceptions gracefully."""
    mock_client = MagicMock(spec=pysolr.Solr)
    mock_client.get_session.side_effect = Exception("Session error")

    try:
        solr_store.close(mock_client)
        # assert no exception is raised
    except Exception as e:
        pytest.fail(f"close() raised an exception unexpectedly: {e}")

    mock_client.get_session.assert_called_once()
