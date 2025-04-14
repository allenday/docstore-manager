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
from typing import Any, Optional

try:
    import pysolr
except ImportError:
    print("Error: pysolr is not installed. Please run: pip install pysolr")
    sys.exit(1)

from ..common.cli import BaseCLI
from ..common.exceptions import ConfigurationError, ConnectionError
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

logger = logging.getLogger(__name__)

class SolrCLI(BaseCLI):
    """CLI implementation for Solr document store."""
    
    def __init__(self):
        super().__init__()
        self.command_handler: Optional[SolrCommand] = None
    
    def _add_connection_args(self, group: argparse._ArgumentGroup):
        """Add Solr-specific connection arguments."""
        group.add_argument(
            "--solr-url",
            help="Specify the base Solr URL (e.g., http://localhost:8983/solr). Overrides config file settings."
        )
        group.add_argument(
            "--zk-hosts",
            help="Specify the ZooKeeper host string for SolrCloud (e.g., zk1:2181,zk2:2181/solr). Overrides config."
        )
        group.add_argument(
            "--username",
            help="Provide the username for Solr authentication. Overrides config."
        )
        group.add_argument(
            "--password",
            help="Provide the password for Solr authentication. Overrides config."
        )
        group.add_argument(
            "--timeout",
            type=int,
            help="Set the connection timeout in seconds (default: 30 from pysolr, can be set in config). Overrides config."
        )
    
    def _add_create_args(self, group: argparse._ArgumentGroup):
        """Add Solr-specific collection creation arguments."""
        group.add_argument(
            "--num-shards",
            type=int,
            help="Specify the number of shards for the new collection (Solr default usually 1)."
        )
        group.add_argument(
            "--replication-factor",
            type=int,
            help="Specify the replication factor for the new collection (Solr default usually 1)."
        )
        group.add_argument(
            "--configset",
            help="Name of the configSet (configuration template) to use for the new collection (e.g., _default). Required if not using default."
        )
        group.add_argument(
            "--overwrite",
            action="store_true",
            help="If set, deletes any existing collection with the same name before creating the new one."
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
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for Solr CLI."""
        parser = argparse.ArgumentParser(
            description="Command-line tool for managing Apache Solr collections and documents.",
            epilog="""
Usage examples:
  solr-manager --profile my-solr list
  solr-manager create my_core --configset _default --num-shards 2
  solr-manager add my_core --doc '[{\"id\":\"doc1\", \"title\":\"Hello\"}]'
  solr-manager delete-docs my_core --query \"id:doc1\"
  solr-manager get my_core --query \"*:*\" --limit 5 --fields id,title
  solr-manager info my_core
  solr-manager config --show-profiles
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Global options (mirrors qdrant-manager)
        parser.add_argument(
            "--profile",
            help="Specify the configuration profile to use (default: 'default'). See config command or file.",
            default="default"
        )
        parser.add_argument(
            "--config-file",
            dest="config_file_path",
            type=Path,
            help="Provide a path to a specific configuration file.",
            default=None
        )
        parser.add_argument(
            "--output",
            help="Specify a file path to write the command output (default: stdout).",
            default=None
        )
        parser.add_argument(
            "--format",
            choices=["json", "yaml", "csv"],
            default="json",
            help="Choose the output format for results (default: json). CSV only supported by 'get' command."
        )

        subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

        # === List Collections ===
        list_parser = subparsers.add_parser(
            "list", 
            help="List all available collections/cores in the Solr instance.",
            description="Retrieves and displays a list of all collection/core names.",
            epilog="""
Example:
  solr-manager list --profile solr-cloud
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        conn_group_list = list_parser.add_argument_group("Connection Options (Overrides config)")
        self._add_connection_args(conn_group_list)

        # === Create Collection ===
        create_parser = subparsers.add_parser(
            "create", 
            help="Create a new collection/core.",
            description="Creates a new Solr collection/core with specified parameters.",
            epilog="""
Examples:
  solr-manager create my_new_collection --configset _default --num-shards 2 --replication-factor 2
  solr-manager create another_one --configset custom_config --overwrite
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        create_parser.add_argument("name", help="The unique name for the new collection/core.")
        conn_group_create = create_parser.add_argument_group("Connection Options (Overrides config)")
        self._add_connection_args(conn_group_create)
        create_group = create_parser.add_argument_group("Creation Options")
        self._add_create_args(create_group)

        # === Delete Collection ===
        delete_parser = subparsers.add_parser(
            "delete", 
            help="Delete an existing collection/core.",
            description="Permanently removes a collection/core and all its data.",
            epilog="""
Example:
  solr-manager delete old_core --profile production-solr
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        delete_parser.add_argument("name", help="The name of the collection/core to delete.")
        conn_group_delete = delete_parser.add_argument_group("Connection Options (Overrides config)")
        self._add_connection_args(conn_group_delete)

        # === Collection Info ===
        info_parser = subparsers.add_parser(
            "info", 
            help="Get detailed information about a collection/core.",
            description="Retrieves metadata and status for a specific collection/core.",
            epilog="""
Example:
  solr-manager info my_data_core
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        info_parser.add_argument("name", help="The name of the collection/core to inspect.")
        conn_group_info = info_parser.add_argument_group("Connection Options (Overrides config)")
        self._add_connection_args(conn_group_info)
        
        # === Add Documents === 
        add_parser = subparsers.add_parser(
            "add", 
            help="Add or update documents in a collection/core.",
            description="Uploads documents to a specified collection/core. Can add new or update existing documents based on ID.",
            epilog="""
Examples:
  solr-manager add my_core --doc '{\"id\":\"1\", \"title\":\"My Doc\"}'
  solr-manager add my_core --doc '[{\"id\":\"2\"}, {\"id\":\"3\"}]'
  solr-manager add my_core --doc @./data/docs.json --batch-size 1000
  solr-manager add my_core --doc @./data/docs.jsonl --commit=false
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        add_parser.add_argument("collection", help="Name of the target collection/core.")
        add_parser.add_argument(
            "--doc",
            required=True,
            help="JSON string, path to a JSON/JSONL file (@filename) containing a single document or a list of documents."
        )
        conn_group_add = add_parser.add_argument_group("Connection Options (Overrides config)")
        self._add_connection_args(conn_group_add)
        batch_group_add = add_parser.add_argument_group("Batch Options")
        batch_group_add.add_argument(
            "--commit", 
            action=argparse.BooleanOptionalAction, 
            default=True,
            help="Perform a Solr commit after adding documents (default: True). Use --no-commit to disable."
        )
        batch_group_add.add_argument(
            "--batch-size", 
            type=int, 
            default=500,
            help="Number of documents to send per batch request, useful for large files (default: 500)."
        )

        # === Delete Documents ===
        delete_docs_parser = subparsers.add_parser(
            "delete-docs", 
            help="Delete documents from a collection/core based on IDs or a query.",
            description="Removes documents matching the specified criteria.",
            epilog="""
Examples:
  solr-manager delete-docs my_core --ids doc1,doc2,doc3
  solr-manager delete-docs my_core --id-file ./ids_to_delete.txt
  solr-manager delete-docs my_core --query \"status:obsolete AND date:[* TO NOW-1YEAR]\"
  solr-manager delete-docs my_core --query \"*:*\" --no-commit # Delete all, no commit yet
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        delete_docs_parser.add_argument("collection", help="Name of the target collection/core.")
        conn_group_del_docs = delete_docs_parser.add_argument_group("Connection Options (Overrides config)")
        self._add_connection_args(conn_group_del_docs)
        selector_group = delete_docs_parser.add_argument_group("Document Selection (Choose ONE)")
        sel_exclusive_group = selector_group.add_mutually_exclusive_group(required=True)
        sel_exclusive_group.add_argument("--id-file", help="Path to a text file containing document IDs to delete, one ID per line.")
        sel_exclusive_group.add_argument("--ids", help="A comma-separated string of document IDs to delete.")
        sel_exclusive_group.add_argument("--query", help="A Solr query string (like \"id:X*\" or \"status:OLD\") to select documents for deletion.")
        delete_docs_parser.add_argument(
            "--commit", 
            action=argparse.BooleanOptionalAction, 
            default=True,
            help="Perform a Solr commit after deleting documents (default: True). Use --no-commit to disable."
        )

        # === Get Documents ===
        get_parser = subparsers.add_parser(
            "get", 
            help="Retrieve specific documents from a collection/core.",
            description="Fetches documents based on IDs or a query, allowing selection of specific fields.",
            epilog="""
Examples:
  solr-manager get my_core --ids doc1
  solr-manager get my_core --ids doc1,doc2,doc3 --fields id,name,price
  solr-manager get my_core --query \"category:electronics\" --limit 100 --output results.json
  solr-manager get my_core --id-file ./ids_to_fetch.txt --format csv > results.csv
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        get_parser.add_argument("collection", help="Name of the collection/core to retrieve from.")
        conn_group_get = get_parser.add_argument_group("Connection Options (Overrides config)")
        self._add_connection_args(conn_group_get)
        # Document selection for 'get'
        get_selector_group = get_parser.add_argument_group("Document Selection (Choose ONE, default is --query='*=*')")
        get_exclusive_group = get_selector_group.add_mutually_exclusive_group(required=False)
        get_exclusive_group.add_argument("--id-file", help="Path to a text file containing document IDs to retrieve, one ID per line.")
        get_exclusive_group.add_argument("--ids", help="A comma-separated string of document IDs to retrieve.")
        get_exclusive_group.add_argument("--query", default="*:*", help="A Solr query string to select documents (default: *:*). Use quotes for complex queries.")
        # Get parameters
        get_param_group = get_parser.add_argument_group("Retrieval Options")
        get_param_group.add_argument("--fields", default="*", help="Comma-separated list of fields to retrieve (default: * for all fields).")
        get_param_group.add_argument("--limit", type=int, default=10, help="Maximum number of documents to retrieve (default: 10).")
        # Output format/file are global args now

        # === Configuration Info ===
        config_parser = subparsers.add_parser(
            "config", 
            help="Show configuration information.",
            description="Displays the location of the configuration directory and lists available profiles.",
            epilog="""
Examples:
  solr-manager config
  solr-manager config --show-profiles
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        config_parser.add_argument("--show-profiles", action="store_true", help="List the names of all configured profiles.")
        # No connection args needed for config info
        
        return parser

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
    
    def handle_list(self, client: Any, args: argparse.Namespace):
        """Handle the list command."""
        list_collections(client, args)
    
    def handle_create(self, client: Any, args: argparse.Namespace):
        """Handle the create command."""
        create_collection(client, args)
    
    def handle_delete(self, client: Any, args: argparse.Namespace):
        """Handle the delete command."""
        delete_collection(client, args)
    
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

    def handle_add(self, client: Any, args: argparse.Namespace):
        """Handle the add command (maps to batch_add)."""
        batch_add(client, args)

    def handle_delete_docs(self, client: Any, args: argparse.Namespace):
        """Handle the delete-docs command (maps to batch_delete)."""
        batch_delete(client, args)

    def handle_search(self, client: Any, args: argparse.Namespace):
        """Handle the search command (maps to get_documents)."""
        get_documents(client, args)

    def run(self) -> None:
        """Parse arguments and run the selected command."""
        parser = self.create_parser()
        args = parser.parse_args()

        try:
            if args.command == "config":
                self.handle_config(args)
                return

            client = self.initialize_client(args)
            self.command_handler = client

            command_map = {
                "list": self.handle_list,
                "create": self.handle_create,
                "delete": self.handle_delete,
                "info": self.handle_info,
                "add": self.handle_add,
                "delete-docs": self.handle_delete_docs,
                "search": self.handle_search,
                "get": self.handle_get,
            }

            if args.command in command_map:
                command_map[args.command](client, args)
            else:
                parser.print_help()
                logger.error(f"Unknown command: {args.command}")
                sys.exit(1)

        except (ConfigurationError, ConnectionError, Exception) as e:
            logger.exception(f"Error during command execution: {e}")
            print(f"\nERROR: {e}", file=sys.stderr)
            sys.exit(1)

def main():
    """Main entry point."""
    cli = SolrCLI()
    cli.run()

if __name__ == "__main__":
    main()