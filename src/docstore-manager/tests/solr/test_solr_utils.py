import pytest
from unittest.mock import patch, MagicMock
import pysolr # Make sure pysolr is imported for type hinting and errors

from docstore_manager.core.exceptions import ConfigurationError, ConnectionError
from docstore_manager.solr.utils import discover_solr_url_from_zk, kazoo_imported, load_configuration, initialize_solr_client, get_solr_base_url

# Mark all tests in this module to skip if kazoo is not installed
pytestmark = pytest.mark.skipif(not kazoo_imported, reason="kazoo library not installed")

@patch('docstore_manager.solr.utils.KazooClient')
def test_discover_solr_url_from_zk_success(mock_kazoo_client):
    """Test successful discovery of Solr URL from ZooKeeper."""
    mock_zk_instance = MagicMock()
    mock_kazoo_client.return_value = mock_zk_instance

    # Mock zk.exists to return True
    mock_zk_instance.exists.return_value = True

    # Mock zk.get_children to return a list of live nodes
    live_nodes = ['10.0.0.1:8983_solr', '10.0.0.2:8983_solr']
    mock_zk_instance.get_children.return_value = live_nodes

    # Use patch to mock random.choice to ensure predictability
    with patch('random.choice', return_value='10.0.0.1:8983_solr'):
        zk_hosts = "zk1:2181,zk2:2181/solr"
        discovered_url = discover_solr_url_from_zk(zk_hosts)

    assert discovered_url == "http://10.0.0.1:8983/solr"
    mock_kazoo_client.assert_called_once_with(hosts=zk_hosts)
    mock_zk_instance.start.assert_called_once()
    mock_zk_instance.exists.assert_called_once_with('/live_nodes')
    mock_zk_instance.get_children.assert_called_once_with('/live_nodes')
    mock_zk_instance.stop.assert_called_once() # Ensure stop is called


@patch('docstore_manager.solr.utils.KazooClient')
def test_discover_solr_url_from_zk_no_live_nodes_path(mock_kazoo_client):
    """Test discovery failure when /live_nodes path doesn't exist."""
    mock_zk_instance = MagicMock()
    mock_kazoo_client.return_value = mock_zk_instance

    # Mock zk.exists to return False
    mock_zk_instance.exists.return_value = False

    zk_hosts = "zk1:2181"
    with pytest.raises(ConfigurationError) as excinfo:
        discover_solr_url_from_zk(zk_hosts)

    assert "No live nodes found in ZooKeeper" in str(excinfo.value)
    assert excinfo.value.details == {'zk_hosts': zk_hosts}
    mock_kazoo_client.assert_called_once_with(hosts=zk_hosts)
    mock_zk_instance.start.assert_called_once()
    mock_zk_instance.exists.assert_called_once_with('/live_nodes')
    mock_zk_instance.stop.assert_called_once()


@patch('docstore_manager.solr.utils.KazooClient')
def test_discover_solr_url_from_zk_no_live_nodes_found(mock_kazoo_client):
    """Test discovery failure when /live_nodes path is empty."""
    mock_zk_instance = MagicMock()
    mock_kazoo_client.return_value = mock_zk_instance

    # Mock zk.exists to return True
    mock_zk_instance.exists.return_value = True
    # Mock zk.get_children to return an empty list
    mock_zk_instance.get_children.return_value = []

    zk_hosts = "zk1:2181"
    with pytest.raises(ConfigurationError) as excinfo:
        discover_solr_url_from_zk(zk_hosts)

    assert "No live Solr nodes found in ZooKeeper" in str(excinfo.value)
    assert excinfo.value.details == {'zk_hosts': zk_hosts}
    mock_kazoo_client.assert_called_once_with(hosts=zk_hosts)
    mock_zk_instance.start.assert_called_once()
    mock_zk_instance.exists.assert_called_once_with('/live_nodes')
    mock_zk_instance.get_children.assert_called_once_with('/live_nodes')
    mock_zk_instance.stop.assert_called_once()

@patch('docstore_manager.solr.utils.KazooClient')
def test_discover_solr_url_from_zk_invalid_node_format(mock_kazoo_client):
    """Test discovery failure with invalid live node format (no underscore)."""
    mock_zk_instance = MagicMock()
    mock_kazoo_client.return_value = mock_zk_instance
    mock_zk_instance.exists.return_value = True
    # Node format missing the underscore separator
    invalid_node = '10.0.0.1:8983solr'
    live_nodes = [invalid_node]
    mock_zk_instance.get_children.return_value = live_nodes

    with patch('random.choice', return_value=invalid_node):
        zk_hosts = "zk1:2181"
        with pytest.raises(ConfigurationError) as excinfo:
            discover_solr_url_from_zk(zk_hosts)

    assert "Could not parse host:port_context from live node name" in str(excinfo.value)
    assert excinfo.value.details == {'node_name': invalid_node}
    mock_zk_instance.stop.assert_called_once()

@patch('docstore_manager.solr.utils.KazooClient')
def test_discover_solr_url_from_zk_kazoo_exception(mock_kazoo_client):
    """Test handling of exceptions during KazooClient interaction (init/start)."""
    mock_zk_instance = MagicMock()
    mock_kazoo_client.return_value = mock_zk_instance

    # Simulate an exception during zk.start()
    error_message = "ZK Connection Failed"
    mock_zk_instance.start.side_effect = Exception(error_message)

    zk_hosts = "zk1:2181"
    # Expect ConnectionError now due to refined outer exception handling
    with pytest.raises(ConnectionError) as excinfo:
        discover_solr_url_from_zk(zk_hosts)

    assert f"Failed to initialize or connect to ZooKeeper: {error_message}" in str(excinfo.value)
    assert excinfo.value.details == {'zk_hosts': zk_hosts, 'error_type': 'Exception'}
    mock_kazoo_client.assert_called_once_with(hosts=zk_hosts)
    mock_zk_instance.start.assert_called_once()
    # stop is NOT called if start fails
    mock_zk_instance.stop.assert_not_called()

@patch('docstore_manager.solr.utils.KazooClient')
def test_discover_solr_url_from_zk_inner_exception(mock_kazoo_client):
    """Test handling of exceptions during ZK operations after connection."""
    mock_zk_instance = MagicMock()
    mock_kazoo_client.return_value = mock_zk_instance

    # Simulate an exception during zk.exists()
    error_message = "ZK Operation Failed"
    mock_zk_instance.exists.side_effect = Exception(error_message)

    zk_hosts = "zk1:2181"
    # Expect ConnectionError now due to refined inner exception handling
    with pytest.raises(ConnectionError) as excinfo:
        discover_solr_url_from_zk(zk_hosts)

    assert f"Error interacting with ZooKeeper after connection: {error_message}" in str(excinfo.value)
    assert excinfo.value.details == {'zk_hosts': zk_hosts, 'error_type': 'Exception'}
    mock_kazoo_client.assert_called_once_with(hosts=zk_hosts)
    mock_zk_instance.start.assert_called_once()
    mock_zk_instance.exists.assert_called_once_with('/live_nodes')
    # stop should still be called in the finally block
    mock_zk_instance.stop.assert_called_once()

# --- Tests for load_configuration ---

@patch('docstore_manager.solr.utils.load_config')
def test_load_configuration_default_profile_solr_url(mock_load_config):
    """Test loading config with default profile and solr_url."""
    mock_load_config.return_value = {
        'solr': {
            'connection': {
                'solr_url': 'http://default-solr:8983/solr',
                'collection': 'default_coll'
            }
        }
    }
    args = MagicMock(spec=['profile', 'solr_url', 'zk_hosts', 'collection'])
    args.profile = None
    args.solr_url = None
    args.zk_hosts = None
    args.collection = None

    config = load_configuration(args)

    assert config == {
        'solr_url': 'http://default-solr:8983/solr',
        'collection': 'default_coll'
    }
    mock_load_config.assert_called_once_with()

@patch('docstore_manager.solr.utils.load_config')
def test_load_configuration_specific_profile_zk(mock_load_config):
    """Test loading config with a specific profile and zk_hosts."""
    profile_name = "myprofile"
    mock_load_config.return_value = {
        'solr': {
            'connection': {
                'zk_hosts': 'zk-server:2181',
                'collection': 'profile_coll'
            }
        }
    }
    args = MagicMock(spec=['profile', 'solr_url', 'zk_hosts', 'collection'])
    args.profile = profile_name
    args.solr_url = None
    args.zk_hosts = None
    args.collection = None

    config = load_configuration(args)

    assert config == {
        'zk_hosts': 'zk-server:2181',
        'collection': 'profile_coll'
    }
    mock_load_config.assert_called_once_with(profile_name)

@patch('docstore_manager.solr.utils.load_config')
def test_load_configuration_cli_overrides(mock_load_config):
    """Test overriding config values with CLI arguments."""
    mock_load_config.return_value = {
        'solr': {
            'connection': {
                'solr_url': 'http://config-solr:8983/solr',
                'collection': 'config_coll'
            }
        }
    }
    args = MagicMock(spec=['profile', 'solr_url', 'zk_hosts', 'collection'])
    args.profile = None
    args.solr_url = 'http://cli-solr:8983/solr' # Override solr_url
    args.zk_hosts = 'cli-zk:2181'            # Add zk_hosts
    args.collection = 'cli_coll'             # Override collection

    config = load_configuration(args)

    assert config == {
        'solr_url': 'http://cli-solr:8983/solr',
        'zk_hosts': 'cli-zk:2181',
        'collection': 'cli_coll'
    }
    mock_load_config.assert_called_once_with()

@patch('docstore_manager.solr.utils.load_config')
def test_load_configuration_missing_url_and_zk(mock_load_config):
    """Test error when neither solr_url nor zk_hosts is provided."""
    mock_load_config.return_value = {
        'solr': {
            'connection': {
                'collection': 'some_coll' # Missing url/zk
            }
        }
    }
    args = MagicMock(spec=['profile', 'solr_url', 'zk_hosts', 'collection'])
    args.profile = None
    args.solr_url = None
    args.zk_hosts = None
    args.collection = None

    with pytest.raises(ConfigurationError) as excinfo:
        load_configuration(args)

    assert "Either solr_url or zk_hosts must be provided" in str(excinfo.value)
    assert excinfo.value.details == {'config_keys': ['collection']}

@patch('docstore_manager.solr.utils.load_config')
@patch('docstore_manager.solr.utils.kazoo_imported', False) # Simulate kazoo not being imported
def test_load_configuration_zk_without_kazoo(mock_load_config):
    """Test error when zk_hosts is provided but kazoo is not installed."""
    mock_load_config.return_value = {
        'solr': {
            'connection': {
                'zk_hosts': 'zk-server:2181',
                'collection': 'zk_coll'
            }
        }
    }
    args = MagicMock(spec=['profile', 'solr_url', 'zk_hosts', 'collection'])
    args.profile = None
    args.solr_url = None
    args.zk_hosts = None # Not overridden by CLI
    args.collection = None

    with pytest.raises(ConfigurationError) as excinfo:
        load_configuration(args)

    assert "'kazoo' library is not installed" in str(excinfo.value)
    assert excinfo.value.details == {
        'missing_package': 'kazoo',
        'install_command': 'pip install solr-manager[zookeeper]'
    }

# --- Tests for initialize_solr_client ---

@patch('docstore_manager.solr.utils.pysolr.Solr')
def test_initialize_solr_client_direct_url(mock_pysolr_solr):
    """Test initializing Solr client with a direct URL."""
    config = {
        'solr_url': 'http://solrserver:8983/solr',
        'username': 'user',
        'password': 'pass',
        'timeout': 15
    }
    collection_name = "my_collection"
    expected_full_url = f"{config['solr_url']}/{collection_name}"
    expected_auth = (config['username'], config['password'])
    
    mock_client_instance = MagicMock()
    mock_pysolr_solr.return_value = mock_client_instance

    client = initialize_solr_client(config, collection_name)

    assert client == mock_client_instance
    mock_pysolr_solr.assert_called_once_with(
        expected_full_url, 
        auth=expected_auth, 
        timeout=config['timeout']
    )

@patch('docstore_manager.solr.utils.pysolr.SolrCloud')
@patch('docstore_manager.solr.utils.KazooClient')
@patch('docstore_manager.solr.utils.kazoo_imported', True) # Ensure kazoo is considered imported
def test_initialize_solr_client_zk(mock_kazoo_client, mock_pysolr_solrcloud):
    """Test initializing Solr client with ZooKeeper hosts."""
    config = {
        'zk_hosts': 'zk1:2181,zk2:2181',
        'timeout': 20
    }
    collection_name = "cloud_collection"
    
    mock_zk_instance = MagicMock()
    mock_kazoo_client.return_value = mock_zk_instance
    mock_solr_cloud_instance = MagicMock()
    mock_pysolr_solrcloud.return_value = mock_solr_cloud_instance

    client = initialize_solr_client(config, collection_name)

    assert client == mock_solr_cloud_instance
    mock_kazoo_client.assert_called_once_with(hosts=config['zk_hosts'], timeout=config['timeout'])
    mock_pysolr_solrcloud.assert_called_once_with(
        mock_zk_instance, 
        collection_name, 
        auth=None, 
        timeout=config['timeout']
    )

@patch('docstore_manager.solr.utils.pysolr.Solr')
def test_initialize_solr_client_no_auth_no_timeout(mock_pysolr_solr):
    """Test initializing Solr client without auth and using default timeout."""
    config = {
        'solr_url': 'http://solrserver:8983/solr',
        # No username/password
        # No timeout
    }
    collection_name = "no_auth_coll"
    expected_full_url = f"{config['solr_url']}/{collection_name}"
    default_timeout = 30 # Default specified in the function

    mock_client_instance = MagicMock()
    mock_pysolr_solr.return_value = mock_client_instance

    client = initialize_solr_client(config, collection_name)

    assert client == mock_client_instance
    mock_pysolr_solr.assert_called_once_with(
        expected_full_url, 
        auth=None, 
        timeout=default_timeout
    )


def test_initialize_solr_client_no_url_or_zk():
    """Test ConfigurationError when neither solr_url nor zk_hosts is provided."""
    config = {}
    collection_name = "test_coll"
    with pytest.raises(ConfigurationError) as excinfo:
        initialize_solr_client(config, collection_name)
    assert "Invalid configuration: No 'solr_url' or 'zk_hosts' provided" in str(excinfo.value)
    assert excinfo.value.details == {'config_keys': []}

@patch('docstore_manager.solr.utils.kazoo_imported', False) # Simulate kazoo not imported
def test_initialize_solr_client_zk_without_kazoo():
    """Test ConfigurationError when zk_hosts is provided but kazoo is not."""
    config = {'zk_hosts': 'zk:2181'}
    collection_name = "test_coll"
    with pytest.raises(ConfigurationError) as excinfo:
        initialize_solr_client(config, collection_name)
    assert "Cannot initialize SolrCloud client: 'kazoo' is not installed" in str(excinfo.value)
    assert excinfo.value.details == {'install_command': 'pip install solr-manager[zookeeper]'}


@patch('docstore_manager.solr.utils.pysolr.Solr', side_effect=pysolr.SolrError("Connection refused"))
def test_initialize_solr_client_pysolr_error(mock_pysolr_solr):
    """Test ConnectionError when pysolr.Solr raises SolrError."""
    config = {'solr_url': 'http://bad-solr:8983/solr'}
    collection_name = "error_coll"
    with pytest.raises(ConnectionError) as excinfo:
        initialize_solr_client(config, collection_name)
    assert "Failed to initialize Solr client: Connection refused" in str(excinfo.value)
    assert excinfo.value.details == {
        'collection': collection_name,
        'solr_url': config['solr_url'],
        'zk_hosts': None
    }

@patch('docstore_manager.solr.utils.pysolr.SolrCloud')
@patch('docstore_manager.solr.utils.KazooClient', side_effect=Exception("Network Error"))
@patch('docstore_manager.solr.utils.kazoo_imported', True)
def test_initialize_solr_client_other_exception(mock_kazoo_client, mock_pysolr_solrcloud):
    """Test ConnectionError for unexpected exceptions during initialization."""
    config = {'zk_hosts': 'zk:2181'}
    collection_name = "other_error_coll"
    with pytest.raises(ConnectionError) as excinfo:
        initialize_solr_client(config, collection_name)
    assert "An unexpected error occurred during Solr connection: Network Error" in str(excinfo.value)
    assert excinfo.value.details == {
        'collection': collection_name,
        'solr_url': None,
        'zk_hosts': config['zk_hosts'],
        'error_type': 'Exception'
    }

# --- Tests for get_solr_base_url --- (Placeholder for potential future tests) 