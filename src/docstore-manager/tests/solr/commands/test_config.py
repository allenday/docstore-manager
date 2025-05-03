"""Tests for Solr config command."""

import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace
import pathlib
import sys
import yaml

from docstore_manager.solr.commands.config import show_config_info

@pytest.fixture
def mock_args():
    return Namespace(profile=None) # Default profile

@pytest.fixture
def mock_profiles():
    return {
        'default': {'solr_url': 'http://default:8983/solr'},
        'prod': {'solr_url': 'http://prod:8983/solr', 'zk_hosts': 'zk1'}
    }

@patch('docstore_manager.solr.commands.config.get_config_dir')
@patch('docstore_manager.solr.commands.config.get_profiles')
@patch('docstore_manager.solr.commands.config.load_config')
@patch('sys.exit')
@patch('pathlib.Path.exists')
def test_show_config_default_profile(mock_exists, mock_sys_exit, mock_load_config, mock_get_profiles, mock_get_config_dir, mock_args, mock_profiles, capsys):
    """Test showing config for the default profile."""
    mock_config_dir = pathlib.Path('/fake/config/dir')
    mock_get_config_dir.return_value = mock_config_dir
    mock_get_profiles.return_value = mock_profiles
    mock_exists.return_value = True

    show_config_info(mock_args)

    captured = capsys.readouterr()
    stdout = captured.out
    stderr = captured.err

    assert "Configuration Directory: /fake/config/dir" in stdout
    assert "Available Profiles:" in stdout
    assert "- default" in stdout
    assert "- prod" in stdout
    assert "Current profile (default):" in stdout
    assert "solr_url: http://default:8983/solr" in stdout
    assert "Configuration file:    /fake/config/dir/config.yaml" in stdout
    assert "Status: Configuration file exists." in stdout
    assert stderr == ""
    mock_load_config.assert_not_called() # Not called when profile arg is None
    mock_sys_exit.assert_not_called()

@patch('docstore_manager.solr.commands.config.get_config_dir')
@patch('docstore_manager.solr.commands.config.get_profiles')
@patch('docstore_manager.solr.commands.config.load_config')
@patch('sys.exit')
@patch('pathlib.Path.exists')
def test_show_config_specific_profile(mock_exists, mock_sys_exit, mock_load_config, mock_get_profiles, mock_get_config_dir, mock_args, mock_profiles, capsys):
    """Test showing config for a specific, valid profile."""
    mock_args.profile = 'prod'
    mock_config_dir = pathlib.Path('/fake/config/dir')
    mock_get_config_dir.return_value = mock_config_dir
    mock_get_profiles.return_value = mock_profiles
    mock_exists.return_value = True
    mock_load_config.return_value = mock_profiles['prod'] # Simulate successful load

    show_config_info(mock_args)

    captured = capsys.readouterr()
    stdout = captured.out
    stderr = captured.err

    assert "Configuration Directory: /fake/config/dir" in stdout
    assert "Current profile (prod):" in stdout
    assert "solr_url: http://prod:8983/solr" in stdout
    assert "zk_hosts: zk1" in stdout
    assert "Checking profile: 'prod'" in stdout
    assert "Profile 'prod' loaded successfully" in stdout
    assert stderr == ""
    mock_load_config.assert_called_once_with('prod')
    mock_sys_exit.assert_not_called()

@patch('docstore_manager.solr.commands.config.get_config_dir')
@patch('docstore_manager.solr.commands.config.get_profiles')
@patch('docstore_manager.solr.commands.config.load_config')
@patch('sys.exit')
@patch('pathlib.Path.exists')
def test_show_config_invalid_profile(mock_exists, mock_sys_exit, mock_load_config, mock_get_profiles, mock_get_config_dir, mock_args, mock_profiles, capsys):
    """Test showing config for a non-existent profile."""
    mock_args.profile = 'staging'
    mock_config_dir = pathlib.Path('/fake/config/dir')
    mock_get_config_dir.return_value = mock_config_dir
    mock_get_profiles.return_value = mock_profiles
    mock_exists.return_value = True
    mock_load_config.side_effect = SystemExit(1) # Simulate load_config failing

    show_config_info(mock_args)

    captured = capsys.readouterr()
    stdout = captured.out
    stderr = captured.err

    assert "Current profile (staging):" in stdout
    assert "Error: Profile 'staging' not found" in stderr # Error printed by show_config_info
    assert "Checking profile: 'staging'" in stdout
    # assert "Profile 'staging' loaded successfully" not in stdout
    mock_load_config.assert_called_once_with('staging') # load_config is still called for validation
    mock_sys_exit.assert_called_once_with(1)

@patch('docstore_manager.solr.commands.config.get_config_dir')
@patch('docstore_manager.solr.commands.config.get_profiles')
@patch('docstore_manager.solr.commands.config.load_config')
@patch('sys.exit')
@patch('pathlib.Path.exists')
def test_show_config_get_profiles_none(mock_exists, mock_sys_exit, mock_load_config, mock_get_profiles, mock_get_config_dir, mock_args, capsys):
    """Test when get_profiles returns None (config load failed)."""
    mock_config_dir = pathlib.Path('/fake/config/dir')
    mock_get_config_dir.return_value = mock_config_dir
    mock_get_profiles.return_value = None # Simulate failure
    mock_exists.return_value = False # Config likely doesn't exist if profiles couldn't load

    show_config_info(mock_args)

    captured = capsys.readouterr()
    stdout = captured.out
    stderr = captured.err

    assert "Error: Could not load profiles" in stderr
    assert "Available Profiles:" not in stdout
    assert "Current profile (default):" not in stdout
    # Still shows config file path and status
    assert "Configuration file:    /fake/config/dir/config.yaml" in stdout
    assert "Status: Configuration file does NOT exist." in stdout 
    mock_load_config.assert_not_called()
    mock_sys_exit.assert_called_once_with(1)

@patch('docstore_manager.solr.commands.config.get_config_dir')
@patch('docstore_manager.solr.commands.config.get_profiles')
@patch('docstore_manager.solr.commands.config.load_config')
@patch('sys.exit')
@patch('pathlib.Path.exists')
def test_show_config_load_config_exception(mock_exists, mock_sys_exit, mock_load_config, mock_get_profiles, mock_get_config_dir, mock_args, mock_profiles, capsys):
    """Test when load_config raises an unexpected exception during validation."""
    mock_args.profile = 'prod'
    mock_config_dir = pathlib.Path('/fake/config/dir')
    mock_get_config_dir.return_value = mock_config_dir
    mock_get_profiles.return_value = mock_profiles
    mock_exists.return_value = True
    mock_load_config.side_effect = yaml.YAMLError("Bad YAML") # Simulate load_config failing

    show_config_info(mock_args)

    captured = capsys.readouterr()
    stdout = captured.out
    stderr = captured.err

    assert "Current profile (prod):" in stdout
    assert "Checking profile: 'prod'" in stdout
    assert "Could not load profile 'prod': Bad YAML" in stderr
    mock_load_config.assert_called_once_with('prod')
    mock_sys_exit.assert_not_called() # Should not exit on unexpected load error

@patch('docstore_manager.solr.commands.config.get_config_dir')
@patch('docstore_manager.solr.commands.config.get_profiles')
@patch('docstore_manager.solr.commands.config.load_config')
@patch('sys.exit')
@patch('pathlib.Path.exists')
def test_show_config_file_does_not_exist(mock_exists, mock_sys_exit, mock_load_config, mock_get_profiles, mock_get_config_dir, mock_args, mock_profiles, capsys):
    """Test output when config file does not exist."""
    mock_config_dir = pathlib.Path('/fake/config/dir')
    mock_get_config_dir.return_value = mock_config_dir
    mock_get_profiles.return_value = mock_profiles # Assume profiles can still be loaded (e.g., from defaults)
    mock_exists.return_value = False

    show_config_info(mock_args)

    captured = capsys.readouterr()
    stdout = captured.out
    stderr = captured.err

    assert "Configuration file:    /fake/config/dir/config.yaml" in stdout
    assert "Status: Configuration file does NOT exist." in stdout
    assert "Run any other command" in stdout
    assert stderr == ""
    mock_sys_exit.assert_not_called() 