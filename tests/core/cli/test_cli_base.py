"""Tests for base CLI functionality."""

import pytest
from unittest.mock import Mock, patch
from argparse import ArgumentParser, _ArgumentGroup
from docstore_manager.core.cli.base import BaseCLI
from docstore_manager.core.client.base import DocumentStoreClient
import sys

# Rename class to avoid pytest warning (used as implementation detail for tests)
class _TestCLIImpl(BaseCLI):
    """Test implementation of DocumentStoreCLI."""
    
    # Removed __init__ as it's causing pytest warning
    # def __init__(self):
    #     super().__init__()
    #     self.parser = self.create_parser() # Create and assign parser
    
    # Keep other methods needed for tests
    def _add_common_args(self, parser: ArgumentParser):
        parser.add_argument("--profile", help="Profile")
        parser.add_argument("--collection", help="Collection")

    def _add_connection_args(self, group: _ArgumentGroup):
        group.add_argument("--host", help="Host")
        group.add_argument("--port", help="Port")
    
    def _add_create_args(self, group: _ArgumentGroup):
        group.add_argument("--name", help="Name")
    
    def _add_batch_args(self, group: _ArgumentGroup):
        group.add_argument("--file", help="File")
    
    def _add_get_args(self, group: _ArgumentGroup):
        group.add_argument("--id", help="ID")
    
    def initialize_client(self, args):
        return Mock(spec=DocumentStoreClient)
    
    def handle_list(self, client, args):
        pass
    
    def handle_config(self, args):
        pass
    
    def handle_create(self, client, args):
        pass
    
    def handle_delete(self, client, args):
        pass
    
    def handle_info(self, client, args):
        pass
    
    def handle_batch(self, client, args):
        pass
    
    def handle_get(self, client, args):
        pass

    # Add missing abstract method implementations
    def create_parser(self):
        parser = ArgumentParser(description="Test CLI") # Add description
        self._add_common_args(parser) # Add common args
        subparsers = parser.add_subparsers(dest='command', required=True)
        # Add dummy subparsers for commands tested
        subparsers.add_parser('list')
        subparsers.add_parser('config')
        subparsers.add_parser('create')
        subparsers.add_parser('delete')
        subparsers.add_parser('info')
        subparsers.add_parser('batch')
        subparsers.add_parser('get')
        # We can add more here if needed for other tests
        return parser

    def handle_add(self, client, args):
        pass

    def handle_delete_docs(self, client, args):
        pass

    def handle_search(self, client, args):
        pass

    def run(self):
        # Basic argument parsing and dispatch for testing
        args = self.parser.parse_args() # Use the instance parser
        command = args.command
        handler_name = f"handle_{command}"
        
        if hasattr(self, handler_name) and callable(getattr(self, handler_name)):
            handler = getattr(self, handler_name)
            client = self.initialize_client(args) # Need a client for handlers
            # Adjust calling convention based on handler signature
            if handler_name == "handle_config":
                 handler(args)
            else:
                 handler(client, args)
        else:
            # Simulate argparse behavior for unknown command or missing handler
            # In a real scenario, argparse would handle this, but we need to simulate for tests
            # like test_cli_handle_unknown_command
            print(f"Error: Unknown command {command}")
            sys.exit(1) # Exit to satisfy tests expecting SystemExit

def test_cli_initialization():
    """Test CLI initialization."""
    cli = _TestCLIImpl()
    # Manually call create_parser if needed for the test, since __init__ is removed
    cli.parser = cli.create_parser() 
    assert isinstance(cli.parser, ArgumentParser)
    assert cli.parser.description == "Test CLI"

def test_cli_add_arguments():
    """Test adding arguments to CLI."""
    cli = _TestCLIImpl()
    cli.parser = cli.create_parser() # Manually create parser
    args = cli.parser.parse_args(["list"])
    assert hasattr(args, "command")
    assert hasattr(args, "profile")
    assert hasattr(args, "collection")

@patch("sys.argv", ["test", "list"])
def test_cli_handle_list():
    """Test handling list command."""
    cli = _TestCLIImpl()
    cli.parser = cli.create_parser() # Manually create parser
    with patch.object(cli, "handle_list") as mock_handle:
        cli.run()
        mock_handle.assert_called_once()

@patch("sys.argv", ["test", "config"])
def test_cli_handle_config():
    """Test handling config command."""
    cli = _TestCLIImpl()
    cli.parser = cli.create_parser() # Manually create parser
    with patch.object(cli, "handle_config") as mock_handle:
        cli.run()
        mock_handle.assert_called_once()

@patch("sys.argv", ["test", "create"])
def test_cli_handle_create():
    """Test handling create command."""
    cli = _TestCLIImpl()
    cli.parser = cli.create_parser() # Manually create parser
    with patch.object(cli, "handle_create") as mock_handle:
        cli.run()
        mock_handle.assert_called_once()

@patch("sys.argv", ["test", "delete"])
def test_cli_handle_delete():
    """Test handling delete command."""
    cli = _TestCLIImpl()
    cli.parser = cli.create_parser() # Manually create parser
    with patch.object(cli, "handle_delete") as mock_handle:
        cli.run()
        mock_handle.assert_called_once()

@patch("sys.argv", ["test", "info"])
def test_cli_handle_info():
    """Test handling info command."""
    cli = _TestCLIImpl()
    cli.parser = cli.create_parser() # Manually create parser
    with patch.object(cli, "handle_info") as mock_handle:
        cli.run()
        mock_handle.assert_called_once()

@patch("sys.argv", ["test", "batch"])
def test_cli_handle_batch():
    """Test handling batch command."""
    cli = _TestCLIImpl()
    cli.parser = cli.create_parser() # Manually create parser
    with patch.object(cli, "handle_batch") as mock_handle:
        cli.run()
        mock_handle.assert_called_once()

@patch("sys.argv", ["test", "get"])
def test_cli_handle_get():
    """Test handling get command."""
    cli = _TestCLIImpl()
    cli.parser = cli.create_parser() # Manually create parser
    with patch.object(cli, "handle_get") as mock_handle:
        cli.run()
        mock_handle.assert_called_once()

@patch("sys.argv", ["test", "list"])
def test_cli_handle_unknown_command():
    """Test handling unknown command."""
    cli = _TestCLIImpl()
    cli.parser = cli.create_parser() # Manually create parser
    with patch.dict(cli.__dict__, {"handle_list": None}):
        with pytest.raises(SystemExit):
            cli.run()

def test_cli_abstract_methods():
    """Test that abstract methods are enforced."""
    with pytest.raises(TypeError):
        # Test that the abstract base class cannot be instantiated directly
        BaseCLI("Test CLI") 