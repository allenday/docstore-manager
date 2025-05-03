"""Base classes for command execution."""

import abc
from typing import Any, Dict, Optional
import argparse # Keep for potential use in underlying commands initially
import click

# Assuming Response might be useful for command results
from docstore_manager.core.response import Response 
# Assuming the client base class might be needed by commands
from docstore_manager.core.client import DocumentStoreClient 

class CommandResponse(Response):
    """Specialized response object for command results (can be extended)."""
    # Add command-specific fields if needed later
    pass

class DocumentStoreCommand(abc.ABC):
    """Abstract base class for document store command implementations."""

    @abc.abstractmethod
    def execute(self, client: DocumentStoreClient, **kwargs) -> CommandResponse:
        """Execute the command logic.
        
        Args:
            client: An initialized DocumentStoreClient instance.
            **kwargs: Command-specific arguments derived from Click options/args.
            
        Returns:
            A CommandResponse object containing the result.
        """
        raise NotImplementedError
        
    # Optional: Add helper methods common to command execution if needed

__all__ = ["DocumentStoreCommand", "CommandResponse"] 