"""
Base CLI interface for document store managers.

This module provides a common CLI structure that can be inherited by specific
document store implementations (e.g., Qdrant, Solr).
"""
import argparse
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from docstore_manager.core.logging import setup_logging

# Configure logging
logger = logging.getLogger(__name__)

class BaseCLI(ABC):
    """Base class for document store CLI implementations."""
    
    def __init__(self):
        """Initialize the CLI."""
        setup_logging()  # Initialize logging with common configuration
    
    @abstractmethod
    def create_parser(self) -> argparse.ArgumentParser:
        """Create and return an argument parser.
        
        Returns:
            argparse.ArgumentParser: Configured argument parser
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
    def handle_list(self, client: Any, args: argparse.Namespace) -> None:
        """Handle the list command.
        
        Args:
            client: Initialized client
            args: Parsed command line arguments
        """
        pass
    
    @abstractmethod
    def handle_create(self, client: Any, args: argparse.Namespace) -> None:
        """Handle the create command.
        
        Args:
            client: Initialized client
            args: Parsed command line arguments
        """
        pass
    
    @abstractmethod
    def handle_delete(self, client: Any, args: argparse.Namespace) -> None:
        """Handle the delete command.
        
        Args:
            client: Initialized client
            args: Parsed command line arguments
        """
        pass
    
    @abstractmethod
    def handle_info(self, client: Any, args: argparse.Namespace) -> None:
        """Handle the info command.
        
        Args:
            client: Initialized client
            args: Parsed command line arguments
        """
        pass
    
    @abstractmethod
    def handle_add(self, client: Any, args: argparse.Namespace) -> None:
        """Handle the add command.
        
        Args:
            client: Initialized client
            args: Parsed command line arguments
        """
        pass
    
    @abstractmethod
    def handle_delete_docs(self, client: Any, args: argparse.Namespace) -> None:
        """Handle the delete-docs command.
        
        Args:
            client: Initialized client
            args: Parsed command line arguments
        """
        pass
    
    @abstractmethod
    def handle_search(self, client: Any, args: argparse.Namespace) -> None:
        """Handle the search command.
        
        Args:
            client: Initialized client
            args: Parsed command line arguments
        """
        pass
    
    @abstractmethod
    def handle_get(self, client: Any, args: argparse.Namespace) -> None:
        """Handle the get command.
        
        Args:
            client: Initialized client
            args: Parsed command line arguments
        """
        pass
    
    @abstractmethod
    def run(self) -> None:
        """Run the CLI application."""
        pass 