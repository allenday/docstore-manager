"""Command-line interface for Qdrant operations."""

import argparse
import logging
import sys
import json
from typing import Any, Optional

from ..common.cli.base import BaseCLI
from ..common.config import load_config
from ..common.exceptions import (
    ConfigurationError,
    DocumentStoreError
)
from .client import QdrantDocumentStore
from .command import QdrantCommand
from .commands.batch import add_documents, delete_documents
from .commands.count import count_documents
from .commands.create import create_collection
from .commands.delete import delete_collection
from .commands.info import collection_info
from .commands.list import list_collections
from .commands.scroll import scroll_documents
from .commands.get import get_documents
from .commands.get import search_documents


class QdrantCLI(BaseCLI):
    """CLI for interacting with Qdrant using argparse."""

    def __init__(self, config_path=None):
        # Initialize BaseCLI correctly
        super().__init__() 
        self.config_path = config_path # Keep track if needed, though BaseCLI doesn't use it
        self.client: Optional[QdrantDocumentStore] = None
        self.command_handler: Optional[QdrantCommand] = None # Add if needed like SolrCLI

    # --- Implement BaseCLI abstract methods ---

    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser with subparsers."""
        parser = argparse.ArgumentParser(description="Qdrant Document Store Manager CLI.")
        
        # Global options (can be refined later)
        parser.add_argument(
            "--profile", 
            help="Configuration profile name (default: 'default').", 
            default="default"
        )
        parser.add_argument(
            "--config-path", 
            help="Path to configuration file.", 
            default=None # Or use get_config_dir() logic
        )
        parser.add_argument(
            "--debug", 
            action="store_true", 
            help="Enable debug logging."
        )

        subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

        # --- Add subparsers for each command ---
        # Example: List command
        list_parser = subparsers.add_parser("list", help="List collections.")
        # Add arguments specific to list if any
        list_parser.add_argument("--output", type=str, help="Optional path to output the list as JSON.")

        # --- Add other subparsers (create, delete, info, add_documents, etc.) ---
        create_parser = subparsers.add_parser("create", help="Create a collection.")
        create_parser.add_argument("collection", help="Collection name.")
        # Add arguments based on original Click command and test expectations
        create_parser.add_argument("--dimension", type=int, required=True, help="Dimension of the vectors.")
        create_parser.add_argument("--distance", default="Cosine", help="Distance metric (e.g., Cosine, Euclid, Dot).")
        create_parser.add_argument("--on-disk", action="store_true", help="Store vectors on disk.")
        create_parser.add_argument("--hnsw-ef", type=int, help="HNSW ef_construct parameter.")
        create_parser.add_argument("--hnsw-m", type=int, help="HNSW M parameter.")
        # Removed placeholder: create_parser.add_argument("--vectors-config", help="JSON string or path to JSON file for vectors configuration.")
        create_parser.add_argument("--shards", type=int, help="Number of shards.")
        create_parser.add_argument("--replication-factor", type=int, help="Replication factor.")
        create_parser.add_argument("--overwrite", action="store_true", help="Overwrite if exists.")

        delete_parser = subparsers.add_parser("delete", help="Delete a collection.")
        delete_parser.add_argument("collection", help="Collection name.")
        
        info_parser = subparsers.add_parser("info", help="Get collection info.")
        info_parser.add_argument("collection", help="Collection name.")
        
        count_parser = subparsers.add_parser("count", help="Count documents.")
        count_parser.add_argument("collection", help="Collection name.")
        count_parser.add_argument("--query", help="JSON filter string for filtering count.") # Renamed from filter to match scroll/search potentially

        add_docs_parser = subparsers.add_parser("add-documents", help="Add documents.")
        add_docs_parser.add_argument("collection", help="Collection name.")
        add_docs_group = add_docs_parser.add_mutually_exclusive_group(required=True)
        # Change FileType back to str path
        add_docs_group.add_argument("--file", type=str, help="Path to JSON file containing documents.")
        add_docs_group.add_argument("--docs", help="JSON string containing documents.")
        add_docs_parser.add_argument("--batch-size", type=int, default=100)

        del_docs_parser = subparsers.add_parser("delete-documents", help="Delete documents.")
        del_docs_parser.add_argument("collection", help="Collection name.")
        del_docs_group = del_docs_parser.add_mutually_exclusive_group(required=True)
        # Change FileType back to str path
        del_docs_group.add_argument("--file", type=str, help="Path to file containing document IDs (one per line).")
        del_docs_group.add_argument("--ids", help="Comma-separated list of document IDs.")
        del_docs_parser.add_argument("--filter", help="JSON filter string to delete points.") # Qdrant uses filter for deletes
        # Add batch size argument
        del_docs_parser.add_argument("--batch-size", type=int, default=100, help="Batch size for delete operations.")

        scroll_parser = subparsers.add_parser("scroll", help="Scroll documents.")
        scroll_parser.add_argument("collection", help="Collection name.")
        scroll_parser.add_argument("--query", help="JSON filter string.") # Renamed from filter to match count
        scroll_parser.add_argument("--batch-size", type=int, default=10, help="Limit for scroll.")
        scroll_parser.add_argument("--with-vectors", action="store_true")
        scroll_parser.add_argument("--with-payload", type=lambda x: (str(x).lower() == 'true'), default=True, help="Include payload (true/false).")
        scroll_parser.add_argument("--offset", help="Scroll offset point ID.")

        # --- To Add: get, search (if distinct from get/scroll), config ---
        get_parser = subparsers.add_parser("get", help="Get specific documents by ID.")
        get_parser.add_argument("collection", help="Collection name.")
        get_ids_group = get_parser.add_mutually_exclusive_group(required=True)
        # Change FileType back to str path
        get_ids_group.add_argument("--file", type=str, help="Path to file containing document IDs (one per line).")
        get_ids_group.add_argument("--ids", help="Comma-separated list of document IDs.")
        get_parser.add_argument("--with-vectors", action="store_true")
        get_parser.add_argument("--with-payload", type=lambda x: (str(x).lower() == 'true'), default=True, help="Include payload (true/false).")
        get_parser.add_argument("--format", choices=['json'], default='json', help="Output format (currently only json).")
        get_parser.add_argument("--output", help="Output file path.")

        # Add the missing search subparser
        search_parser = subparsers.add_parser("search", help="Search documents.")
        search_parser.add_argument("collection", help="Collection name.")
        search_parser.add_argument("--query", required=True, help="JSON query string (e.g., '{\"vector\": [0.1, 0.2]}').")
        search_parser.add_argument("--limit", type=int, default=10, help="Number of results to return.")
        search_parser.add_argument("--with-vectors", action="store_true", help="Include vectors in results.")
        search_parser.add_argument("--with-payload", type=lambda x: (str(x).lower() == 'true'), default=True, help="Include payload (true/false).")
        search_parser.add_argument("--format", choices=['json'], default='json', help="Output format (currently only json).")
        search_parser.add_argument("--output", help="Output file path.")

        return parser

    def initialize_client(self, args: argparse.Namespace) -> QdrantDocumentStore:
        """Initialize and return the Qdrant client based on args."""
        if not self.client:
            try:
                # Load config based on profile/path from args
                config_data = load_config(profile=args.profile, config_path=args.config_path) 
                qdrant_config = config_data.get('qdrant', {})
                
                # Prepare the config dict expected by QdrantDocumentStore
                client_config = {}
                
                # Allow args to override config (if CLI args for host/port/etc. were added)
                # For now, just use values from the loaded qdrant_config section
                if qdrant_config.get('host') and qdrant_config.get('port'):
                    client_config['host'] = qdrant_config.get('host')
                    client_config['port'] = qdrant_config.get('port')
                elif qdrant_config.get('url'): # Prioritize URL if host/port not present
                     client_config['url'] = qdrant_config.get('url')
                # Add other relevant fields like api_key, prefer_grpc, https
                if qdrant_config.get('api_key'):
                    client_config['api_key'] = qdrant_config.get('api_key')
                if qdrant_config.get('prefer_grpc') is not None:
                    client_config['prefer_grpc'] = qdrant_config.get('prefer_grpc')
                if qdrant_config.get('https') is not None:
                     client_config['https'] = qdrant_config.get('https')
                if qdrant_config.get('timeout'):
                    client_config['timeout'] = qdrant_config.get('timeout')

                # Validate required fields before creating client
                # QdrantDocumentStore's create_client or validate_config handles detailed checks
                if not client_config.get('url') and not (client_config.get('host') and client_config.get('port')):
                     # Check for cloud URL as well if that becomes an option
                     raise ConfigurationError("Qdrant host/port or url not configured.")
                
                # Pass the prepared config dictionary
                self.client = QdrantDocumentStore(config=client_config)
                
                # Optional: Initialize command handler if used elsewhere
                # self.command_handler = QdrantCommand(self.client.client) 

            except ConfigurationError as e:
                logging.error(f"Configuration error: {e}")
                sys.exit(1)
            except Exception as e:
                # Catch potential errors during client instantiation too
                logging.error(f"Failed to initialize Qdrant client: {e}", exc_info=args.debug)
                sys.exit(1)
        return self.client

    def handle_list(self, client: QdrantDocumentStore, args: argparse.Namespace) -> None:
        """Handle the list command."""
        try:
            # Assuming list_collections needs command object
            command = QdrantCommand(client.client) 
            list_collections(command, args) # Correctly call the imported function
        except DocumentStoreError as e:
            logging.error(f"Error listing collections: {e}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error during list: {e}", exc_info=args.debug)
            sys.exit(1)

    def handle_create(self, client: QdrantDocumentStore, args: argparse.Namespace) -> None:
        logging.info(f"Handling create for collection: {args.collection}") # Changed from args.name
        try:
             command = QdrantCommand(client.client)
             # Pass args directly, create_collection should handle them
             create_collection(command, args) 
        except DocumentStoreError as e:
             logging.error(f"Error creating collection: {e}")
             sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error during create: {e}", exc_info=args.debug)
            sys.exit(1)
            
    def handle_delete(self, client: QdrantDocumentStore, args: argparse.Namespace) -> None:
        logging.info(f"Handling delete for collection: {args.collection}") # Changed from args.name
        try:
             # delete_collection expects the qdrant_client itself, not command object
             delete_collection(client.client, args) 
        except DocumentStoreError as e:
             logging.error(f"Error deleting collection: {e}")
             sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error during delete: {e}", exc_info=args.debug)
            sys.exit(1)

    def handle_info(self, client: QdrantDocumentStore, args: argparse.Namespace) -> None:
        logging.info(f"Handling info for collection: {args.collection}") # Changed from args.name
        try:
            # collection_info expects the qdrant_client itself
            collection_info(client.client, args)
        except DocumentStoreError as e:
             logging.error(f"Error getting collection info: {e}")
             sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error during info: {e}", exc_info=args.debug)
            sys.exit(1)
            
    def handle_count(self, client: QdrantDocumentStore, args: argparse.Namespace) -> None:
        logging.info(f"Handling count for collection: {args.collection}")
        try:
            command = QdrantCommand(client.client)
            count_documents(command, args)
        except DocumentStoreError as e:
             logging.error(f"Error counting documents: {e}")
             sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error during count: {e}", exc_info=args.debug)
            sys.exit(1)

    def handle_add(self, client: QdrantDocumentStore, args: argparse.Namespace) -> None:
        """Dispatch add document logic. Maps to 'add-documents' command."""
        logging.info(f"Handling add-documents for collection: {args.collection}")
        try:
            command = QdrantCommand(client.client)
            # The add_documents function expects the command and original args
            # It handles file opening/JSON parsing internally
            add_documents(command, args)
            # Removed the manual file reading and temp_ns creation
            
        except DocumentStoreError as e:
             logging.error(f"Error adding documents: {e}")
             sys.exit(1)
        except Exception as e:
            # Catch potential file handling errors from within add_documents
            logging.error(f"Unexpected error during add-documents: {e}", exc_info=args.debug)
            sys.exit(1)

    def handle_delete_docs(self, client: QdrantDocumentStore, args: argparse.Namespace) -> None:
        """Dispatch delete documents logic. Maps to 'delete-documents' command."""
        logging.info(f"Handling delete-documents for collection: {args.collection}")
        try:
            # Instantiate the command object, passing the raw client
            command = QdrantCommand(client.client)
            # Call the command function directly, passing the command object and args
            delete_documents(command, args)
            
            # Removed the redundant parsing logic previously here

        # Keep error handling
        except json.JSONDecodeError as e:
             logging.error(f"Invalid JSON in --filter: {e}") # Should be caught inside delete_documents now
             sys.exit(1)
        except DocumentStoreError as e:
             logging.error(f"Error deleting documents: {e}")
             sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error during delete-documents: {e}", exc_info=args.debug)
            sys.exit(1)

    def handle_scroll(self, client: QdrantDocumentStore, args: argparse.Namespace) -> None:
        """Handle the scroll command."""
        logging.info(f"Handling scroll for collection: {args.collection}")
        try:
            # Instantiate the command object
            command = QdrantCommand(client.client)
            # Call the command function directly
            scroll_documents(command, args)
            
            # Removed JSON parsing and direct call logic

        # Keep error handling (though JSON errors should be caught within scroll_documents now)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in --query: {e}")
            sys.exit(1)
        except DocumentStoreError as e:
             logging.error(f"Error scrolling documents: {e}")
             sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error during scroll: {e}", exc_info=args.debug)
            sys.exit(1)

    def handle_get(self, client: QdrantDocumentStore, args: argparse.Namespace) -> None:
        """Dispatch get documents by ID logic. Maps to 'get' command."""
        logging.info(f"Handling get documents for collection: {args.collection}")
        try:
            # Instantiate the command object
            command = QdrantCommand(client.client)
            # Call the command function directly
            get_documents(command, args)
            
            # Removed ID parsing logic

        # Keep error handling
        except DocumentStoreError as e:
             logging.error(f"Error getting documents: {e}")
             sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error during get: {e}", exc_info=args.debug)
            sys.exit(1)


    # Required methods not yet mapped to specific commands
    def handle_search(self, client: Any, args: argparse.Namespace) -> None:
        """Handle the search command."""
        logging.info(f"Handling search for collection: {args.collection}")
        try:
            # Instantiate the command object
            command = QdrantCommand(client.client)
            # Call the command function directly
            search_documents(command, args)

            # Removed JSON parsing logic

        # Keep error handling (though JSON errors should be caught within search_documents now)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in --query: {e}")
            sys.exit(1)
        except DocumentStoreError as e:
             logging.error(f"Error searching documents: {e}")
             sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error during search: {e}", exc_info=args.debug)
            sys.exit(1)

    # --- Run method ---
    def run(self) -> None:
        """Parse arguments and execute the corresponding command handler."""
        parser = self.create_parser()
        args = parser.parse_args()

        # Setup logging level based on debug flag
        log_level = logging.DEBUG if args.debug else logging.INFO
        # Use basicConfig with force=True to override potential BaseCLI setup
        logging.basicConfig(
            level=log_level, 
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True 
        )
        
        # Suppress noisy libraries if needed
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING) # Qdrant client uses httpx
        logging.getLogger("qdrant_client").setLevel(logging.INFO if args.debug else logging.WARNING)


        try:
            client = self.initialize_client(args)
            
            # Dispatch to the correct handler based on the subparser command
            if args.command == "list":
                self.handle_list(client, args)
            elif args.command == "create":
                self.handle_create(client, args)
            elif args.command == "delete":
                self.handle_delete(client, args)
            elif args.command == "info":
                self.handle_info(client, args)
            elif args.command == "count":
                 self.handle_count(client, args)
            elif args.command == "add-documents":
                 self.handle_add(client, args) # Mapped handle_add to add-documents command
            elif args.command == "delete-documents":
                 self.handle_delete_docs(client, args)
            elif args.command == "scroll":
                 self.handle_scroll(client, args)
            elif args.command == "get":
                 self.handle_get(client, args)
            elif args.command == "search":
                 self.handle_search(client, args)
            else:
                logging.error(f"Unknown command: {args.command}")
                parser.print_help()
                sys.exit(1)

        except DocumentStoreError as e:
            # Ensure error details are logged if present
            details_str = f" Details: {e.details}" if hasattr(e, 'details') and e.details else ""
            logging.error(f"Error: {e}{details_str}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}", exc_info=args.debug)
            sys.exit(1)


# --- Main execution ---
def main():
    """Main entry point for the Qdrant CLI."""
    # Check for qdrant-client import early
    try:
        import qdrant_client
        # Check specific components if needed
        from qdrant_client.http.models import Distance, VectorParams
    except ImportError:
        # Use print directly as logging might not be configured yet
        print("Error: qdrant-client is not installed. Please run: pip install qdrant-client")
        sys.exit(1)

    # Configure root logger before instantiating CLI, in case BaseCLI setup runs
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    cli_instance = QdrantCLI()
    cli_instance.run()

if __name__ == '__main__':
    main() 