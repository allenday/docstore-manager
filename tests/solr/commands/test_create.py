"""Tests for Solr create command."""

import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace
import logging
import json

from docstore_manager.solr.commands.create import create_collection
from docstore_manager.solr.command import SolrCommand

@pytest.fixture
def mock_command():
    """Fixture for mocked SolrCommand."""
    return MagicMock(spec=SolrCommand)

@pytest.fixture
def mock_args():
    """Fixture for mocked command line arguments."""
    return Namespace(
        collection="new_collection",
        num_shards=None,
        replication_factor=None,
        configset=None
    )

def test_create_collection_success_defaults(mock_command, mock_args, caplog):
    """Test successful creation with default arguments."""
    caplog.set_level(logging.INFO)
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.message = "Created collection 'new_collection'"
    mock_response.data = {'name': 'new_collection'}
    mock_response.error = None
    mock_command.create_collection.return_value = mock_response

    create_collection(mock_command, mock_args)

    mock_command.create_collection.assert_called_once_with(name="new_collection")
    assert "Creating collection 'new_collection'" in caplog.text
    assert "Created collection 'new_collection'" in caplog.text
    assert "Collection details:" in caplog.text

def test_create_collection_success_with_args(mock_command, mock_args, caplog):
    """Test successful creation with specific arguments."""
    caplog.set_level(logging.INFO)
    mock_args.num_shards = 2
    mock_args.replication_factor = 2
    mock_args.configset = "my_config"
    
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.message = "Created collection 'new_collection'"
    mock_response.data = {'name': 'new_collection'}
    mock_response.error = None
    mock_command.create_collection.return_value = mock_response

    create_collection(mock_command, mock_args)

    expected_config = {
        'numShards': 2,
        'replicationFactor': 2,
        'config_set': 'my_config'
    }
    mock_command.create_collection.assert_called_once_with(name="new_collection", **expected_config)
    assert "Creating collection 'new_collection'" in caplog.text
    
    # Find the log message and parse the JSON
    config_log_found = False
    for record in caplog.records:
        if record.levelname == 'INFO' and "Using configuration:" in record.message:
            json_part = record.message.split("Using configuration:", 1)[1].strip()
            logged_config = json.loads(json_part)
            assert logged_config == expected_config
            config_log_found = True
            break
    assert config_log_found, "Configuration log message not found or JSON mismatch"

    assert "Created collection 'new_collection'" in caplog.text

def test_create_collection_missing_name(mock_command, mock_args, caplog):
    """Test creation attempt with missing collection name."""
    caplog.set_level(logging.ERROR)
    mock_args.collection = None

    create_collection(mock_command, mock_args)

    mock_command.create_collection.assert_not_called()
    assert "Collection name is required" in caplog.text

def test_create_collection_command_failure(mock_command, mock_args, caplog):
    """Test handling failure from SolrCommand.create_collection."""
    caplog.set_level(logging.ERROR)
    mock_response = MagicMock()
    mock_response.success = False
    mock_response.error = "Collection already exists"
    mock_command.create_collection.return_value = mock_response

    create_collection(mock_command, mock_args)

    mock_command.create_collection.assert_called_once_with(name="new_collection")
    assert "Failed to create collection: Collection already exists" in caplog.text

def test_create_collection_unexpected_exception(mock_command, mock_args, caplog):
    """Test handling unexpected exception during creation."""
    caplog.set_level(logging.ERROR)
    mock_command.create_collection.side_effect = ConnectionError("Solr down")

    create_collection(mock_command, mock_args)

    mock_command.create_collection.assert_called_once_with(name="new_collection")
    assert "Failed to create collection: Solr down" in caplog.text 