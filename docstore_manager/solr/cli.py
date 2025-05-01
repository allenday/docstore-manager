#!/usr/bin/env python3
"""
Solr Click command definitions.

Provides commands to create, delete, list and modify collections, as well as perform
batch operations on documents within collections, integrated with the main Click app.
"""
import os
import sys
import argparse # Keep temporarily if needed by underlying commands
import logging
from pathlib import Path
from typing import Any, Optional, Tuple
import json
import click # Ensure click is imported

try:
    import pysolr
except ImportError:
    print("Error: pysolr is not installed. Please run: pip install pysolr")
    sys.exit(1)

# Keep necessary imports 
from docstore_manager.solr.client import SolrClient
from docstore_manager.solr.format import SolrFormatter
from docstore_manager.solr.command import SolrCommand
from docstore_manager.solr.commands import (
    list_collections as cmd_list_collections,
    delete_collection as cmd_delete_collection,
    create_collection as cmd_create_collection,
    collection_info as cmd_collection_info,
    add_documents as cmd_add_documents,
    remove_documents as cmd_remove_documents,
    get_documents as cmd_get_documents,
    show_config_info as cmd_show_config_info,
    search_documents as cmd_search_documents,
)
from docstore_manager.core.config.base import load_config # Added
from docstore_manager.core.exceptions import ConfigurationError, ConnectionError # Added

logger = logging.getLogger(__name__)

# --- Removed SolrCLI class and argparse-related code --- 

# --- Click Integration --- 

# Helper function to initialize the Solr client for Click commands
def initialize_solr_command(ctx: click.Context, profile: str, config_path: Optional[Path]):
    """Initialize the SolrClient based on context and args.
    Stores the client instance in ctx.obj['solr_client'] 
    and the target collection name in ctx.obj['solr_collection'].
    Expects ctx.obj to be a dict.
    """
    # Check if client is already initialized in the context
    if 'solr_client' in ctx.obj and isinstance(ctx.obj['solr_client'], SolrClient):
        return # Already initialized

    try:
        # Load configuration using the core load_config function
        config_data = load_config(profile=profile, config_path=config_path)
        solr_profile_config = config_data.get('solr', {})
        solr_connection_config = solr_profile_config.get('connection', {})

        # Extract primary connection details
        solr_url = solr_connection_config.get('url')
        zk_hosts = solr_connection_config.get('zk_hosts')
        collection_name = solr_connection_config.get('collection') # Get collection name
        timeout = solr_connection_config.get('timeout')

        if not collection_name:
             raise ConfigurationError(
                "Solr 'collection' name not found in profile connection details.",
                details=f"Profile: '{profile}', Config File: {config_path}"
            )

        # Create the config dictionary for SolrClient constructor
        client_config_dict = {
            'collection': collection_name, # Client needs collection name too
            'timeout': timeout
        }
        if solr_url:
             client_config_dict['solr_url'] = solr_url
             logger.debug(f"Initializing SolrClient with URL: {solr_url}")
        elif zk_hosts:
             client_config_dict['zk_hosts'] = zk_hosts
             logger.debug(f"Initializing SolrClient with ZK hosts: {zk_hosts}")
        else:
            raise ConfigurationError(
                "Solr connection details (url or zk_hosts) not found in profile.",
                details=f"Profile: '{profile}', Config File: {config_path}"
            )
            
        # Initialize the SolrClient with the config dictionary
        solr_client = SolrClient(client_config_dict)
        
        # Store client and collection name in context
        if not isinstance(ctx.obj, dict):
             ctx.obj = {}
        ctx.obj['solr_client'] = solr_client 
        ctx.obj['solr_collection'] = collection_name # Store collection name from config
        logger.info(f"Initialized SolrClient for profile '{profile}' targeting collection '{collection_name}'.")
        # No return needed, modifies context directly

    except ConfigurationError as e:
        logger.error(f"Solr configuration error for profile '{profile}': {e}")
        click.echo(f"ERROR: Solr configuration error - {e}", err=True)
        sys.exit(1)
    except ConnectionError as e:
         logger.error(f"Solr connection error for profile '{profile}': {e}")
         click.echo(f"ERROR: Solr connection error - {e}", err=True)
         sys.exit(1)
    except ImportError as e: 
        logger.error(f"Error importing pysolr: {e}")
        click.echo(f"ERROR: Error importing pysolr - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        is_debug = isinstance(ctx.obj, dict) and ctx.obj.get('DEBUG', False)
        logger.error(f"Failed to initialize Solr client for profile '{profile}': {e}", exc_info=is_debug)
        click.echo(f"ERROR: Failed to initialize Solr client - {e}", err=True)
        sys.exit(1)

# Click command definition for listing collections/cores
@click.command("list")
@click.pass_context
def list_collections_cli(ctx: click.Context):
    """List Solr collections/cores."""
    if 'solr_client' not in ctx.obj or not isinstance(ctx.obj['solr_client'], SolrClient):
         logger.error("SolrClient not initialized in context.")
         click.echo("ERROR: SolrClient not initialized. Check group setup.", err=True)
         sys.exit(1)
         
    solr_client: SolrClient = ctx.obj['solr_client']
    
    # Call the imported function
    try:
        click.echo("Executing list_collections function (placeholder call)...")
        # The function likely expects the old args namespace. We need to adapt.
        # For list, it might not need specific args beyond what's in the handler/client.
        # TODO: Refactor cmd_list_collections to accept handler/client and specific params.
        # cmd_list_collections(command=command_handler, args=None) # Placeholder call, args need mapping
        pass 
    except Exception as e:
        logger.error(f"Error executing list command: {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing list command: {e}", err=True)
        sys.exit(1)

# === Create Collection ===
@click.command("create")
@click.argument('name', type=str)
@click.option('--num-shards', type=int, help='Number of shards for the new collection.')
@click.option('--replication-factor', type=int, help='Replication factor for the new collection.')
@click.option('--configset', help='Name of the configSet to use (e.g., _default).')
@click.option('--overwrite', is_flag=True, default=False, help='Overwrite if collection exists.')
@click.pass_context
def create_collection_cli(ctx: click.Context, name: str, num_shards: Optional[int], replication_factor: Optional[int], configset: Optional[str], overwrite: bool):
    """Create a new Solr collection/core."""
    if 'solr_client' not in ctx.obj or not isinstance(ctx.obj['solr_client'], SolrClient):
        logger.error("SolrClient not initialized in context.")
        click.echo("ERROR: SolrClient not initialized.", err=True)
        sys.exit(1)
    solr_client: SolrClient = ctx.obj['solr_client']
    
    # Get config values from profile if not provided as args (sensible defaults)
    # These are loaded during initialization but not stored directly in ctx.obj yet
    # Let's reload config here for simplicity, or ideally store them in context during init
    profile = ctx.obj['PROFILE']
    config_path = ctx.obj['CONFIG_PATH']
    config_data = load_config(profile=profile, config_path=config_path)
    solr_conn_config = config_data.get('solr', {}).get('connection', {})
    
    num_shards = num_shards if num_shards is not None else solr_conn_config.get('num_shards')
    replication_factor = replication_factor if replication_factor is not None else solr_conn_config.get('replication_factor')
    configset = configset if configset is not None else solr_conn_config.get('config_name') # Use config_name from profile

    try:
        logger.info(f"Attempting to create collection '{name}'...")
        success, message = cmd_create_collection(
            client=solr_client, 
            collection_name=name, 
            num_shards=num_shards, 
            replication_factor=replication_factor,
            config_name=configset,
            overwrite=overwrite
        )
        if success:
            click.echo(message)
            logger.info(message)
        else:
            # cmd_create_collection should raise exceptions on failure, 
            # but handle potential False return just in case.
            click.echo(f"WARN: {message}", err=True)
            logger.warning(message)
            # sys.exit(1) # Maybe don't exit on just a warning? Depends on command logic.

    except Exception as e:
        logger.error(f"Error executing create command for '{name}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing create command: {e}", err=True)
        sys.exit(1)

# === Delete Collection ===
@click.command("delete")
@click.argument('name', type=str)
@click.option('--yes', '-y', is_flag=True, default=False, help='Skip confirmation prompt.') # Added confirmation flag
@click.pass_context
def delete_collection_cli(ctx: click.Context, name: str, yes: bool):
    """Delete an existing Solr collection/core."""
    if 'solr_client' not in ctx.obj or not isinstance(ctx.obj['solr_client'], SolrClient):
        logger.error("SolrClient not initialized in context.")
        click.echo("ERROR: SolrClient not initialized.", err=True)
        sys.exit(1)
    solr_client: SolrClient = ctx.obj['solr_client']
    # Add confirmation prompt
    if not yes and not click.confirm(f"Are you sure you want to delete the collection '{name}'?"):
        click.echo("Aborted.")
        sys.exit(0)
    try:
        click.echo(f"Executing delete_collection function for '{name}' (placeholder call)...")
        # TODO: Refactor cmd_delete_collection
        # result = cmd_delete_collection(command=command_handler, name=name)
        pass
    except Exception as e:
        logger.error(f"Error executing delete command: {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing delete command: {e}", err=True)
        sys.exit(1)

# === Collection Info ===
@click.command("info")
@click.argument('name', type=str)
@click.pass_context
def collection_info_cli(ctx: click.Context, name: str):
    """Get detailed information about a collection/core."""
    if 'solr_client' not in ctx.obj or not isinstance(ctx.obj['solr_client'], SolrClient):
        logger.error("SolrClient not initialized in context.")
        click.echo("ERROR: SolrClient not initialized.", err=True)
        sys.exit(1)
    solr_client: SolrClient = ctx.obj['solr_client']
    try:
        click.echo(f"Executing collection_info function for '{name}' (placeholder call)...")
        # TODO: Refactor cmd_collection_info
        # result = cmd_collection_info(command=command_handler, name=name)
        pass
    except Exception as e:
        logger.error(f"Error executing info command: {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing info command: {e}", err=True)
        sys.exit(1)

# === Add Documents ===
@click.command("add-documents")
@click.option('--doc', required=True, help='JSON string or path to JSON/JSONL file (@filename) containing documents.')
@click.option('--commit/--no-commit', default=True, help='Perform Solr commit after adding.')
@click.option('--batch-size', type=int, default=500, show_default=True, help='Number of documents per batch request.')
@click.pass_context
def add_documents_cli(ctx: click.Context, doc: str, commit: bool, batch_size: int):
    """Add or update documents in the configured collection."""
    if 'solr_client' not in ctx.obj or not isinstance(ctx.obj['solr_client'], SolrClient):
        logger.error("SolrClient not initialized in context.")
        click.echo("ERROR: SolrClient not initialized.", err=True)
        sys.exit(1)
    solr_client: SolrClient = ctx.obj['solr_client']
    collection_name: str = ctx.obj['solr_collection'] # Get collection from context
    try:
        # Call the refactored command function with correct alias
        success, message = cmd_add_documents(
            client=solr_client, 
            collection_name=collection_name, 
            doc_input=doc, # Pass the raw --doc input 
            commit=commit, 
            batch_size=batch_size
        )
        # Output based on result
        if success:
             click.echo(message)
        else:
             click.echo(f"WARN: {message}", err=True)
             # Decide if non-success always warrants non-zero exit
             # sys.exit(1) 

    except Exception as e:
        logger.error(f"Error executing add command: {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing add command: {e}", err=True)
        sys.exit(1)

# === Remove Documents ===
@click.command("remove-documents")
@click.option('--id-file', type=click.Path(exists=True, dir_okay=False), help='Path to file containing document IDs (one per line).')
@click.option('--ids', help='Comma-separated list of document IDs.')
@click.option('--query', help='Solr query string to select documents for deletion.')
@click.option('--commit/--no-commit', default=True, help='Perform Solr commit after deleting.')
@click.option('--yes', '-y', is_flag=True, default=False, help='Skip confirmation prompt for query deletion.')
@click.pass_context
def remove_documents_cli(ctx: click.Context, id_file: Optional[str], ids: Optional[str], query: Optional[str], commit: bool, yes: bool):
    """Remove documents by IDs or query from the configured collection."""
    if not id_file and not ids and not query:
         click.echo("Error: Must provide --id-file, --ids, or --query to select documents for deletion.", err=True)
         sys.exit(1)
    if len([arg for arg in [id_file, ids, query] if arg]) > 1:
         click.echo("Error: --id-file, --ids, and --query are mutually exclusive.", err=True)
         sys.exit(1)

    if 'solr_client' not in ctx.obj or not isinstance(ctx.obj['solr_client'], SolrClient):
        logger.error("SolrClient not initialized in context.")
        click.echo("ERROR: SolrClient not initialized.", err=True)
        sys.exit(1)
    solr_client: SolrClient = ctx.obj['solr_client']
    collection_name: str = ctx.obj['solr_collection'] # Get collection from context

    # Add confirmation for query-based deletion
    if query and not yes and not click.confirm(f"Are you sure you want to delete documents matching query '{query}' in collection '{collection_name}'?"):
         click.echo("Aborted.")
         sys.exit(0)

    try:
        # Call the refactored command function with correct alias
        success, message = cmd_remove_documents(
            client=solr_client,
            collection_name=collection_name,
            id_file=id_file,
            ids=ids,
            query=query,
            commit=commit
        )
        # Output based on result
        if success:
            click.echo(message)
        else:
            click.echo(f"WARN: {message}", err=True)
            # Consider if non-success always warrants non-zero exit
            # sys.exit(1) 
            
    except Exception as e:
        logger.error(f"Error executing remove-documents command: {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing remove-documents command: {e}", err=True)
        sys.exit(1)

# === Get Documents ===
@click.command("get")
@click.option('--id-file', type=click.Path(exists=True, dir_okay=False), help='Path to file containing document IDs (one per line).')
@click.option('--ids', help='Comma-separated list of document IDs.')
@click.option('--query', default='*:*', show_default=True, help='Solr query string to select documents.')
@click.option('--fields', default='*', show_default=True, help='Comma-separated list of fields to retrieve.')
@click.option('--limit', type=int, default=10, show_default=True, help='Maximum number of documents to retrieve.')
@click.option('--format', type=click.Choice(['json', 'csv'], case_sensitive=False), default='json', show_default=True, help='Output format.')
@click.option('--output', type=click.Path(dir_okay=False, writable=True), help='Output file path (prints to stdout if not specified).')
@click.pass_context
def get_documents_cli(ctx: click.Context, id_file: Optional[str], ids: Optional[str], query: str, fields: str, limit: int, format: str, output: Optional[str]):
    """Retrieve documents by IDs or query from the configured collection."""
    # Basic validation: only one selector allowed (similar to remove-documents)
    if len([arg for arg in [id_file, ids] if arg]) > 1:
         click.echo("Error: --id-file and --ids are mutually exclusive.", err=True)
         sys.exit(1)
    # If id_file or ids are provided, the default query might be ignored or handled by the underlying command
    
    if 'solr_client' not in ctx.obj or not isinstance(ctx.obj['solr_client'], SolrClient):
        logger.error("SolrClient not initialized in context.")
        click.echo("ERROR: SolrClient not initialized.", err=True)
        sys.exit(1)
    solr_client: SolrClient = ctx.obj['solr_client']
    collection_name: str = ctx.obj['solr_collection'] # Get collection from context
    try:
        # TODO: Refactor cmd_get_documents and call it here
        # Pass client, collection_name, selectors (ids/file/query), fields, limit, format, output
        click.echo(f"Executing get_documents function for '{collection_name}' (placeholder call)...")
        pass
    except Exception as e:
        logger.error(f"Error executing get command: {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing get command: {e}", err=True)
        sys.exit(1)

# === Config Info ===
@click.command("config")
@click.option('--show-profiles', is_flag=True, default=False, help='List the names of all configured profiles.')
@click.pass_context
def show_config_info_cli(ctx: click.Context, show_profiles: bool):
    """Show configuration information."""
    # This command might not need the client/handler if it only interacts with config files
    try:
        click.echo(f"Executing show_config_info function (placeholder call)...")
        # TODO: Refactor cmd_show_config_info if needed (might not need client)
        # result = cmd_show_config_info(show_profiles=show_profiles, config_path=ctx.obj.get('CONFIG_PATH'))
        pass
    except Exception as e:
        logger.error(f"Error executing config command: {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing config command: {e}", err=True)
        sys.exit(1)

# === Search Documents ===
@click.command("search")
@click.option('--query', '-q', default='*:*', show_default=True, help='Solr query string (q parameter).')
@click.option('--filter', '-f', 'filter_query', multiple=True, help='Filter query (fq parameter). Can be used multiple times.')
@click.option('--fields', '-fl', help='Comma-separated list of fields to return (fl parameter).')
@click.option('--limit', '-l', type=int, default=10, show_default=True, help='Maximum number of documents to return (rows parameter).')
# Add format/output options if needed, similar to 'get' command
@click.pass_context
def search_documents_cli(ctx: click.Context, query: str, filter_query: Tuple[str], fields: Optional[str], limit: int):
    """Search documents in the configured collection."""
    if 'solr_client' not in ctx.obj or not isinstance(ctx.obj['solr_client'], SolrClient):
        logger.error("SolrClient not initialized in context.")
        click.echo("ERROR: SolrClient not initialized.", err=True)
        sys.exit(1)
    solr_client: SolrClient = ctx.obj['solr_client']
    collection_name: str = ctx.obj['solr_collection']

    try:
        # Call the refactored command function
        success, results = cmd_search_documents(
            client=solr_client,
            collection_name=collection_name,
            query=query,
            filter_query=list(filter_query) if filter_query else None,
            fields=fields,
            limit=limit
        )
        
        # Output results (simple JSON print for now)
        if success:
            click.echo(json.dumps(results, indent=2))
        else:
            click.echo(f"ERROR: {results}", err=True)
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error executing search command: {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing search command: {e}", err=True)
        sys.exit(1)

# Add commands to Click group
solr = click.Group()
solr.add_command(list_collections_cli, name="list")
solr.add_command(create_collection_cli, name="create")
solr.add_command(delete_collection_cli, name="delete")
solr.add_command(collection_info_cli, name="info")
solr.add_command(add_documents_cli, name="add-documents")
solr.add_command(remove_documents_cli, name="remove-documents")
solr.add_command(get_documents_cli, name="get")
solr.add_command(show_config_info_cli, name="config")
solr.add_command(search_documents_cli, name="search")