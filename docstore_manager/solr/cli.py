#!/usr/bin/env python3
"""
Solr Manager - CLI tool for managing Solr collections.

Provides commands to create, delete, list and modify collections, as well as perform
batch operations on documents within collections.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Any

try:
    import pysolr
except ImportError:
    print("Error: pysolr is not installed. Please run: pip install pysolr")
    sys.exit(1)

from ..common.cli import DocumentStoreCLI
from ..common.exceptions import ConfigurationError
from .config import get_profiles, get_config_dir
from .utils import initialize_solr_client, load_configuration
from .command import SolrCommand
from .commands.create import create_collection
from .commands.delete import delete_collection
from .commands.list import list_collections
from .commands.info import collection_info
from .commands.batch import batch_add, batch_delete
from .commands.get import get_documents
from .commands.config import show_config_info

class SolrCLI(DocumentStoreCLI):
    """Solr-specific CLI implementation."""
    
    def __init__(self):
        super().__init__("Solr Manager - CLI tool for managing SolrCloud collections and documents")
    
    def _add_connection_args(self, group: argparse._ArgumentGroup):
        """Add Solr-specific connection arguments."""
        group.add_argument(
            "--solr-url",
            help="Base Solr URL (e.g., http://localhost:8983/solr). Overrides config."
        )
        group.add_argument(
            "--zk-hosts",
            help="ZooKeeper host string (e.g., zk1:2181,zk2:2181/solr). Overrides config."
        )
        group.add_argument(
            "--username",
            help="Username for Solr authentication. Overrides config."
        )
        group.add_argument(
            "--password",
            help="Password for Solr authentication. Overrides config."
        )
        group.add_argument(
            "--timeout",
            type=int,
            help="Connection timeout in seconds (default: 30). Overrides config."
        )
    
    def _add_create_args(self, group: argparse._ArgumentGroup):
        """Add Solr-specific collection creation arguments."""
        group.add_argument(
            "--num-shards",
            type=int,
            default=1,
            help="Number of shards for the new collection (default: 1)"
        )
        group.add_argument(
            "--replication-factor",
            type=int,
            default=1,
            help="Replication factor for the new collection (default: 1)"
        )
        group.add_argument(
            "--configset",
            help="Name of the configSet to use for the new collection (e.g., _default)"
        )
        group.add_argument(
            "--overwrite",
            action="store_true",
            help="Delete existing collection with the same name before creating"
        )
    
    def _add_batch_args(self, group: argparse._ArgumentGroup):
        """Add Solr-specific batch operation arguments."""
        # Document selection
        doc_selector = group.add_mutually_exclusive_group(required=False)
        doc_selector.add_argument(
            "--id-file",
            help="Path to a file containing document IDs, one per line (for --delete-docs)"
        )
        doc_selector.add_argument(
            "--ids",
            help="Comma-separated list of document IDs (for --delete-docs)"
        )
        doc_selector.add_argument(
            "--query",
            help="Solr query string to select documents (e.g., 'category:product AND inStock:true')"
        )
        
        # Operation type
        op_type = group.add_mutually_exclusive_group(required=False)
        op_type.add_argument(
            "--add-update",
            action="store_true",
            help="Add/update documents using the provided --doc data (JSON format)"
        )
        op_type.add_argument(
            "--delete-docs",
            action="store_true",
            help="Delete documents matching --query, --ids, or --id-file"
        )
        
        # Batch parameters
        group.add_argument(
            "--doc",
            help="JSON string containing a single document or a list of documents for --add-update (e.g., '{\"id\":\"1\", \"field\":\"val\"}' or '[{\"id\":\"1\"}, {\"id\":\"2\"}]')"
        )
        group.add_argument(
            "--commit",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Perform a Solr commit after the batch operation (default: True)"
        )
        group.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Number of documents to send per batch request (for --add-update with large data)"
        )
    
    def _add_get_args(self, group: argparse._ArgumentGroup):
        """Add Solr-specific document retrieval arguments."""
        # Document selection for 'get'
        get_selector = group.add_mutually_exclusive_group(required=False)
        get_selector.add_argument(
            "--id-file-get",
            dest="id_file",
            help="Path to a file containing document IDs, one per line"
        )
        get_selector.add_argument(
            "--ids-get",
            dest="ids",
            help="Comma-separated list of document IDs"
        )
        get_selector.add_argument(
            "--query-get",
            dest="query",
            help="Solr query string to select documents (default: *:*)"
        )
        
        # Get parameters
        group.add_argument(
            "--fields",
            default="*",
            help="Comma-separated list of fields to retrieve (default: *)"
        )
        group.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum number of documents to retrieve (default: 10)"
        )
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
    
    def initialize_client(self, args: argparse.Namespace) -> Any:
        """Initialize and return a Solr client."""
        config = load_configuration(args)
        solr_url = config.get('solr_url')
        zk_hosts = config.get('zk_hosts')
        if not solr_url and not zk_hosts:
            raise ConfigurationError(
                "Either solr_url or zk_hosts must be provided",
                details={'config_keys': list(config.keys())}
            )
        return SolrCommand(solr_url=solr_url, zk_hosts=zk_hosts)
    
    def handle_create(self, client: Any, args: argparse.Namespace):
        """Handle the create command."""
        create_collection(client, args)
    
    def handle_delete(self, client: Any, args: argparse.Namespace):
        """Handle the delete command."""
        delete_collection(client, args)
    
    def handle_list(self, client: Any, args: argparse.Namespace):
        """Handle the list command."""
        list_collections(client, args)
    
    def handle_info(self, client: Any, args: argparse.Namespace):
        """Handle the info command."""
        collection_info(client, args)
    
    def handle_batch(self, client: Any, args: argparse.Namespace):
        """Handle the batch command."""
        if args.add_update:
            batch_add(client, args)
        elif args.delete_docs:
            batch_delete(client, args)
        else:
            raise ValueError("Either --add-update or --delete-docs must be specified")
    
    def handle_get(self, client: Any, args: argparse.Namespace):
        """Handle the get command."""
        get_documents(client, args)
    
    def handle_config(self, args: argparse.Namespace):
        """Handle the config command."""
        show_config_info(args)

def main():
    """Main entry point."""
    cli = SolrCLI()
    cli.run()

if __name__ == "__main__":
    main()