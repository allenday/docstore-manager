import pytest
from unittest.mock import patch, MagicMock, Mock
import pysolr
import re

from docstore_manager.common.exceptions import ConfigurationError, ConnectionError
from docstore_manager.solr.client import SolrDocumentStore
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
    """Fixture to provide a SolrDocumentStore instance."""
    return SolrDocumentStore()

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

@patch('pysolr.Solr') # Target original class
def test_create_client_with_solr_url(mock_solr, solr_store):
    """Test create_client successfully using solr_url."""
    solr_url = 'http://solr.example.com:8983/solr'
    collection = 'mycoll'
    config = {'solr_url': solr_url, 'collection': collection}
    expected_url = f"{solr_url.rstrip('/')}/{collection}"
    mock_client_instance = MagicMock()
    mock_solr.return_value = mock_client_instance

    client = solr_store.create_client(config)

    assert client == mock_client_instance
    mock_solr.assert_called_once_with(expected_url, timeout=10)

@patch('kazoo.client.KazooClient') # Target original class
@patch('pysolr.Solr') # Target original class
@patch.object(SolrDocumentStore, '_get_solr_url_via_zk')
@pytest.mark.skipif(not kazoo_imported, reason="kazoo library not installed")
def test_create_client_with_zk_hosts(mock_get_url_helper, mock_solr, mock_kazoo_client, solr_store):
    """Test creating Solr client using ZooKeeper hosts via the helper."""
    zk_hosts = "zk1:2181,zk2:2181/solr"
    collection = 'zkcoll'
    config = {'zk_hosts': zk_hosts, 'collection': collection}
    mock_solr_url_base = 'http://mocked_solr_host:8983/solr'
    mock_get_url_helper.return_value = mock_solr_url_base

    mock_client_instance = MagicMock()
    mock_solr.return_value = mock_client_instance
    expected_pysolr_url = f"{mock_solr_url_base.rstrip('/')}/{collection}"

    client = solr_store.create_client(config)

    mock_get_url_helper.assert_called_once_with(zk_hosts)
    mock_solr.assert_called_once_with(expected_pysolr_url, timeout=10)
    assert client == mock_client_instance
    # KazooClient is called by the mocked _get_solr_url_via_zk, not directly here
    mock_kazoo_client.assert_not_called()

@patch.object(SolrDocumentStore, '_get_solr_url_via_zk', side_effect=ConfigurationError("ZK URL error"))
def test_create_client_zk_get_url_fails(mock_get_url, solr_store, solr_store_zk_config):
    """Test create_client raises ConnectionError when _get_solr_url_via_zk fails."""
    config = solr_store_zk_config
    with pytest.raises(ConnectionError, match="Failed to create Solr client: ZK URL error"):
        solr_store.create_client(config)
    mock_get_url.assert_called_once_with(config['zk_hosts']) # Ensure helper was called

@patch('pysolr.Solr') # Target original class
def test_create_client_pysolr_fails(mock_solr, solr_store):
    """Test create_client failure when pysolr.Solr() instantiation fails."""
    config = {'solr_url': 'http://badsurl/solr', 'collection': 'badcoll'}
    mock_solr.side_effect = pysolr.SolrError("Init failed")

    with pytest.raises(ConnectionError, match="Failed to create Solr client: Init failed"):
        solr_store.create_client(config)

    expected_url = f"{config['solr_url'].rstrip('/')}/{config['collection']}"
    mock_solr.assert_called_once_with(expected_url, timeout=10)

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


# --- Tests for _get_solr_url_via_zk (Direct Method Tests) ---

@pytest.mark.skipif(not kazoo_imported, reason="kazoo library not installed")
def test_get_solr_url_via_zk_success(solr_store_zk_config):
    """Test _get_solr_url_via_zk success scenario (manual patch via class globals)."""
    mock_zk_instance = MagicMock()
    mock_zk_instance.start.return_value = None
    mock_zk_instance.get_children.return_value = ['host1:8983_solr', 'host2:7574_solr']
    # We need to mock the get() method called inside _get_solr_url_via_zk
    # Simulate getting the node data for the first node
    mock_zk_instance.get.return_value = (b'host1:8983_solr', MagicMock()) # Return bytes and stat mock

    mock_kazoo_client_class = MagicMock(return_value=mock_zk_instance)

    method_to_patch = SolrDocumentStore._get_solr_url_via_zk
    method_globals = method_to_patch.__globals__
    original_kazoo_client = method_globals.get('KazooClient')

    if original_kazoo_client is None:
        pytest.fail("Could not find KazooClient in the method's globals to patch.")

    method_globals['KazooClient'] = mock_kazoo_client_class

    try:
        store = SolrDocumentStore()
        zk_hosts_param = solr_store_zk_config['zk_hosts']

        solr_url = store._get_solr_url_via_zk(zk_hosts_param)

        mock_kazoo_client_class.assert_called_once_with(hosts=zk_hosts_param)
        assert solr_url == "http://host1:8983"
        mock_zk_instance.start.assert_called_once()
        mock_zk_instance.get_children.assert_called_once_with('/live_nodes')
        # Verify get was called for the first node path
        mock_zk_instance.get.assert_called_once_with('/live_nodes/host1:8983_solr')
        mock_zk_instance.stop.assert_called_once()
        mock_zk_instance.close.assert_called_once()

    finally:
        if original_kazoo_client:
            method_globals['KazooClient'] = original_kazoo_client

@pytest.mark.skipif(not kazoo_imported, reason="kazoo library not installed")
def test_get_solr_url_via_zk_no_nodes(solr_store_zk_config):
    """Test _get_solr_url_via_zk when no live nodes are found (manual patch via class globals)."""
    # 1. Prepare the mock instance and the mock class
    mock_zk_instance = MagicMock()
    mock_zk_instance.start.return_value = None
    mock_zk_instance.get_children.return_value = [] # No live nodes

    mock_kazoo_client_class = MagicMock(return_value=mock_zk_instance)

    # 2. Manually patch KazooClient in the method's global scope via the CLASS
    method_to_patch = SolrDocumentStore._get_solr_url_via_zk
    method_globals = method_to_patch.__globals__
    original_kazoo_client = method_globals.get('KazooClient') # Use .get for safety

    if original_kazoo_client is None:
        pytest.fail("Could not find KazooClient in the method's globals to patch.")

    method_globals['KazooClient'] = mock_kazoo_client_class

    try:
        # 3. Run the test logic
        store = SolrDocumentStore()
        zk_hosts_param = solr_store_zk_config['zk_hosts']

        with pytest.raises(ConnectionError, match="No live Solr nodes found in ZooKeeper"):
            store._get_solr_url_via_zk(zk_hosts_param)

        # 4. Assertions
        mock_kazoo_client_class.assert_called_once_with(hosts=zk_hosts_param)
        mock_zk_instance.start.assert_called_once()
        mock_zk_instance.get_children.assert_called_once_with('/live_nodes')
        mock_zk_instance.get.assert_not_called()
        mock_zk_instance.stop.assert_called_once()
        mock_zk_instance.close.assert_called_once()

    finally:
        # 5. Restore the original KazooClient (CRUCIAL)
        if original_kazoo_client:
             method_globals['KazooClient'] = original_kazoo_client

@pytest.mark.skipif(not kazoo_imported, reason="kazoo library not installed")
def test_get_solr_url_via_zk_exception(solr_store_zk_config):
    """Test _get_solr_url_via_zk handles Kazoo exceptions (manual patch via class globals)."""
    mock_zk_instance = MagicMock()
    # Simulate an exception during the start method
    mock_zk_instance.start.side_effect = Exception("Kazoo connection lost")

    mock_kazoo_client_class = MagicMock(return_value=mock_zk_instance)

    method_to_patch = SolrDocumentStore._get_solr_url_via_zk
    method_globals = method_to_patch.__globals__
    original_kazoo_client = method_globals.get('KazooClient')

    if original_kazoo_client is None:
        pytest.fail("Could not find KazooClient in the method's globals to patch.")

    method_globals['KazooClient'] = mock_kazoo_client_class

    try:
        store = SolrDocumentStore()
        zk_hosts_param = solr_store_zk_config['zk_hosts']

        with pytest.raises(ConnectionError, match=r"Failed to get Solr URL from ZooKeeper: Kazoo connection lost"):
            store._get_solr_url_via_zk(zk_hosts_param)

        # Assertions
        mock_kazoo_client_class.assert_called_once_with(hosts=zk_hosts_param)
        mock_zk_instance.start.assert_called_once()
        mock_zk_instance.get_children.assert_not_called()
        mock_zk_instance.get.assert_not_called()
        # stop/close should still be called in the finally block
        mock_zk_instance.stop.assert_called_once()
        mock_zk_instance.close.assert_called_once()

    finally:
        # Restore the original KazooClient
        if original_kazoo_client:
            method_globals['KazooClient'] = original_kazoo_client
