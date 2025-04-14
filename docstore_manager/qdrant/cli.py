"""Command-line interface for Qdrant operations."""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError:
    print("Error: qdrant-client is not installed. Please run: pip install qdrant-client")
    sys.exit(1)

from ..common.cli.base import BaseCLI
from ..common.config.base import get_profiles, get_config_dir, load_config
from ..common.exceptions import (
    DocumentError,
    QueryError,
    CollectionError,
    ConfigurationError,
    DocumentStoreError
)
from .command import QdrantCommand
from .client import QdrantDocumentStore
from .commands.batch import add_documents, delete_documents
from .commands.count import count_documents
from .commands.create import create_collection
from .commands.delete import delete_collection
from .commands.get import get_documents, search_documents
from .commands.info import collection_info
from .commands.list_cmd import list_collections
from .commands.scroll import scroll_documents

class QdrantCLI(BaseCLI):
    """Command-line interface for Qdrant operations."""

    def __init__(self):
        """Initialize the CLI."""
        super().__init__()
        self.parser = self.create_parser()

    def create_parser(self) -> argparse.ArgumentParser:
        """Create command-line argument parser."""
        parser = argparse.ArgumentParser(
            description="Command-line tool for managing Qdrant vector database collections and documents.",
            epilog="""
Usage examples:
  qdrant-manager --profile my-prod list
  qdrant-manager create my_collection --dimension 768 --distance Cosine
  qdrant-manager add my_collection --file documents.json --batch-size 100
  qdrant-manager search my_collection --query '{\\"vector\\": [0.1, 0.2, ...], \\"limit\\": 5}' --with-payload
  qdrant-manager info my_collection
""",
            formatter_class=argparse.RawDescriptionHelpFormatter # Allows embedding newlines in epilog
        )
        
        # Global options
        parser.add_argument(
            "--profile",
            help="Specify the configuration profile to use (default: 'default'). See config file.",
            default="default"
        )
        parser.add_argument(
            "--config",
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
            choices=["json", "yaml"],
            default="json",
            help="Choose the output format for results (default: json)."
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True) # Make command required
        
        # List collections
        list_parser = subparsers.add_parser(
            "list",
            help="List all available collections in the Qdrant instance.",
            description="Retrieves and displays a list of all collection names.",
            epilog="""
Example:
  qdrant-manager list --profile staging
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Create collection
        create_parser = subparsers.add_parser(
            "create",
            help="Create a new vector collection.",
            description="Creates a new collection with specified parameters for storing vectors.",
            epilog="""
Examples:
  qdrant-manager create my_images --dimension 512 --distance Dot
  qdrant-manager create my_embeddings --dimension 768 --distance Cosine --on-disk --hnsw-ef 200 --hnsw-m 32
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        create_parser.add_argument(
            "name",
            help="The unique name for the new collection."
        )
        create_parser.add_argument(
            "--dimension",
            type=int,
            required=True,
            help="The dimensionality of the vectors that will be stored in this collection (required)."
        )
        create_parser.add_argument(
            "--distance",
            choices=["Cosine", "Euclid", "Dot"],
            default="Cosine",
            help="The distance metric used for vector similarity search (default: Cosine)."
        )
        create_parser.add_argument(
            "--on-disk",
            action="store_true",
            help="If set, store the payload (metadata) on disk instead of in memory."
        )
        create_parser.add_argument(
            "--hnsw-ef",
            type=int,
            help="Optional HNSW graph parameter: size of the dynamic list for the nearest neighbors (ef_construct)."
        )
        create_parser.add_argument(
            "--hnsw-m",
            type=int,
            help="Optional HNSW graph parameter: maximum number of connections per node."
        )
        
        # Delete collection
        delete_parser = subparsers.add_parser(
            "delete",
            help="Delete an existing collection.",
            description="Permanently removes a collection and all its data.",
            epilog="""
Example:
  qdrant-manager delete old_collection --profile production
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        delete_parser.add_argument(
            "name",
            help="The name of the collection to delete."
        )
        
        # Get collection info
        info_parser = subparsers.add_parser(
            "info",
            help="Get detailed information about a collection.",
            description="Retrieves metadata and statistics for a specific collection.",
            epilog="""
Example:
  qdrant-manager info my_collection
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        info_parser.add_argument(
            "name",
            help="The name of the collection to inspect."
        )
        
        # Add documents
        add_parser = subparsers.add_parser(
            "add",
            help="Add or update documents in a collection.",
            description="Uploads documents (points) including vectors and payload to a specified collection. Can be used for both adding new documents and updating existing ones.",
            epilog="""
Examples:
  qdrant-manager add my_collection --file ./data/docs_to_add.json
  qdrant-manager add my_collection --docs '[{\\"id\\": 1, \\"vector\\": [0.1, ...], \\"payload\\": {\\"meta\\": \\"data\\"}}]'
  qdrant-manager add large_collection --file massive_dataset.jsonl --batch-size 500
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        add_parser.add_argument(
            "collection",
            help="The name of the collection to add documents to."
        )
        add_parser.add_argument(
            "--file",
            type=Path,
            help="Path to a JSON or JSON Lines (.jsonl) file containing a list of documents (points) to add."
        )
        add_parser.add_argument(
            "--docs",
            help="A JSON string representing a list of documents (points) to add."
        )
        add_parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Number of documents to upload in each batch (default: 50)."
        )
        
        # Delete documents
        delete_docs_parser = subparsers.add_parser(
            "delete-docs",
            help="Delete specific documents from a collection by ID.",
            description="Removes documents from a collection based on a list of their IDs.",
             epilog="""
Examples:
  qdrant-manager delete-docs my_collection --ids 123,456,789
  qdrant-manager delete-docs my_collection --file ./ids_to_remove.txt
  qdrant-manager delete-docs sensitive_data --ids 101,202 --batch-size 10
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
       )
        delete_docs_parser.add_argument(
            "collection",
            help="The name of the collection from which to delete documents."
        )
        delete_docs_parser.add_argument(
            "--file",
            type=Path,
            help="Path to a text file containing document IDs to delete, one ID per line."
        )
        delete_docs_parser.add_argument(
            "--ids",
            help="A comma-separated string of document IDs to delete."
        )
        delete_docs_parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Number of documents to delete in each batch (default: 50)."
        )
        
        # Search documents
        search_parser = subparsers.add_parser(
            "search",
            help="Search for similar documents in a collection.",
            description="Performs a vector similarity search based on a query vector and optional filters.",
            epilog="""
Example Query Format:
{
  \"vector\": [0.1, 0.2, 0.3, ...],  // The query vector
  \"filter\": {                      // Optional filter conditions (see Qdrant docs)
    \"must\": [
      {\"key\": \"metadata.year\", \"range\": {\"gte\": 2020}}
    ]
  },
  \"limit\": 10                     // Optional limit (overrides --limit flag)
}

Examples:
  qdrant-manager search my_collection --query '{\\"vector\\": [0.9, ...]}' --limit 5
  qdrant-manager search my_collection --query '{\\"vector\\": [0.1, ...], \\"filter\\": {\\"must\\": [ ... ]}}' --with-payload --with-vectors
  qdrant-manager search my_collection --query \"$(cat query.json)\" --output results.json
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        search_parser.add_argument(
            "collection",
            help="The name of the collection to search within."
        )
        search_parser.add_argument(
            "--query",
            required=True,
            help="A JSON string representing the search query, typically including a 'vector' and optionally 'filter' and 'limit'. See epilog for format."
        )
        search_parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum number of search results to return (default: 10). Can be overridden within the --query JSON."
        )
        search_parser.add_argument(
            "--with-vectors",
            action="store_true",
            help="If set, include the document vectors in the search results."
        )
        search_parser.add_argument(
            "--with-payload",
            action="store_true",
            help="If set, include the document payloads (metadata) in the search results."
        )
        
        # Scroll documents
        scroll_parser = subparsers.add_parser(
            "scroll",
            help="Iterate through all documents in a collection.",
            description="Retrieves documents sequentially using a scroll API, useful for fetching large datasets.",
            epilog="""
Examples:
  # Get first 50 docs
  qdrant-manager scroll my_collection --batch-size 50 --with-payload > batch1.json

  # Get next batch (assuming output contains 'next_page_offset')
  OFFSET=$(jq -r '.next_page_offset // empty' batch1.json)
  qdrant-manager scroll my_collection --batch-size 50 --with-payload --offset \"$OFFSET\" > batch2.json
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        scroll_parser.add_argument(
            "collection",
            help="The name of the collection to scroll through."
        )
        scroll_parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Number of documents to retrieve in each scroll request (default: 50)."
        )
        scroll_parser.add_argument(
            "--with-vectors",
            action="store_true",
            help="If set, include document vectors in the response."
        )
        scroll_parser.add_argument(
            "--with-payload",
            action="store_true",
            help="If set, include document payloads (metadata) in the response."
        )
        scroll_parser.add_argument(
            "--offset",
            type=str, # Keep as string, needs JSON parsing later
            help="The scroll offset ID (from previous response's 'next_page_offset') to continue scrolling. Should be a JSON string or object."
        )
        scroll_parser.add_argument(
            "--limit", # Added limit to scroll
            type=int,
            default=None, # Default to no limit (scroll all)
            help="Maximum number of documents to retrieve in total across all batches (default: no limit)."
        )
        scroll_parser.add_argument(
            "--query", # Added back the filter argument, named query for consistency
            help="Optional: A JSON string containing a 'filter' object to scroll only matching documents. See Qdrant filter documentation."
        )

        # Get documents by ID
        get_parser = subparsers.add_parser( # Renamed from get_docs to get
            "get",
            help="Retrieve specific documents by their IDs.",
            description="Fetches one or more documents directly using their unique IDs.",
            epilog="""
Examples:
  qdrant-manager get my_collection --ids 123
  qdrant-manager get my_collection --ids 101,202,303 --with-vectors
  qdrant-manager get my_collection --file ./ids_to_get.txt --output fetched_docs.json
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        get_parser.add_argument(
            "collection",
            help="The name of the collection from which to retrieve documents."
        )
        get_parser.add_argument(
            "--file",
            type=Path,
            help="Path to a text file containing document IDs to retrieve, one ID per line."
        )
        get_parser.add_argument(
            "--ids",
            help="A comma-separated string of document IDs to retrieve."
        )
        get_parser.add_argument(
            "--with-vectors",
            action="store_true",
            help="If set, include document vectors in the response."
        )
        get_parser.add_argument(
            "--with-payload", # Added with-payload for consistency
            action="store_true",
            help="If set, include document payloads (metadata) in the response."
        )

        # Count documents
        count_parser = subparsers.add_parser(
            "count",
            help="Count documents in a collection, optionally with a filter.",
            description="Returns the total number of documents in a collection, optionally matching specific filter criteria.",
            epilog="""
Example Filter Format:
{
  \"filter\": {
    \"must\": [
      {\"key\": \"metadata.category\", \"match\": {\"value\": \"news\"}}
    ]
  }
}

Examples:
  qdrant-manager count my_collection
  qdrant-manager count my_collection --query '{\\"filter\\": {\\"must\\": [...]}}'
""",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        count_parser.add_argument(
            "collection",
            help="The name of the collection to count documents in."
        )
        count_parser.add_argument(
            "--query", # Changed from --filter to --query for consistency with search
            help="Optional: A JSON string containing a 'filter' object to count only matching documents. See Qdrant filter documentation."
        )

        return parser

    def initialize_client(self, args: Any) -> QdrantCommand:
        """Initialize the Qdrant client.

        Args:
            args: Command line arguments

        Returns:
            QdrantCommand instance

        Raises:
            ConfigurationError: If client initialization fails
        """
        try:
            config = load_config(args.config, args.profile)
            # Create a new QdrantDocumentStore instance without passing config
            client = QdrantDocumentStore()
            # Initialize the client with the config
            client.create_client(config)
            command = QdrantCommand()
            command.initialize(client)
            return command
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize client: {e}")

    def handle_list(self, client: QdrantCommand, args: argparse.Namespace) -> None:
        """Handle list command."""
        list_collections(client, args)

    def handle_create(self, client: QdrantCommand, args: argparse.Namespace) -> None:
        """Handle create command."""
        create_collection(client, args)

    def handle_delete(self, client: QdrantCommand, args: argparse.Namespace) -> None:
        """Handle delete command."""
        delete_collection(client, args)

    def handle_info(self, client: QdrantCommand, args: argparse.Namespace) -> None:
        """Handle info command."""
        collection_info(client, args)

    def handle_add(self, client: QdrantCommand, args: argparse.Namespace) -> None:
        """Handle add command."""
        add_documents(client, args)

    def handle_delete_docs(self, client: QdrantCommand, args: argparse.Namespace) -> None:
        """Handle delete-docs command."""
        delete_documents(client, args)

    def handle_search(self, client: QdrantCommand, args: argparse.Namespace) -> None:
        """Handle search command."""
        search_documents(client, args)

    def handle_get(self, client: QdrantCommand, args: argparse.Namespace) -> None:
        """Handle get command."""
        get_documents(client, args)

    def handle_scroll(self, client: QdrantCommand, args: argparse.Namespace) -> None:
        """Handle scroll command."""
        scroll_documents(client, args)

    def handle_count(self, client: QdrantCommand, args: argparse.Namespace) -> None:
        """Handle count command."""
        count_documents(client, args)

    def run(self) -> None:
        """Run the CLI."""
        args = self.parser.parse_args()
        
        # Validate command before initializing client
        if not args.command:
            raise ValueError("No command specified")
        if args.command not in ["list", "create", "delete", "info", "add", "delete-docs", "search", "get", "scroll", "count"]:
            raise ValueError(f"Unknown command: {args.command}")
        
        # Validate mutually exclusive arguments
        if args.command in ["add", "delete-docs", "get"]:
            if hasattr(args, "file") and hasattr(args, "docs") and args.file and args.docs:
                print("Error: Specify either --file or --docs, not both", file=sys.stderr)
                sys.exit(1)
            if hasattr(args, "file") and hasattr(args, "ids") and args.file and args.ids:
                print("Error: Specify either --file or --ids, not both", file=sys.stderr)
                sys.exit(1)
            if not (hasattr(args, "file") and args.file) and not (hasattr(args, "docs") and args.docs) and not (hasattr(args, "ids") and args.ids):
                if args.command == "add":
                    print("Error: Either --file or --docs must be specified", file=sys.stderr)
                else:
                    print("Error: Either --file or --ids must be specified", file=sys.stderr)
                sys.exit(1)
        
        try:
            client = self.initialize_client(args)
            if args.command == "list":
                self.handle_list(client, args)
            elif args.command == "create":
                self.handle_create(client, args)
            elif args.command == "delete":
                self.handle_delete(client, args)
            elif args.command == "info":
                self.handle_info(client, args)
            elif args.command == "add":
                self.handle_add(client, args)
            elif args.command == "delete-docs":
                self.handle_delete_docs(client, args)
            elif args.command == "search":
                self.handle_search(client, args)
            elif args.command == "get":
                self.handle_get(client, args)
            elif args.command == "scroll":
                self.handle_scroll(client, args)
            elif args.command == "count":
                self.handle_count(client, args)
        except ConfigurationError as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            sys.exit(1)
        except DocumentStoreError as e:
            print(f"Document store error: {e}", file=sys.stderr)
            sys.exit(1)

def main() -> None:
    """Main entry point."""
    cli = QdrantCLI()
    cli.run()

if __name__ == "__main__":
    main() 