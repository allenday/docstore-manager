"""
Click command definitions for Qdrant operations.

This module defines Click commands for interacting with Qdrant vector database.
These commands are intended to be attached to a group defined in the main cli.py.
The module provides a comprehensive set of commands for managing Qdrant collections
and documents, including creating, listing, and deleting collections, as well as
adding, retrieving, searching, and removing documents.

Each command function is designed to be used as a Click command and handles
parameter validation, error handling, and proper output formatting. The commands
rely on the underlying command implementation functions from the commands package.
"""

import click
import logging
import sys
import json
from typing import Any, Optional, List, Dict, Union
from pathlib import Path
from urllib.parse import urlparse

# Core components
from docstore_manager.core.config.base import load_config
from docstore_manager.core.exceptions import (
    ConfigurationError,
    DocumentStoreError,
    CollectionError,
    CollectionDoesNotExistError,
    DocumentError,
    InvalidInputError
)
# Qdrant specific components
from docstore_manager.qdrant.client import QdrantClient
from docstore_manager.qdrant.format import QdrantFormatter
# Import the underlying command functions
from docstore_manager.qdrant.commands.list import list_collections as cmd_list_collections
from docstore_manager.qdrant.commands.create import create_collection as cmd_create_collection
from docstore_manager.qdrant.commands.delete import delete_collection as cmd_delete_collection
from docstore_manager.qdrant.commands.info import collection_info as cmd_collection_info
from docstore_manager.qdrant.commands.count import count_documents as cmd_count_documents
from docstore_manager.qdrant.commands.batch import add_documents as cmd_add_documents
from docstore_manager.qdrant.commands.batch import remove_documents as cmd_remove_documents
from docstore_manager.qdrant.commands.scroll import scroll_documents as cmd_scroll_documents
from docstore_manager.qdrant.commands.get import get_documents as cmd_get_documents
from docstore_manager.qdrant.commands.search import search_documents as cmd_search_documents
# Import the helper functions needed by the CLI layer now
from docstore_manager.qdrant.commands.batch import _load_documents_from_file, _load_ids_from_file

logger = logging.getLogger(__name__) # Logger for this module

# --- Helper Functions ---

def handle_missing_config(client: Optional[Any], collection_name: Optional[str], command_name: str):
    """
    Handle missing client or collection name and exit with an error.
    
    This function checks if the client or collection name is missing and
    provides appropriate error messages before exiting the program.
    
    Args:
        client (Optional[Any]): The Qdrant client instance, or None if not initialized.
        collection_name (Optional[str]): The name of the collection, or None if not specified.
        command_name (str): The name of the command being executed, for error message context.
        
    Returns:
        None: This function does not return as it calls sys.exit(1).
        
    Raises:
        SystemExit: Always raised with exit code 1 after logging the error.
    """
    if not client:
        logger.error(f"{command_name.capitalize()} command failed: Qdrant client not initialized.")
        click.echo("ERROR: Qdrant client not available. Check configuration and profile.", err=True)
    elif not collection_name:
        logger.error(f"{command_name.capitalize()} command failed: Collection name not specified via option or config profile.")
        click.echo("ERROR: Collection name missing. Use --collection-name or set in profile.", err=True)
    else:
        # Should not happen if called correctly, but good to log
        logger.error(f"handle_missing_config called unexpectedly for {command_name}.")
        click.echo("Internal Error: Configuration check failed.", err=True)
    sys.exit(1)

def initialize_client(ctx: click.Context, profile: str, config_path: Optional[Path]) -> QdrantClient:
    """
    Initialize and return the Qdrant client based on context and args.
    
    This function loads configuration from the specified profile and config path,
    initializes a QdrantClient with the appropriate connection parameters, and
    stores the client in ctx.obj['client'] for use by command functions.
    
    Args:
        ctx (click.Context): The Click context object, which must have an 'obj' dict.
        profile (str): The configuration profile name to use.
        config_path (Optional[Path]): Path to the configuration file, or None to use default.
        
    Returns:
        QdrantClient: The initialized Qdrant client.
        
    Raises:
        ConfigurationError: If there are issues with the configuration.
        SystemExit: If client initialization fails, exits with code 1.
        
    Examples:
        >>> client = initialize_client(ctx, "default", Path("config.yaml"))
        >>> # Client is now initialized and stored in ctx.obj['client']
    """
    # Check if client is already initialized in the context
    if 'client' in ctx.obj and isinstance(ctx.obj['client'], QdrantClient):
        return ctx.obj['client']

    try:
        config_data = load_config(profile=profile, config_path=config_path)
        qdrant_profile_config = config_data.get('qdrant', {})
        qdrant_connection_config = qdrant_profile_config.get('connection', {})

        # --- DEBUG LOGGING --- 
        logger.debug(f"Loaded config_data for profile '{profile}': {config_data}")
        logger.debug(f"Extracted qdrant_profile_config: {qdrant_profile_config}")
        logger.debug(f"Extracted qdrant_connection_config: {qdrant_connection_config}")
        # --- END DEBUG LOGGING ---

        client_init_args = {}
        url = qdrant_connection_config.get('url')
        api_key = qdrant_connection_config.get('api_key')
        
        # Primary connection method: URL
        if url:
            client_init_args['url'] = url
            logger.debug(f"Connecting via URL: {url}")
        # Optional: Could add back host/port or cloud_url logic here if needed as fallbacks
        # elif host and port: ...
        # elif cloud_url and api_key: ...
        else:
             raise ConfigurationError(
                 "Qdrant connection URL not found in profile.",
                 details=f"Profile: '{profile}', Config File: {config_path}, Keys found: {list(qdrant_connection_config.keys())}"
             )

        # API key is always optional
        if api_key:
             client_init_args['api_key'] = api_key

        # Other optional args directly from connection config
        if qdrant_connection_config.get('prefer_grpc') is not None:
            client_init_args['prefer_grpc'] = qdrant_connection_config.get('prefer_grpc')
        if qdrant_connection_config.get('https') is not None: # Note: QdrantClient infers https from URL scheme
             client_init_args['https'] = qdrant_connection_config.get('https')
             # logger.warning("'https' config key for Qdrant is often inferred from URL scheme.")
        if qdrant_connection_config.get('timeout'):
            client_init_args['timeout'] = qdrant_connection_config.get('timeout')

        logger.debug(f"QdrantClient final init args: {client_init_args}")
        client = QdrantClient(**client_init_args)
        
        # Store client in context
        if not isinstance(ctx.obj, dict):
             ctx.obj = {}
        ctx.obj['client'] = client 
        logger.info(f"Initialized QdrantClient for profile '{profile}'.")
        return client

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        click.echo(f"ERROR: Configuration error - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        is_debug = isinstance(ctx.obj, dict) and ctx.obj.get('DEBUG', False)
        logger.error(f"Failed to initialize Qdrant client: {e}", exc_info=is_debug)
        click.echo(f"ERROR: Failed to initialize Qdrant client - {e}", err=True)
        sys.exit(1)

# --- Click Command Definitions (Standalone) ---

@click.command("list") 
@click.option("--output", "output_path", type=click.Path(dir_okay=False, writable=True), help="Optional path to output the list as JSON.")
@click.pass_context
def list_collections_cli(ctx: click.Context, output_path: Optional[str]):
    """
    List all collections in the Qdrant instance.
    
    This command retrieves and displays a list of all collections available in the
    connected Qdrant instance. The output can optionally be saved to a file.
    
    Relies on the client being initialized and stored in ctx.obj['client'] 
    by the parent group.
    
    Args:
        ctx (click.Context): The Click context object containing the initialized client.
        output_path (Optional[str]): If provided, the path where the output will be saved.
        
    Raises:
        SystemExit: If the client is not initialized or if an error occurs during execution.
        
    Examples:
        $ docstore-manager qdrant list
        $ docstore-manager qdrant list --output collections.json
    """
    if 'client' not in ctx.obj or not isinstance(ctx.obj['client'], QdrantClient):
         # This should ideally be caught by the group ensuring client init
         logger.error("Qdrant client not initialized in context.")
         click.echo("ERROR: Client not initialized. Check group setup.", err=True)
         sys.exit(1)
         
    client: QdrantClient = ctx.obj['client']
    # Call the underlying command function (which now takes client)
    try:
        cmd_list_collections(client=client, output_path=output_path, output_format='json')
    except CollectionError as e:
        logger.error(f"Collection error: {e}")
        click.echo(f"Collection error: {str(e)}", err=True)
        sys.exit(1)

@click.command("create")
@click.option('--overwrite', is_flag=True, default=False, help='Overwrite if collection exists.')
@click.pass_context
def create_collection_cli(ctx: click.Context, overwrite: bool):
    """
    Create a new collection as defined in the config profile.
    
    This command creates a new Qdrant collection using the parameters specified in
    the configuration profile. The collection name, vector dimension, distance metric,
    and other settings are all read from the profile configuration.
    
    Args:
        ctx (click.Context): The Click context object containing the initialized client.
        overwrite (bool): If True, overwrite the collection if it already exists.
            Defaults to False.
        
    Raises:
        ConfigurationError: If required configuration parameters are missing.
        SystemExit: If an error occurs during collection creation.
        
    Examples:
        $ docstore-manager qdrant create
        $ docstore-manager qdrant create --overwrite
    """
    client: QdrantClient = ctx.obj['client']
    profile: str = ctx.obj['PROFILE'] 
    config_path: Optional[Path] = ctx.obj.get('CONFIG_PATH') 

    try:
        # Load the full config for the profile
        config_data = load_config(profile=profile, config_path=config_path)
        qdrant_config = config_data.get('qdrant')
        if not qdrant_config:
            raise ConfigurationError(f"'qdrant' section missing in profile '{profile}'.")
            
        # --- Get Collection Name from Config ---
        connection_config = qdrant_config.get('connection')
        if not connection_config:
            raise ConfigurationError(f"'qdrant.connection' section missing in profile '{profile}'.")
        collection_name = connection_config.get('collection')
        if not collection_name:
            raise ConfigurationError(f"'qdrant.connection.collection' name is required but missing in profile '{profile}'.")
        logger.info(f"Operating on collection '{collection_name}' defined in profile '{profile}'.")
        # --------------------------------------
            
        vector_config = qdrant_config.get('vectors')
        if not vector_config:
             raise ConfigurationError(f"'qdrant.vectors' section missing in profile '{profile}'.")

        # --- Extract Payload Indices from Config --- 
        payload_indices_config = qdrant_config.get('payload_indices', []) # Get list or empty list
        if not isinstance(payload_indices_config, list):
            logger.warning(f"'qdrant.payload_indices' in profile '{profile}' should be a list, but found {type(payload_indices_config)}. Ignoring.")
            payload_indices_config = []
        # Optional: Add validation for each index dict structure if needed
        # -------------------------------------------

        # Extract parameters strictly from config
        dimension = vector_config.get('size')
        distance = vector_config.get('distance', 'Cosine') 
        on_disk = vector_config.get('on_disk', False) 
        
        hnsw_config_data = vector_config.get('hnsw_config', {}) 
        hnsw_ef = hnsw_config_data.get('ef_construct')
        hnsw_m = hnsw_config_data.get('m')
        
        cluster_config = qdrant_config.get('cluster', {}) 
        shards = cluster_config.get('shards') 
        replication_factor = cluster_config.get('replication_factor')

        # --- Validation --- 
        if dimension is None:
            raise ConfigurationError(f"'qdrant.vectors.size' (dimension) is required but missing in profile '{profile}'.")
        if not isinstance(dimension, int):
             raise ConfigurationError(f"'qdrant.vectors.size' must be an integer in profile '{profile}'.")

        # --- Log extracted values --- 
        logger.debug(f"Using config profile '{profile}' for creation:")
        logger.debug(f"  Collection Name: {collection_name}") # Log collection name
        logger.debug(f"  Dimension: {dimension}")
        logger.debug(f"  Distance: {distance}")
        logger.debug(f"  On Disk: {on_disk}")
        logger.debug(f"  HNSW EF: {hnsw_ef}")
        logger.debug(f"  HNSW M: {hnsw_m}")
        logger.debug(f"  Shards: {shards}")
        logger.debug(f"  Replication Factor: {replication_factor}")
        logger.debug(f"  Overwrite: {overwrite}")

        # Call the underlying command function with config-sourced values
        cmd_create_collection(
            client=client, 
            collection_name=collection_name, # Use name from config
            dimension=dimension, 
            distance=distance, 
            on_disk=on_disk, 
            hnsw_ef=hnsw_ef, 
            hnsw_m=hnsw_m, 
            shards=shards, 
            replication_factor=replication_factor, 
            overwrite=overwrite,
            payload_indices=payload_indices_config # Pass extracted indices
        )

    except ConfigurationError as e:
        logger.error(f"Configuration error for profile '{profile}': {e}")
        click.echo(f"ERROR: Configuration error - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error processing configuration for create command: {e}", exc_info=True)
        click.echo(f"ERROR: Failed processing configuration - {e}", err=True)
        sys.exit(1)

@click.command("delete")
@click.option('--yes', '-y', is_flag=True, default=False, help='Skip confirmation prompt.')
@click.pass_context
def delete_collection_cli(ctx: click.Context, yes: bool):
    """
    Delete the collection defined in the config profile.
    
    This command deletes the Qdrant collection specified in the configuration profile.
    By default, it will prompt for confirmation before deletion unless the --yes flag
    is provided.
    
    Args:
        ctx (click.Context): The Click context object containing the initialized client.
        yes (bool): If True, skip the confirmation prompt. Defaults to False.
        
    Raises:
        ConfigurationError: If the collection name is missing from the configuration.
        SystemExit: If an error occurs during collection deletion.
        
    Examples:
        $ docstore-manager qdrant delete
        $ docstore-manager qdrant delete --yes
    """
    client = ctx.obj['client']
    profile: str = ctx.obj['PROFILE'] 
    config_path: Optional[Path] = ctx.obj.get('CONFIG_PATH')

    try:
        # Load the full config for the profile to get the collection name
        config_data = load_config(profile=profile, config_path=config_path)
        qdrant_config = config_data.get('qdrant')
        if not qdrant_config:
            raise ConfigurationError(f"'qdrant' section missing in profile '{profile}'.")
        connection_config = qdrant_config.get('connection')
        if not connection_config:
            raise ConfigurationError(f"'qdrant.connection' section missing in profile '{profile}'.")
        collection_name = connection_config.get('collection')
        if not collection_name:
            raise ConfigurationError(f"'qdrant.connection.collection' name is required but missing in profile '{profile}'.")
            
        logger.info(f"Targeting collection '{collection_name}' from profile '{profile}' for deletion.")

        # Confirmation prompt
        if not yes:
            if not click.confirm(f"Are you sure you want to delete the collection '{collection_name}' defined in profile '{profile}'?"):
                click.echo("Aborted")
                return

        # Call the refactored command function
        cmd_delete_collection(client, collection_name) 

    except ConfigurationError as e:
        logger.error(f"Configuration error for profile '{profile}': {e}")
        click.echo(f"ERROR: Configuration error - {e}", err=True)
        sys.exit(1)
    except Exception as e: # Catch other potential errors 
         logger.error(f"Error during delete command processing: {e}", exc_info=True)
         click.echo(f"ERROR: Failed during delete - {e}", err=True)
         sys.exit(1)

@click.command("info")
@click.pass_context
def collection_info_cli(ctx: click.Context):
    """
    Get detailed information about the collection defined in the config profile.
    
    This command retrieves and displays detailed information about the Qdrant collection
    specified in the configuration profile, including its status, vector configuration,
    and other settings.
    
    Args:
        ctx (click.Context): The Click context object containing the initialized client.
        
    Raises:
        ConfigurationError: If the collection name is missing from the configuration.
        CollectionDoesNotExistError: If the specified collection does not exist.
        SystemExit: If an error occurs during information retrieval.
        
    Examples:
        $ docstore-manager qdrant info
    """
    client: QdrantClient = ctx.obj['client']
    profile: str = ctx.obj['PROFILE']
    config_path: Optional[Path] = ctx.obj.get('CONFIG_PATH')

    try:
        # Load config to get collection name
        config_data = load_config(profile=profile, config_path=config_path)
        qdrant_config = config_data.get('qdrant', {})
        connection_config = qdrant_config.get('connection', {})
        collection_name = connection_config.get('collection')
        if not collection_name:
            raise ConfigurationError(f"'qdrant.connection.collection' name missing in profile '{profile}'.")
        logger.info(f"Getting info for collection '{collection_name}' defined in profile '{profile}'.")

        # Call the refactored command function
        cmd_collection_info(client, collection_name)

    except ConfigurationError as e:
        logger.error(f"Configuration error for profile '{profile}': {e}")
        click.echo(f"ERROR: Configuration error - {e}", err=True)
        sys.exit(1)
    except Exception as e: # Catch other potential errors
        logger.error(f"Error during info command processing: {e}", exc_info=True)
        click.echo(f"ERROR: Failed during info command - {e}", err=True)
        sys.exit(1)

@click.command("count")
@click.option('--filter-json', 'query_filter_json', help='JSON filter string (Qdrant Filter object).')
@click.pass_context
def count_documents_cli(ctx: click.Context, query_filter_json: Optional[str]):
    """
    Count documents in the collection defined in the profile.
    
    This command counts the number of documents in the Qdrant collection specified
    in the configuration profile. An optional filter can be applied to count only
    documents matching specific criteria.
    
    Args:
        ctx (click.Context): The Click context object containing the initialized client.
        query_filter_json (Optional[str]): Optional JSON string representing a Qdrant
            filter to apply when counting documents.
        
    Raises:
        ConfigurationError: If the collection name is missing from the configuration.
        CollectionDoesNotExistError: If the specified collection does not exist.
        InvalidInputError: If the provided filter JSON is invalid.
        SystemExit: If an error occurs during the count operation.
        
    Examples:
        $ docstore-manager qdrant count
        $ docstore-manager qdrant count --filter-json '{"must": [{"key": "category", "match": {"value": "electronics"}}]}'
    """
    client: QdrantClient = ctx.obj['client']
    profile: str = ctx.obj['PROFILE']
    config_path: Optional[Path] = ctx.obj.get('CONFIG_PATH')

    try:
        # Load config to get collection name
        config_data = load_config(profile=profile, config_path=config_path)
        qdrant_config = config_data.get('qdrant', {})
        connection_config = qdrant_config.get('connection', {})
        collection_name = connection_config.get('collection')
        if not collection_name:
            raise ConfigurationError(f"'qdrant.connection.collection' name missing in profile '{profile}'.")
        logger.info(f"Counting documents for collection '{collection_name}' defined in profile '{profile}'.")

        # Call the refactored command function
        cmd_count_documents(
            client=client, 
            collection_name=collection_name, 
            query_filter_json=query_filter_json
        )

    except ConfigurationError as e:
        logger.error(f"Configuration error for profile '{profile}': {e}")
        click.echo(f"ERROR: Configuration error - {e}", err=True)
        sys.exit(1)
    except Exception as e: # Catch other potential errors
        logger.error(f"Error during count command processing: {e}", exc_info=True)
        click.echo(f"ERROR: Failed during count command - {e}", err=True)
        sys.exit(1)

@click.command("add-documents")
@click.option('--file', type=click.Path(exists=True, dir_okay=False), help='Path to JSON Lines file (.jsonl) containing documents.')
@click.option('--docs', 'docs_json', help='JSON string containing documents (list of dicts).')
@click.option('--batch-size', type=int, default=100, show_default=True, help='Documents per batch (used conceptually).')
@click.pass_context
def add_documents_cli(ctx: click.Context, file: Optional[str], docs_json: Optional[str], batch_size: int):
    """
    Add documents to the collection defined in the profile.
    
    This command adds documents to the Qdrant collection specified in the configuration
    profile. Documents can be provided either as a JSON Lines file or as a JSON string
    directly in the command line.
    
    Args:
        ctx (click.Context): The Click context object containing the initialized client.
        file (Optional[str]): Path to a JSON Lines file (.jsonl) containing documents.
        docs_json (Optional[str]): JSON string containing documents as a list of dictionaries.
        batch_size (int): Number of documents to process in each batch. Defaults to 100.
        
    Raises:
        ConfigurationError: If the collection name is missing from the configuration.
        click.UsageError: If neither --file nor --docs is specified, or if both are specified.
        InvalidInputError: If the provided documents are invalid.
        SystemExit: If an error occurs during document addition.
        
    Examples:
        $ docstore-manager qdrant add-documents --file documents.jsonl
        $ docstore-manager qdrant add-documents --docs '[{"id": "doc1", "vector": [0.1, 0.2], "payload": {"text": "example"}}]'
    """
    client: QdrantClient = ctx.obj['client']
    profile: str = ctx.obj['PROFILE']
    config_path: Optional[Path] = ctx.obj.get('CONFIG_PATH')

    try:
        # Load config to get collection name
        config_data = load_config(profile=profile, config_path=config_path)
        qdrant_config = config_data.get('qdrant', {})
        connection_config = qdrant_config.get('connection', {})
        collection_name = connection_config.get('collection')
        if not collection_name:
            raise ConfigurationError(f"'qdrant.connection.collection' name missing in profile '{profile}'.")
        logger.info(f"Operating on collection '{collection_name}' defined in profile '{profile}'.")

        # Validate and load documents from CLI options
        if file and docs_json:
            raise click.UsageError("Specify either --file or --docs, not both.")

        documents: List[Dict[str, Any]] = []
        if file:
            try:
                documents = _load_documents_from_file(file)
            except (FileOperationError, FileParseError) as e:
                details_str = f" Details: {e.details}" if hasattr(e, 'details') and e.details else ""
                raise click.UsageError(f"Error loading documents from --file: {e}{details_str}")
        elif docs_json:
            try:
                documents = json.loads(docs_json)
                if not isinstance(documents, list):
                    raise ValueError("Documents must be a JSON array (list).")
                if not all(isinstance(doc, dict) for doc in documents):
                     raise ValueError("JSON array must contain only objects (dictionaries).")
            except (json.JSONDecodeError, ValueError) as e:
                raise click.UsageError(f"Invalid JSON in --docs string: {e}")
        else:
            raise click.UsageError("Either --file or --docs must be specified.")

        # Call the refactored command function
        cmd_add_documents(
            client=client,
            collection_name=collection_name,
            documents=documents,
            batch_size=batch_size
        )

    except ConfigurationError as e:
        logger.error(f"Configuration error for profile '{profile}': {e}")
        click.echo(f"ERROR: Configuration error - {e}", err=True)
        sys.exit(1)
    except click.UsageError as e:
        click.echo(f"Usage Error: {e}", err=True)
        sys.exit(1)
    except Exception as e: # Catch other potential errors
        logger.error(f"Error during add-documents command: {e}", exc_info=True)
        click.echo(f"ERROR: Failed during add-documents - {e}", err=True)
        sys.exit(1)

@click.command("remove-documents")
@click.option('--file', 'id_file', type=click.Path(exists=True, dir_okay=False), help='Path to file containing document IDs (one per line).')
@click.option('--ids', help='Comma-separated list of document IDs.')
@click.option('--filter-json', help='JSON filter string (Qdrant Filter object).')
@click.option('--batch-size', type=int, default=100, show_default=True, help='Conceptual batch size.')
@click.option('--yes', '-y', is_flag=True, default=False, help='Skip confirmation for filter deletion.')
@click.pass_context
def remove_documents_cli(ctx: click.Context, id_file: Optional[str], ids: Optional[str], filter_json: Optional[str], batch_size: int, yes: bool):
    """
    Remove documents from the collection defined in the profile.
    
    This command removes documents from the Qdrant collection specified in the
    configuration profile. Documents can be removed by providing their IDs (either
    as a comma-separated list or from a file) or by specifying a filter to match
    documents for removal.
    
    Args:
        ctx (click.Context): The Click context object containing the initialized client.
        id_file (Optional[str]): Path to a file containing document IDs, one per line.
        ids (Optional[str]): Comma-separated list of document IDs to remove.
        filter_json (Optional[str]): JSON string representing a Qdrant filter to match
            documents for removal.
        batch_size (int): Number of documents to process in each batch. Defaults to 100.
        yes (bool): If True, skip the confirmation prompt for filter-based deletion.
            Defaults to False.
        
    Raises:
        ConfigurationError: If the collection name is missing from the configuration.
        click.UsageError: If none or multiple of --file, --ids, or --filter-json are specified.
        InvalidInputError: If the provided IDs or filter are invalid.
        SystemExit: If an error occurs during document removal.
        
    Examples:
        $ docstore-manager qdrant remove-documents --ids doc1,doc2,doc3
        $ docstore-manager qdrant remove-documents --file document_ids.txt
        $ docstore-manager qdrant remove-documents --filter-json '{"must": [{"key": "category", "match": {"value": "electronics"}}]}' --yes
    """
    client: QdrantClient = ctx.obj['client']
    profile: str = ctx.obj['PROFILE']
    config_path: Optional[Path] = ctx.obj.get('CONFIG_PATH')

    try:
        # Load config to get collection name
        config_data = load_config(profile=profile, config_path=config_path)
        qdrant_config = config_data.get('qdrant', {})
        connection_config = qdrant_config.get('connection', {})
        collection_name = connection_config.get('collection')
        if not collection_name:
            raise ConfigurationError(f"'qdrant.connection.collection' name missing in profile '{profile}'.")
        logger.info(f"Operating on collection '{collection_name}' defined in profile '{profile}'.")

        # Validate input options
        provided_options = [opt for opt in [id_file, ids, filter_json] if opt]
        if len(provided_options) == 0:
            raise click.UsageError("Either --file, --ids, or --filter-json must be specified.")
        if len(provided_options) > 1:
            raise click.UsageError("Specify only one of --file, --ids, or --filter-json.")

        # Prepare arguments for the underlying command
        doc_ids_to_remove: Optional[List[str]] = None
        doc_filter_to_remove: Optional[Dict] = None

        if id_file:
            try:
                doc_ids_to_remove = _load_ids_from_file(id_file)
            except FileOperationError as e:
                raise click.UsageError(f"Error loading IDs from --file: {e}")
        elif ids:
            doc_ids_to_remove = [id_str.strip() for id_str in ids.split(',') if id_str.strip()]
            if not doc_ids_to_remove:
                raise click.UsageError("No valid document IDs found in --ids string.")
        elif filter_json:
            try:
                doc_filter_to_remove = json.loads(filter_json)
                if not isinstance(doc_filter_to_remove, dict):
                     raise ValueError("Filter must be a JSON object (dictionary).")
                # Add confirmation for filter deletion
                if not yes:
                    click.confirm(
                        f"Are you sure you want to remove documents matching filter in collection '{collection_name}'? Filter: {filter_json}",
                        abort=True
                    )
            except (json.JSONDecodeError, ValueError) as e:
                raise click.UsageError(f"Invalid JSON in --filter-json string: {e}")

        # Call the renamed refactored command function
        cmd_remove_documents(
            client=client,
            collection_name=collection_name,
            doc_ids=doc_ids_to_remove,
            doc_filter=doc_filter_to_remove,
            batch_size=batch_size
        )

    except ConfigurationError as e:
        logger.error(f"Configuration error for profile '{profile}': {e}")
        click.echo(f"ERROR: Configuration error - {e}", err=True)
        sys.exit(1)
    except click.UsageError as e:
        click.echo(f"Usage Error: {e}", err=True)
        sys.exit(1)
    except Exception as e: # Catch other potential errors
        logger.error(f"Error during remove-documents command: {e}", exc_info=True)
        click.echo(f"ERROR: Failed during remove-documents - {e}", err=True)
        sys.exit(1)

@click.command("scroll")
@click.option('--collection-name', default=None, help='Name of the collection')
@click.option('--filter-json', 'scroll_filter', default=None, help='JSON string for scroll filter')
@click.option('--limit', type=int, default=10, help='Max number of results')
@click.option('--offset', default=None, help='Scroll offset (point ID or integer)')
@click.option('--output', 'output_path', type=click.Path(), default=None, help='File path to save results')
@click.option('--format', 'output_format', type=click.Choice(['json', 'yaml', 'csv', 'table']), default='json', help='Output format')
@click.option('--with-vectors', is_flag=True, default=False, help='Include vectors in the output')
@click.option('--with-payload', is_flag=True, default=True, help='Include payload in the output')
@click.pass_context
def scroll_documents_cli(ctx, collection_name, scroll_filter, limit, offset, output_path, output_format, with_vectors, with_payload):
    """
    Scroll through documents in a collection.
    
    This command retrieves documents from the Qdrant collection in batches, allowing
    for pagination through large collections. An optional filter can be applied to
    retrieve only documents matching specific criteria.
    
    Args:
        ctx (click.Context): The Click context object containing the initialized client.
        collection_name (Optional[str]): Name of the collection. If not provided,
            uses the collection name from the configuration profile.
        scroll_filter (Optional[str]): JSON string representing a Qdrant filter to
            apply when scrolling through documents.
        limit (int): Maximum number of results to return. Defaults to 10.
        offset (Optional[str]): Scroll offset (point ID or integer) for pagination.
        output_path (Optional[str]): File path to save the results.
        output_format (str): Output format ('json', 'yaml', 'csv', or 'table').
            Defaults to 'json'.
        with_vectors (bool): If True, include vectors in the output. Defaults to False.
        with_payload (bool): If True, include payload in the output. Defaults to True.
        
    Raises:
        ConfigurationError: If the collection name is missing and not provided.
        CollectionDoesNotExistError: If the specified collection does not exist.
        InvalidInputError: If the provided filter or offset is invalid.
        SystemExit: If an error occurs during the scroll operation.
        
    Examples:
        $ docstore-manager qdrant scroll --limit 20
        $ docstore-manager qdrant scroll --filter-json '{"must": [{"key": "category", "match": {"value": "electronics"}}]}'
        $ docstore-manager qdrant scroll --offset doc1 --limit 5 --with-vectors
    """
    client = ctx.obj.get('client')
    # Load config within the command using profile and path from context
    profile: str = ctx.obj['PROFILE']
    config_path: Optional[Path] = ctx.obj.get('CONFIG_PATH')
    try:
        config_data = load_config(profile=profile, config_path=config_path)
        qdrant_config = config_data.get('qdrant', {})
        connection_config = qdrant_config.get('connection', {})
        profile_collection_name = connection_config.get('collection')
    except ConfigurationError as e:
        logger.error(f"Configuration error for profile '{profile}': {e}")
        click.echo(f"ERROR: Configuration error - {e}", err=True)
        sys.exit(1)

    effective_collection_name = collection_name or profile_collection_name

    if not client or not effective_collection_name:
        handle_missing_config(client, effective_collection_name, "scroll")
        return

    try:
        cmd_scroll_documents(
            client=client,
            collection_name=effective_collection_name,
            scroll_filter=scroll_filter,
            limit=limit,
            offset=offset,
            with_payload=with_payload,
            with_vectors=with_vectors,
        )
    except (CollectionError, DocumentError, InvalidInputError) as e:
        logger.error(f"Error during scroll command: {e}", exc_info=False)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during scroll command execution: {e}", exc_info=True)
        click.echo(f"Unexpected Error: {e}", err=True)
        sys.exit(1)

@click.command("get")
@click.option('--collection-name', default=None, help='Name of the collection')
@click.option('--ids', default=None, help='Comma-separated list of document IDs')
@click.option('--file', 'ids_file', type=click.Path(exists=True), help='File containing document IDs (one per line)')
@click.option('--output', 'output_path', type=click.Path(), default=None, help='File path to save results')
@click.option('--format', 'output_format', type=click.Choice(['json', 'yaml', 'csv', 'table']), default='json', help='Output format')
@click.option('--with-vectors', is_flag=True, default=False, help='Include vectors in the output')
@click.option('--with-payload', is_flag=True, default=True, help='Include payload in the output')
@click.pass_context
def get_documents_cli(ctx, collection_name, ids, ids_file, output_path, output_format, with_vectors, with_payload):
    """
    Retrieve documents by ID from a collection.
    
    This command retrieves specific documents from the Qdrant collection by their IDs.
    Document IDs can be provided either as a comma-separated list or from a file.
    
    Args:
        ctx (click.Context): The Click context object containing the initialized client.
        collection_name (Optional[str]): Name of the collection. If not provided,
            uses the collection name from the configuration profile.
        ids (Optional[str]): Comma-separated list of document IDs to retrieve.
        ids_file (Optional[str]): Path to a file containing document IDs, one per line.
        output_path (Optional[str]): File path to save the results.
        output_format (str): Output format ('json', 'yaml', 'csv', or 'table').
            Defaults to 'json'.
        with_vectors (bool): If True, include vectors in the output. Defaults to False.
        with_payload (bool): If True, include payload in the output. Defaults to True.
        
    Raises:
        ConfigurationError: If the collection name is missing and not provided.
        CollectionDoesNotExistError: If the specified collection does not exist.
        InvalidInputError: If no document IDs are provided or they are invalid.
        DocumentError: If an error occurs during document retrieval.
        SystemExit: If an error occurs during the get operation.
        
    Examples:
        $ docstore-manager qdrant get --ids doc1,doc2,doc3
        $ docstore-manager qdrant get --file document_ids.txt --with-vectors
        $ docstore-manager qdrant get --ids doc1 --format yaml
    """
    client = ctx.obj.get('client')
    # Load config within the command using profile and path from context
    profile: str = ctx.obj['PROFILE']
    config_path: Optional[Path] = ctx.obj.get('CONFIG_PATH')
    try:
        config_data = load_config(profile=profile, config_path=config_path)
        qdrant_config = config_data.get('qdrant', {})
        connection_config = qdrant_config.get('connection', {})
        profile_collection_name = connection_config.get('collection')
    except ConfigurationError as e:
        logger.error(f"Configuration error for profile '{profile}': {e}")
        click.echo(f"ERROR: Configuration error - {e}", err=True)
        sys.exit(1)

    # Use the explicitly passed collection_name if provided, otherwise fallback to profile's name
    effective_collection_name = collection_name or profile_collection_name

    if not client or not effective_collection_name:
        handle_missing_config(client, effective_collection_name, "get")
        return

    doc_ids = []
    if ids:
        doc_ids.extend([item.strip() for item in ids.split(',') if item.strip()])
    if ids_file:
        try:
            doc_ids.extend(_load_ids_from_file(ids_file))
        except Exception as e:
            click.echo(f"Error reading IDs file: {e}", err=True)
            sys.exit(1)
            
    if not doc_ids:
        click.echo("Error: No document IDs provided via --ids or --file.", err=True)
        sys.exit(1)

    # Convert IDs to int if possible, keep as string otherwise
    parsed_ids = []
    for doc_id in doc_ids:
        try:
            parsed_ids.append(int(doc_id))
        except ValueError:
            parsed_ids.append(doc_id) # Keep as string if not int

    try:
        cmd_get_documents(
            client=client,
            collection_name=effective_collection_name,
            doc_ids=parsed_ids,
            with_payload=with_payload,
            with_vectors=with_vectors,
        )
    except (CollectionError, DocumentError, InvalidInputError) as e:
        logger.error(f"Error during get command: {e}", exc_info=False)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during get command execution: {e}", exc_info=True)
        click.echo(f"Unexpected Error: {e}", err=True)
        sys.exit(1)

@click.command("search")
@click.option('--query-vector', help='JSON string representing the query vector (list of floats).')
@click.option('--query-filter-json', help='JSON filter string (Qdrant Filter object).')
@click.option('--limit', type=int, default=10, show_default=True, help='Number of results.')
@click.option('--with-vectors', is_flag=True, default=False, help='Include vectors in output.')
@click.option('--with-payload/--without-payload', default=True, show_default=True, help='Include payload in output.')
@click.pass_context
def search_documents_cli(ctx: click.Context, query_vector: Optional[str], query_filter_json: Optional[str],
                         limit: int, with_vectors: bool, with_payload: bool):
    """
    Search for similar documents in the collection defined in the profile.
    
    This command performs a vector similarity search in the Qdrant collection
    specified in the configuration profile. It requires a query vector and can
    optionally apply a filter to narrow down the search results.
    
    Args:
        ctx (click.Context): The Click context object containing the initialized client.
        query_vector (Optional[str]): JSON string representing the query vector
            (a list of floats). Required for search.
        query_filter_json (Optional[str]): JSON string representing a Qdrant filter
            to apply to the search results.
        limit (int): Maximum number of results to return. Defaults to 10.
        with_vectors (bool): If True, include vectors in the output. Defaults to False.
        with_payload (bool): If True, include payload in the output. Defaults to True.
        
    Raises:
        ConfigurationError: If the collection name is missing from the configuration.
        click.UsageError: If the query vector is missing or invalid.
        CollectionDoesNotExistError: If the specified collection does not exist.
        InvalidInputError: If the provided query vector or filter is invalid.
        SystemExit: If an error occurs during the search operation.
        
    Examples:
        $ docstore-manager qdrant search --query-vector '[0.1, 0.2, 0.3]'
        $ docstore-manager qdrant search --query-vector '[0.1, 0.2, 0.3]' --query-filter-json '{"must": [{"key": "category", "match": {"value": "electronics"}}]}'
        $ docstore-manager qdrant search --query-vector '[0.1, 0.2, 0.3]' --limit 5 --with-vectors
    """
    client: QdrantClient = ctx.obj['client']
    profile: str = ctx.obj['PROFILE']
    config_path: Optional[Path] = ctx.obj.get('CONFIG_PATH')

    try:
        # Load config to get collection name
        config_data = load_config(profile=profile, config_path=config_path)
        qdrant_config = config_data.get('qdrant', {})
        connection_config = qdrant_config.get('connection', {})
        collection_name = connection_config.get('collection')
        if not collection_name:
            raise ConfigurationError(f"'qdrant.connection.collection' name missing in profile '{profile}'.")
        logger.info(f"Operating on collection '{collection_name}' defined in profile '{profile}'.")

        # Validate and parse query vector
        if not query_vector:
             raise click.UsageError("--query-vector is required for search.")
        try:
            parsed_vector = json.loads(query_vector)
            if not isinstance(parsed_vector, list) or not all(isinstance(x, (int, float)) for x in parsed_vector):
                 raise ValueError("Query vector must be a JSON array of numbers.")
        except (json.JSONDecodeError, ValueError) as e:
             raise click.UsageError(f"Invalid JSON for --query-vector: {e}")

        # Parse filter if provided
        parsed_filter: Optional[Filter] = None # Need Filter type from qdrant_client.http.models
        if query_filter_json:
             try:
                 filter_dict = json.loads(query_filter_json)
                 if not isinstance(filter_dict, dict):
                     raise ValueError("Filter must be a JSON object.")
                 # Attempt to create Filter object for validation
                 from qdrant_client.http.models import Filter # Import here or at top
                 parsed_filter = Filter(**filter_dict) 
             except (json.JSONDecodeError, ValueError) as e:
                 raise click.UsageError(f"Invalid JSON for --query-filter-json: {e}")
             except Exception as e: # Catch pydantic errors
                  raise click.UsageError(f"Invalid filter structure for --query-filter-json: {e}")

        # Call the refactored command function
        cmd_search_documents(
            client=client,
            collection_name=collection_name,
            query_vector=parsed_vector,
            query_filter=parsed_filter,
            limit=limit,
            with_payload=with_payload,
            with_vectors=with_vectors
        )

    except ConfigurationError as e:
        logger.error(f"Configuration error for profile '{profile}': {e}")
        click.echo(f"ERROR: Configuration error - {e}", err=True)
        sys.exit(1)
    except click.UsageError as e:
        click.echo(f"Usage Error: {e}", err=True)
        sys.exit(1)
    except Exception as e: # Catch other potential errors
        logger.error(f"Error during search command: {e}", exc_info=True)
        click.echo(f"ERROR: Failed during search command - {e}", err=True)
        sys.exit(1)
