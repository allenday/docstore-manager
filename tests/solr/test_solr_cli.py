"""Tests for the Solr CLI module."""
import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace

from docstore_manager.solr.cli import SolrCLI, main
from docstore_manager.common.exceptions import ConfigurationError, DocumentStoreError

@pytest.fixture
def cli():
    """Create a SolrCLI instance."""
    return SolrCLI()

@pytest.fixture
def mock_args():
    """Create mock command line arguments."""
    return Namespace(
        command=None,
        solr_url="http://localhost:8983/solr",
        zk_hosts=None,
        username=None,
        password=None,
        timeout=30,
        profile=None,
        config=None
    )

def test_cli_initialization(cli):
    """Test CLI initialization."""
    assert isinstance(cli, SolrCLI)
    parser = cli.create_parser()
    expected_description = "Command-line tool for managing Apache Solr collections and documents."
    assert parser.description == expected_description

def test_initialize_client_with_solr_url(cli, mock_args):
    """Test client initialization with Solr URL."""
    with patch("docstore_manager.solr.cli.load_configuration") as mock_load_config:
        mock_load_config.return_value = {"solr_url": "http://localhost:8983/solr"}
        with patch("docstore_manager.solr.cli.SolrCommand") as mock_command:
            client = cli.initialize_client(mock_args)
            mock_command.assert_called_once_with(solr_url="http://localhost:8983/solr", zk_hosts=None)
            assert client == mock_command.return_value

def test_initialize_client_with_zk_hosts(cli, mock_args):
    """Test client initialization with ZooKeeper hosts."""
    with patch("docstore_manager.solr.cli.load_configuration") as mock_load_config:
        mock_load_config.return_value = {"zk_hosts": "zk1:2181,zk2:2181/solr"}
        with patch("docstore_manager.solr.cli.SolrCommand") as mock_command:
            client = cli.initialize_client(mock_args)
            mock_command.assert_called_once_with(solr_url=None, zk_hosts="zk1:2181,zk2:2181/solr")
            assert client == mock_command.return_value

def test_initialize_client_no_url_or_zk(cli, mock_args):
    """Test client initialization with neither Solr URL nor ZooKeeper hosts."""
    with patch("docstore_manager.solr.cli.load_configuration") as mock_load_config:
        mock_load_config.return_value = {}
        with pytest.raises(ConfigurationError) as exc_info:
            cli.initialize_client(mock_args)
        assert "Either solr_url or zk_hosts must be provided" in str(exc_info.value)

def test_handle_create(cli, mock_args):
    """Test create command handling."""
    mock_client = MagicMock()
    mock_args.command = "create"
    mock_args.name = "test_collection"
    mock_args.num_shards = 1
    mock_args.replication_factor = 1
    mock_args.configset = "default"
    
    with patch("docstore_manager.solr.cli.create_collection") as mock_create:
        cli.handle_create(mock_client, mock_args)
        mock_create.assert_called_once_with(mock_client, mock_args)

def test_handle_delete(cli, mock_args):
    """Test delete command handling."""
    mock_client = MagicMock()
    mock_args.command = "delete"
    mock_args.name = "test_collection"
    
    with patch("docstore_manager.solr.cli.delete_collection") as mock_delete:
        cli.handle_delete(mock_client, mock_args)
        mock_delete.assert_called_once_with(mock_client, mock_args)

def test_handle_list(cli, mock_args):
    """Test list command handling."""
    mock_client = MagicMock()
    mock_args.command = "list"
    
    with patch("docstore_manager.solr.cli.list_collections") as mock_list:
        cli.handle_list(mock_client, mock_args)
        mock_list.assert_called_once_with(mock_client, mock_args)

def test_handle_info(cli, mock_args):
    """Test info command handling."""
    mock_client = MagicMock()
    mock_args.command = "info"
    mock_args.name = "test_collection"
    
    with patch("docstore_manager.solr.cli.collection_info") as mock_info:
        cli.handle_info(mock_client, mock_args)
        mock_info.assert_called_once_with(mock_client, mock_args)

def test_handle_batch_add(cli, mock_args):
    """Test batch add command handling."""
    mock_client = MagicMock()
    mock_args.command = "batch"
    mock_args.add_update = True
    mock_args.delete_docs = False
    mock_args.collection = "test_collection"
    mock_args.doc = '{"id": "1", "field": "value"}'
    
    with patch("docstore_manager.solr.cli.batch_add") as mock_add:
        cli.handle_batch(mock_client, mock_args)
        mock_add.assert_called_once_with(mock_client, mock_args)

def test_handle_batch_delete(cli, mock_args):
    """Test batch delete command handling."""
    mock_client = MagicMock()
    mock_args.command = "batch"
    mock_args.add_update = False
    mock_args.delete_docs = True
    mock_args.collection = "test_collection"
    mock_args.ids = "1,2,3"
    
    with patch("docstore_manager.solr.cli.batch_delete") as mock_delete:
        cli.handle_batch(mock_client, mock_args)
        mock_delete.assert_called_once_with(mock_client, mock_args)

def test_handle_get(cli, mock_args):
    """Test get command handling."""
    mock_client = MagicMock()
    mock_args.command = "get"
    mock_args.collection = "test_collection"
    mock_args.ids = "doc1,doc2"
    
    with patch("docstore_manager.solr.cli.get_documents") as mock_get:
        cli.handle_get(mock_client, mock_args)
        mock_get.assert_called_once_with(mock_client, mock_args)

def test_handle_config(cli, mock_args):
    """Test config command handling."""
    mock_args.command = "config"
    
    with patch("docstore_manager.solr.cli.show_config_info") as mock_config:
        cli.handle_config(mock_args)
        mock_config.assert_called_once_with(mock_args)

def test_main():
    """Test main function."""
    with patch("docstore_manager.solr.cli.SolrCLI") as mock_cli:
        mock_instance = MagicMock()
        mock_cli.return_value = mock_instance
        main()
        mock_instance.run.assert_called_once() 