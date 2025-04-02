"""
Base CLI interface for document store managers.

This module provides a common CLI structure that can be inherited by specific
document store implementations (e.g., Qdrant, Solr).
"""
import argparse
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from ..logging import setup_logging

# Configure logging
logger = logging.getLogger(__name__)

class DocumentStoreCLI(ABC):
    """Base class for document store CLI implementations."""
    
    def __init__(self, description: str):
        """Initialize the CLI with a description.
        
        Args:
            description: Description of the CLI tool
        """
        setup_logging()  # Initialize logging with common configuration
        self.parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.RawTextHelpFormatter
        )
        self._add_arguments()
    
    def _add_arguments(self):
        """Add common arguments to the parser."""
        # Command argument
        self.parser.add_argument(
            "command",
            choices=["create", "delete", "list", "info", "batch", "config", "get"],
            help="""Command to execute:
  create: Create a new collection
  delete: Delete an existing collection
  list: List all collections
  info: Get detailed information about a collection
  batch: Perform batch operations on documents
  config: View or modify configuration
  get: Retrieve documents from a collection"""
        )
        
        # Connection arguments
        connection_args = self.parser.add_argument_group('Connection Options')
        connection_args.add_argument(
            "--profile",
            help="Configuration profile to use"
        )
        self._add_connection_args(connection_args)
        
        # Collection argument
        self.parser.add_argument(
            "--collection",
            help="Collection name (defaults to value from config)"
        )
        
        # Collection creation arguments
        create_args = self.parser.add_argument_group("Collection Creation Options (for 'create')")
        self._add_create_args(create_args)
        
        # Batch operation arguments
        batch_group = self.parser.add_argument_group("Batch Operation Options (for 'batch')")
        self._add_batch_args(batch_group)
        
        # Get/Retrieve arguments
        get_params = self.parser.add_argument_group("Get/Retrieve Options (for 'get')")
        self._add_get_args(get_params)
    
    @abstractmethod
    def _add_connection_args(self, group: argparse._ArgumentGroup):
        """Add connection-specific arguments.
        
        Args:
            group: ArgumentGroup to add arguments to
        """
        pass
    
    @abstractmethod
    def _add_create_args(self, group: argparse._ArgumentGroup):
        """Add collection creation arguments.
        
        Args:
            group: ArgumentGroup to add arguments to
        """
        pass
    
    @abstractmethod
    def _add_batch_args(self, group: argparse._ArgumentGroup):
        """Add batch operation arguments.
        
        Args:
            group: ArgumentGroup to add arguments to
        """
        pass
    
    @abstractmethod
    def _add_get_args(self, group: argparse._ArgumentGroup):
        """Add document retrieval arguments.
        
        Args:
            group: ArgumentGroup to add arguments to
        """
        pass
    
    @abstractmethod
    def initialize_client(self, args: argparse.Namespace) -> Any:
        """Initialize and return a client for the document store.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Any: Initialized client object
        """
        pass
    
    @abstractmethod
    def handle_create(self, client: Any, args: argparse.Namespace):
        """Handle the create command.
        
        Args:
            client: Initialized client
            args: Parsed command line arguments
        """
        pass
    
    @abstractmethod
    def handle_delete(self, client: Any, args: argparse.Namespace):
        """Handle the delete command.
        
        Args:
            client: Initialized client
            args: Parsed command line arguments
        """
        pass
    
    @abstractmethod
    def handle_list(self, client: Any, args: argparse.Namespace):
        """Handle the list command.
        
        Args:
            client: Initialized client
            args: Parsed command line arguments
        """
        pass
    
    @abstractmethod
    def handle_info(self, client: Any, args: argparse.Namespace):
        """Handle the info command.
        
        Args:
            client: Initialized client
            args: Parsed command line arguments
        """
        pass
    
    @abstractmethod
    def handle_batch(self, client: Any, args: argparse.Namespace):
        """Handle the batch command.
        
        Args:
            client: Initialized client
            args: Parsed command line arguments
        """
        pass
    
    @abstractmethod
    def handle_get(self, client: Any, args: argparse.Namespace):
        """Handle the get command.
        
        Args:
            client: Initialized client
            args: Parsed command line arguments
        """
        pass
    
    @abstractmethod
    def handle_config(self, args: argparse.Namespace):
        """Handle the config command.
        
        Args:
            args: Parsed command line arguments
        """
        pass
    
    def run(self):
        """Run the CLI application."""
        args = self.parser.parse_args()
        
        # Handle config command separately (doesn't need client)
        if args.command == "config":
            return self.handle_config(args)
        
        # Initialize client for other commands
        client = self.initialize_client(args)
        
        # Dispatch to appropriate handler
        command_handlers = {
            "create": self.handle_create,
            "delete": self.handle_delete,
            "list": self.handle_list,
            "info": self.handle_info,
            "batch": self.handle_batch,
            "get": self.handle_get
        }
        
        handler = command_handlers.get(args.command)
        if handler:
            handler(client, args)
        else:
            self.parser.error(f"Unknown command: {args.command}") 