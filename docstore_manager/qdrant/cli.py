#!/usr/bin/env python3
"""
Qdrant Manager - CLI tool for managing Qdrant vector database collections.

Provides commands to create, delete, list and modify collections, as well as perform
batch operations on documents within collections.
"""
import os
import sys
import argparse
import logging
from pathlib import Path

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError:
    print("Error: qdrant-client is not installed. Please run: pip install qdrant-client")
    sys.exit(1)

from ..common.cli import DocumentStoreCLI
from .config import get_profiles, get_config_dir, load_configuration
from .utils import initialize_qdrant_client
from .commands.create import create_collection
from .commands.delete import delete_collection
from .commands.list_cmd import list_collections
from .commands.info import collection_info
from .commands.batch import batch_operations
from .commands.get import get_points
from .commands.config import show_config_info

class QdrantCLI(DocumentStoreCLI):
    """Qdrant-specific CLI implementation."""
    
    def __init__(self):
        super().__init__("Qdrant Manager - CLI tool for managing Qdrant vector database collections")
    
    def _add_connection_args(self, group: argparse._ArgumentGroup):
        """Add Qdrant-specific connection arguments."""
        group.add_argument(
            "--url",
            help="Qdrant server URL"
        )
        group.add_argument(
            "--port",
            type=int,
            help="Qdrant server port"
        )
        group.add_argument(
            "--api-key",
            help="Qdrant API key"
        )
    
    def _add_create_args(self, group: argparse._ArgumentGroup):
        """Add Qdrant-specific collection creation arguments."""
        group.add_argument(
            "--size",
            type=int,
            help="Vector size for the collection (uses config default if not specified)"
        )
        group.add_argument(
            "--distance",
            choices=["cosine", "euclid", "dot"],
            help="Distance function for vector similarity (uses config default if not specified)"
        )
        group.add_argument(
            "--indexing-threshold",
            type=int,
            help="Indexing threshold (number of vectors before indexing, 0 for immediate indexing)"
        )
        group.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite collection if it already exists during creation"
        )
    
    def _add_batch_args(self, group: argparse._ArgumentGroup):
        """Add Qdrant-specific batch operation arguments."""
        # Document selection
        doc_selector = group.add_mutually_exclusive_group(required=False)
        doc_selector.add_argument(
            "--id-file",
            help="Path to a file containing document IDs, one per line"
        )
        doc_selector.add_argument(
            "--ids",
            help="Comma-separated list of document IDs"
        )
        doc_selector.add_argument(
            "--filter",
            help="JSON string containing Qdrant filter (e.g., '{\"key\":\"category\",\"match\":{\"value\":\"product\"}}')"
        )
        
        # Operation type
        op_type = group.add_mutually_exclusive_group(required=False)
        op_type.add_argument(
            "--add",
            action="store_true",
            help="Add/update fields in documents (merges payload)"
        )
        op_type.add_argument(
            "--delete",
            action="store_true",
            help="Delete fields from documents (requires --selector)"
        )
        op_type.add_argument(
            "--replace",
            action="store_true",
            help="Replace payload in documents (requires --selector, currently only works with --ids/--id-file)"
        )
        
        # Batch parameters
        group.add_argument(
            "--doc",
            help="JSON string containing document payload data for add/replace operations (e.g., '{\"field1\":\"value1\"}')"
        )
        group.add_argument(
            "--selector",
            help="""JSON path selector for where to add/delete/replace fields (e.g., 'metadata.author').
Required for --delete and --replace.
For --add, if omitted, adds to root; if provided, adds under that key."""
        )
        group.add_argument(
            "--limit",
            type=int,
            default=10000,
            help="Maximum number of points to process for --filter in 'batch' or retrieve in 'get' (default: 10000 for batch, 10 for get)"
        )
    
    def _add_get_args(self, group: argparse._ArgumentGroup):
        """Add Qdrant-specific document retrieval arguments."""
        group.add_argument(
            "--format",
            choices=["json", "csv"],
            default="json",
            help="Output format (default: json)"
        )
        group.add_argument(
            "--output",
            help="Output file path (prints to stdout if not specified)"
        )
        group.add_argument(
            "--with-vectors",
            action="store_true",
            help="Include vector data in output (default: False)"
        )
    
    def initialize_client(self, args: argparse.Namespace) -> QdrantClient:
        """Initialize and return a Qdrant client."""
        return initialize_qdrant_client(args)
    
    def handle_create(self, client: QdrantClient, args: argparse.Namespace):
        """Handle the create command."""
        create_collection(client, args)
    
    def handle_delete(self, client: QdrantClient, args: argparse.Namespace):
        """Handle the delete command."""
        delete_collection(client, args)
    
    def handle_list(self, client: QdrantClient, args: argparse.Namespace):
        """Handle the list command."""
        list_collections(client, args)
    
    def handle_info(self, client: QdrantClient, args: argparse.Namespace):
        """Handle the info command."""
        collection_info(client, args)
    
    def handle_batch(self, client: QdrantClient, args: argparse.Namespace):
        """Handle the batch command."""
        batch_operations(client, args)
    
    def handle_get(self, client: QdrantClient, args: argparse.Namespace):
        """Handle the get command."""
        get_points(client, args)
    
    def handle_config(self, args: argparse.Namespace):
        """Handle the config command."""
        show_config_info(args)

def main():
    """Main entry point."""
    cli = QdrantCLI()
    cli.run()

if __name__ == "__main__":
    main()