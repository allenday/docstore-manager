"""Main entry point for the Document Store Manager CLI."""

import argparse
import logging
import sys

# from .core import ( # Relative
from docstore_manager.core import (
    setup_logging,
    get_config_dir,
    get_profiles,
    ConfigurationError,
    ConnectionError,
    CollectionError,
    DocumentError,
)
# from .qdrant.cli import qdrant_cli # Relative
from docstore_manager.qdrant.cli import qdrant_cli # Absolute
# from .solr.cli import solr_cli # Relative
from docstore_manager.solr.cli import solr_cli # Absolute

# Import the argparse-based CLI classes
from docstore_manager.qdrant.cli import QdrantCLI
from docstore_manager.solr.cli import SolrCLI

def main():
    # Basic logging setup before parsing args (can be refined by subcommands)
    setup_logging()
    logger = logging.getLogger("docstore-manager")

    # --- Top-level Argparse Setup ---
    parser = argparse.ArgumentParser(
        description="Manage Qdrant and Solr document stores.",
        usage="docstore-manager <command> [<args>]"
    )
    # Add subparsers for qdrant and solr
    subparsers = parser.add_subparsers(
        title="Available Commands",
        dest="store_type",
        help="Specify the document store type (qdrant or solr)",
        metavar="<command>"
    )

    # --- Qdrant Subparser Placeholder ---
    # We don't need to define all qdrant args here.
    # We just need a way to capture 'qdrant' and the rest of the args.
    qdrant_parser = subparsers.add_parser(
        "qdrant",
        help="Manage Qdrant instances. Use 'qdrant --help' for specific commands.",
        add_help=False # Disable argparse help for this subparser
    )
    # Add a catch-all for remaining arguments to pass to QdrantCLI
    qdrant_parser.add_argument('qdrant_args', nargs=argparse.REMAINDER)

    # --- Solr Subparser Placeholder ---
    solr_parser = subparsers.add_parser(
        "solr",
        help="Manage Solr instances. Use 'solr --help' for specific commands.",
        add_help=False # Disable argparse help for this subparser
    )
    # Add a catch-all for remaining arguments to pass to SolrCLI
    solr_parser.add_argument('solr_args', nargs=argparse.REMAINDER)

    # --- Argument Parsing and Dispatching ---
    # Parse only the first few arguments to determine store_type
    # Use parse_known_args to separate main args from subcommand args
    args, remaining_args = parser.parse_known_args()

    if args.store_type == "qdrant":
        logger.debug(f"Dispatching to QdrantCLI with args: {remaining_args}")
        qdrant_cli_instance = QdrantCLI()
        # QdrantCLI().run() expects a list of args (like sys.argv[2:])
        qdrant_cli_instance.run(remaining_args)
    elif args.store_type == "solr":
        logger.debug(f"Dispatching to SolrCLI with args: {remaining_args}")
        solr_cli_instance = SolrCLI()
        # SolrCLI().run() expects a list of args
        solr_cli_instance.run(remaining_args)
    else:
        # If no command was provided (or an invalid one)
        parser.print_help()
        sys.exit(1)

# This check ensures main() runs only when script is executed directly
# The actual entry point is configured in pyproject.toml to call this main()
if __name__ == '__main__':
    main()

# ... existing code ... 