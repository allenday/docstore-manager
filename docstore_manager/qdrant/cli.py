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

from ..common.config.base import get_profiles, get_config_dir, load_config
from ..common.exceptions import (
    DocumentError,
    QueryError,
    CollectionError,
    ConfigurationError
)
from .command import QdrantCommand

def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Command-line tool for managing Qdrant vector database collections"
    )
    
    # Global options
    parser.add_argument(
        "--profile",
        help="Configuration profile to use",
        default="default"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to config file",
        default=None
    )
    parser.add_argument(
        "--output",
        help="Output file path (default: stdout)",
        default=None
    )
    parser.add_argument(
        "--format",
        choices=["json", "yaml"],
        default="json",
        help="Output format (default: json)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # List collections
    list_parser = subparsers.add_parser(
        "list",
        help="List all collections"
    )
    
    # Create collection
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new collection"
    )
    create_parser.add_argument(
        "name",
        help="Collection name"
    )
    create_parser.add_argument(
        "--dimension",
        type=int,
        required=True,
        help="Vector dimension"
    )
    create_parser.add_argument(
        "--distance",
        choices=["Cosine", "Euclid", "Dot"],
        default="Cosine",
        help="Distance function (default: Cosine)"
    )
    create_parser.add_argument(
        "--on-disk",
        action="store_true",
        help="Store payload on disk"
    )
    
    # Delete collection
    delete_parser = subparsers.add_parser(
        "delete",
        help="Delete a collection"
    )
    delete_parser.add_argument(
        "name",
        help="Collection name"
    )
    
    # Get collection info
    info_parser = subparsers.add_parser(
        "info",
        help="Get collection information"
    )
    info_parser.add_argument(
        "name",
        help="Collection name"
    )
    
    # Add documents
    add_parser = subparsers.add_parser(
        "add",
        help="Add documents to collection"
    )
    add_parser.add_argument(
        "collection",
        help="Collection name"
    )
    add_parser.add_argument(
        "--file",
        type=Path,
        help="JSON file containing documents"
    )
    add_parser.add_argument(
        "--docs",
        help="JSON string containing documents"
    )
    add_parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for document upload (default: 100)"
    )
    
    # Delete documents
    delete_docs_parser = subparsers.add_parser(
        "delete-docs",
        help="Delete documents from collection"
    )
    delete_docs_parser.add_argument(
        "collection",
        help="Collection name"
    )
    delete_docs_parser.add_argument(
        "--file",
        type=Path,
        help="File containing document IDs (one per line)"
    )
    delete_docs_parser.add_argument(
        "--ids",
        help="Comma-separated list of document IDs"
    )
    
    # Search documents
    search_parser = subparsers.add_parser(
        "search",
        help="Search documents in collection"
    )
    search_parser.add_argument(
        "collection",
        help="Collection name"
    )
    search_parser.add_argument(
        "--query",
        required=True,
        help="JSON query string"
    )
    search_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)"
    )
    search_parser.add_argument(
        "--with-vectors",
        action="store_true",
        help="Include vectors in results"
    )
    
    # Get documents
    get_parser = subparsers.add_parser(
        "get",
        help="Get documents by IDs"
    )
    get_parser.add_argument(
        "collection",
        help="Collection name"
    )
    get_parser.add_argument(
        "--file",
        type=Path,
        help="File containing document IDs (one per line)"
    )
    get_parser.add_argument(
        "--ids",
        help="Comma-separated list of document IDs"
    )
    get_parser.add_argument(
        "--with-vectors",
        action="store_true",
        help="Include vectors in results"
    )
    
    # Scroll documents
    scroll_parser = subparsers.add_parser(
        "scroll",
        help="Scroll through all documents in collection"
    )
    scroll_parser.add_argument(
        "collection",
        help="Collection name"
    )
    scroll_parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size (default: 100)"
    )
    scroll_parser.add_argument(
        "--with-vectors",
        action="store_true",
        help="Include vectors in results"
    )
    
    # Count documents
    count_parser = subparsers.add_parser(
        "count",
        help="Count documents in collection"
    )
    count_parser.add_argument(
        "collection",
        help="Collection name"
    )
    count_parser.add_argument(
        "--query",
        help="JSON query string"
    )
    
    return parser

def main() -> None:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        # Load configuration
        config = load_config(args.profile, args.config)
        command = QdrantCommand()
        
        # Execute command
        if args.command == "list":
            result = command.list_collections()
            command._write_output(result, args.output, args.format)
            
        elif args.command == "create":
            command.create_collection(
                args.name,
                args.dimension,
                args.distance,
                args.on_disk
            )
            
        elif args.command == "delete":
            command.delete_collection(args.name)
            
        elif args.command == "info":
            result = command.get_collection(args.name)
            command._write_output(result, args.output, args.format)
            
        elif args.command == "add":
            if args.file and args.docs:
                raise ValueError("Specify either --file or --docs, not both")
            
            if not (args.file or args.docs):
                raise ValueError("Either --file or --docs must be specified")
            
            documents = command._load_documents(
                args.collection,
                docs_file=args.file,
                docs_str=args.docs
            )
            command.add_documents(args.collection, documents, args.batch_size)
            
        elif args.command == "delete-docs":
            if args.file and args.ids:
                raise ValueError("Specify either --file or --ids, not both")
            
            if not (args.file or args.ids):
                raise ValueError("Either --file or --ids must be specified")
            
            ids = command._load_ids(
                args.collection,
                ids_file=args.file,
                ids_str=args.ids
            )
            command.delete_documents(args.collection, ids)
            
        elif args.command == "search":
            query = command._parse_query(args.collection, args.query)
            result = command.search_documents(
                args.collection,
                query,
                args.limit,
                args.with_vectors
            )
            command._write_output(result, args.output, args.format)
            
        elif args.command == "get":
            if args.file and args.ids:
                raise ValueError("Specify either --file or --ids, not both")
            
            if not (args.file or args.ids):
                raise ValueError("Either --file or --ids must be specified")
            
            ids = command._load_ids(
                args.collection,
                ids_file=args.file,
                ids_str=args.ids
            )
            result = command.get_documents(
                args.collection,
                ids,
                args.with_vectors
            )
            command._write_output(result, args.output, args.format)
            
        elif args.command == "scroll":
            result = command.scroll_documents(
                args.collection,
                args.batch_size,
                args.with_vectors
            )
            command._write_output(result, args.output, args.format)
            
        elif args.command == "count":
            query = command._parse_query(args.collection, args.query) if args.query else None
            result = command.count_documents(args.collection, query)
            command._write_output({"count": result}, args.output, args.format)
            
    except (DocumentError, QueryError, CollectionError, ConfigurationError) as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 