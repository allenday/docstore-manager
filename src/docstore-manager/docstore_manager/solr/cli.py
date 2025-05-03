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

# Configure logging early
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Get logger for this module

try:
    import pysolr
except ImportError:
    logger.error("Error: pysolr is not installed. Please run: pip install pysolr")
    sys.exit(1)

# Keep necessary imports 
from docstore_manager.solr.client import SolrClient as RealSolrClient
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
from docstore_manager.core.config.base import load_config, get_config_dir, get_profiles
from docstore_manager.core.exceptions import (
    ConfigurationError, 
    ConnectionError, 
    DocumentStoreError, 
    InvalidInputError, 
    CollectionError,
    CollectionDoesNotExistError # Added
)

# --- Removed SolrCLI class and argparse-related code --- 

# --- Click Integration --- 

# Helper function to initialize the Solr client for Click commands
def initialize_solr_client(ctx: click.Context, profile: str, config_path: Optional[Path]) -> SolrClient:
    """Initialize and return the Solr client based on context and args.
    Stores the client in ctx.obj['client'].
    Expects ctx.obj to be a dict.
    """
    # Check if client is already initialized
    if 'client' in ctx.obj and isinstance(ctx.obj['client'], SolrClient):
        return ctx.obj['client']

    try:
        config_data = load_config(profile=profile, config_path=config_path)
        solr_profile_config = config_data.get('solr', {})
        solr_connection_config = solr_profile_config.get('connection', {})
        
        logger.debug(f"Loaded Solr config for profile '{profile}': {solr_connection_config}")

        # Prepare config dict for SolrClient constructor
        client_config_dict = {}
        if 'solr_url' in solr_connection_config:
             client_config_dict['solr_url'] = solr_connection_config['solr_url']
        if 'zk_hosts' in solr_connection_config and solr_connection_config['zk_hosts']:
             client_config_dict['zk_hosts'] = solr_connection_config['zk_hosts']
        if 'collection' in solr_connection_config:
            client_config_dict['collection'] = solr_connection_config['collection']
        else:
             # Client requires collection, ensure it's present
             raise ConfigurationError("Solr 'collection' name missing in profile connection details.",
                                       details=f"Profile: '{profile}'")
        if 'timeout' in solr_connection_config:
             client_config_dict['timeout'] = solr_connection_config['timeout']

        if 'solr_url' not in client_config_dict and 'zk_hosts' not in client_config_dict:
            raise ConfigurationError("Solr connection details (url or zk_hosts) not found in profile.",
                                       details=f"Profile: '{profile}'")

        logger.debug(f"Final client_config_dict before SolrClient init: {client_config_dict}") # DEBUG
        logger.debug(f"Initializing SolrClient with config: {client_config_dict}")
        client = SolrClient(config=client_config_dict)
        
        # Store client in context
        if not isinstance(ctx.obj, dict):
             ctx.obj = {}
        ctx.obj['client'] = client 
        ctx.obj['SOLR_COLLECTION'] = client_config_dict['collection'] # Store collection name
        logger.info(f"Initialized SolrClient for profile '{profile}' targeting collection '{client_config_dict['collection']}'.")
        return client

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        click.echo(f"ERROR: Configuration error - {e}", err=True)
        sys.exit(1)
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        click.echo(f"ERROR: Connection error - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        is_debug = isinstance(ctx.obj, dict) and ctx.obj.get('DEBUG', False)
        logger.error(f"Failed to initialize Solr client: {e}", exc_info=is_debug)
        click.echo(f"ERROR: Failed to initialize Solr client - {e}", err=True)
        sys.exit(1)

# Click command definition for listing collections/cores
@click.group()
@click.option("--profile", default="default", show_default=True, help="Configuration profile to use.")
@click.option("--config-path", type=click.Path(exists=True, dir_okay=False), help="Path to configuration file (e.g., config.yaml).")
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging.") # Added debug flag
@click.pass_context
def solr_cli(ctx: click.Context, profile: str, config_path: Optional[str], debug: bool):
    """Manage Solr collections and documents."""
    ctx.ensure_object(dict)
    ctx.obj['PROFILE'] = profile
    ctx.obj['CONFIG_PATH'] = Path(config_path) if config_path else None
    ctx.obj['DEBUG'] = debug
    
    # Initialize client here - it will be available to all subcommands
    # Subcommands that don't need the client (like config info) can ignore it
    try:
        # Attempt init only if not the 'config' command (which doesn't need client)
        # Check invoked subcommand name
        if ctx.invoked_subcommand != 'config': 
            initialize_solr_client(ctx, profile, ctx.obj['CONFIG_PATH'])
        else:
            logger.debug("Skipping client initialization for 'config' command.")
            
    except Exception as e:
        # Error handling is inside initialize_solr_client, which exits
        # This try/except might be redundant if init helper always exits on failure
        logger.critical(f"Unhandled exception during Solr CLI setup: {e}", exc_info=debug)
        click.echo(f"CRITICAL ERROR during setup: {e}", err=True)
        sys.exit(1)

# === List Collections ===
@solr_cli.command("list") 
@click.option("--output", "output_path", type=click.Path(dir_okay=False, writable=True), help="Optional path to output the list as JSON.")
@click.pass_context
def list_collections_cli(ctx: click.Context, output_path: Optional[str]):
    """List Solr collections/cores."""
    if 'client' not in ctx.obj or not isinstance(ctx.obj['client'], RealSolrClient):
         logger.error("SolrClient not initialized in context for list.")
         click.echo("ERROR: Client not initialized. Check group setup or connection.", err=True)
         sys.exit(1)
         
    client: RealSolrClient = ctx.obj['client']
    
    try:
        # Call the imported function with direct args
        cmd_list_collections(client=client, output_path=output_path)
        logger.info("List command completed.")
    except DocumentStoreError as e:
        logger.error(f"Error listing collections: {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error executing list command: {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing list command: {e}", err=True)
        sys.exit(1)

# === Create Collection ===
@solr_cli.command("create")
@click.argument('name') # Use collection name from profile by default?
@click.option('--num-shards', type=int, help='Number of shards.')
@click.option('--replication-factor', type=int, help='Replication factor.')
@click.option('--configset', help='Name of the configSet.')
@click.option('--overwrite', is_flag=True, default=False, help='Overwrite if exists.')
@click.pass_context
def create_collection_cli(ctx: click.Context, name: Optional[str], num_shards: Optional[int], 
                           replication_factor: Optional[int], configset: Optional[str], overwrite: bool):
    """Create a new Solr collection/core."""
    client: SolrClient = ctx.obj['client']
    profile_collection_name = ctx.obj.get('SOLR_COLLECTION')
    collection_to_create = name if name else profile_collection_name

    if not collection_to_create:
        click.echo("ERROR: Collection name must be provided via argument or profile configuration.", err=True)
        sys.exit(1)

    # Get config values from profile if not provided as args
    profile = ctx.obj['PROFILE']
    config_path = ctx.obj['CONFIG_PATH']
    config_data = load_config(profile=profile, config_path=config_path)
    solr_conn_config = config_data.get('solr', {}).get('connection', {})
    
    # Prioritize CLI args over config file values
    num_shards_final = num_shards if num_shards is not None else solr_conn_config.get('num_shards')
    replication_factor_final = replication_factor if replication_factor is not None else solr_conn_config.get('replication_factor')
    configset_final = configset if configset is not None else solr_conn_config.get('config_name')

    try:
        logger.info(f"Attempting to create collection '{collection_to_create}'...")
        # Assuming cmd_create_collection now accepts these args directly
        success, message = cmd_create_collection(
            client=client, 
            collection_name=collection_to_create, 
            num_shards=num_shards_final, 
            replication_factor=replication_factor_final,
            config_name=configset_final,
            overwrite=overwrite
        )
        if success:
            click.echo(message)
            logger.info(message)
        else:
            click.echo(f"WARN: {message}", err=True)
            logger.warning(message)

    except CollectionError as e:
         logger.error(f"Error creating collection '{collection_to_create}': {e}", exc_info=ctx.obj.get('DEBUG', False))
         click.echo(f"ERROR: {e}", err=True)
         sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error executing create command for '{collection_to_create}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing create command: {e}", err=True)
        sys.exit(1)

# === Delete Collection ===
@solr_cli.command("delete")
@click.argument('name', required=False) # Make optional, will use profile default if None
@click.option('--yes', '-y', is_flag=True, default=False, help='Skip confirmation prompt.')
@click.pass_context
def delete_collection_cli(ctx: click.Context, name: Optional[str], yes: bool):
    """Delete an existing Solr collection/core."""
    client: SolrClient = ctx.obj['client']
    profile_collection_name = ctx.obj.get('SOLR_COLLECTION')
    collection_to_delete = name if name else profile_collection_name

    if not collection_to_delete:
        click.echo("ERROR: Collection name must be provided via argument or profile configuration.", err=True)
        sys.exit(1)
        
    # Add confirmation prompt
    if not yes:
        click.confirm(f"Are you sure you want to delete the collection '{collection_to_delete}'?", abort=True)
        
    try:
        # Call the imported function directly (assuming it's refactored)
        cmd_delete_collection(client=client, collection_name=collection_to_delete)
        logger.info(f"Delete command executed for collection '{collection_to_delete}'.")
        click.echo(f"Collection '{collection_to_delete}' deleted successfully.") # Assume success if no exception
    except CollectionDoesNotExistError as e:
        logger.warning(f"Collection '{collection_to_delete}' not found for deletion: {e}")
        click.echo(f"WARN: Collection '{collection_to_delete}' not found.", err=True)
        # Do not exit with error if collection simply doesn't exist
    except DocumentStoreError as e:
        logger.error(f"Error deleting collection '{collection_to_delete}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error executing delete command for '{collection_to_delete}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing delete command: {e}", err=True)
        sys.exit(1)

# === Collection Info ===
@solr_cli.command("info")
@click.argument('name', required=False) # Use profile default if not provided
@click.pass_context
def collection_info_cli(ctx: click.Context, name: Optional[str]):
    """Get detailed information about a collection/core."""
    client: SolrClient = ctx.obj['client']
    profile_collection_name = ctx.obj.get('SOLR_COLLECTION')
    collection_to_info = name if name else profile_collection_name

    if not collection_to_info:
        click.echo("ERROR: Collection name must be provided via argument or profile configuration.", err=True)
        sys.exit(1)
        
    try:
        # Call the imported function directly (assuming it's refactored)
        cmd_collection_info(client=client, collection_name=collection_to_info)
        logger.info(f"Info command executed for collection '{collection_to_info}'.")
    except DocumentStoreError as e: # Ensure this exception is imported
        logger.error(f"Error getting info for '{collection_to_info}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error executing info command for '{collection_to_info}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing info command: {e}", err=True)
        sys.exit(1)

# === Add Documents ===
@solr_cli.command("add-documents")
# Allow collection override via option
@click.option('--collection', help='Target collection name (overrides profile default).') 
@click.option('--doc', required=True, help='JSON string or path to JSON/JSONL file (@filename) containing documents.')
@click.option('--commit/--no-commit', default=True, help='Perform Solr commit after adding.')
@click.option('--batch-size', type=int, default=100, show_default=True, help='Documents per batch.')
@click.pass_context
def add_documents_cli(ctx: click.Context, collection: Optional[str], doc: str, commit: bool, batch_size: int):
    """Add/update documents in the specified Solr collection."""
    client: SolrClient = ctx.obj['client']
    target_collection = collection or client.config.get('collection')
    if not target_collection:
        click.echo("ERROR: No collection specified and no default collection found in profile.", err=True)
        sys.exit(1)
        
    # Explicitly set log level if debug is on
    if ctx.obj.get('DEBUG', False):
        logging.getLogger('docstore_manager').setLevel(logging.DEBUG)
        logger.debug("Set docstore_manager log level to DEBUG.")

    try:
        success, message = cmd_add_documents(
            client=client, 
            collection_name=target_collection,
            doc_input=doc, # Parameter name might need adjustment based on refactored command
            commit=commit,
            batch_size=batch_size 
        )
        logger.info(f"Add documents command executed for collection '{target_collection}'. Message: {message}") # Log message
        if success:
             logger.info(f"Command successful, printing message to stdout: {message}") # DEBUG
             click.echo(message) # Print the success message to stdout
        else:
             # Should not happen if exceptions are raised correctly, but handle just in case
             logger.warning(f"Command returned success=False, printing WARN: {message}") # DEBUG
             click.echo(f"WARN: {message}", err=True)

    except DocumentStoreError as e:
        logger.error(f"Error adding documents to '{target_collection}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)
    except InvalidInputError as e:
        logger.error(f"Invalid input for adding documents to '{target_collection}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR: Invalid input - {e}", err=True)
        sys.exit(1)

# === Remove Documents ===
@solr_cli.command("remove-documents")
@click.option('--collection', help='Target collection name (overrides profile default).')
@click.option('--id-file', type=click.Path(exists=True, dir_okay=False), help='Path to file containing document IDs (one per line).')
@click.option('--ids', help='Comma-separated list of document IDs.')
@click.option('--query', help='Solr query string to select documents for deletion.')
@click.option('--commit/--no-commit', default=True, help='Perform Solr commit after deleting.')
@click.option('--yes', '-y', is_flag=True, default=False, help='Skip confirmation prompt for query deletion.')
@click.pass_context
def remove_documents_cli(ctx: click.Context, collection: Optional[str], id_file: Optional[str], 
                         ids: Optional[str], query: Optional[str], commit: bool, yes: bool):
    """Remove documents from the specified Solr collection."""
    client: SolrClient = ctx.obj['client']
    target_collection = collection if collection else ctx.obj.get('SOLR_COLLECTION')

    if not target_collection:
        click.echo("ERROR: Collection name must be provided via --collection option or profile configuration.", err=True)
        sys.exit(1)
        
    # Input validation
    input_methods = sum(1 for item in [id_file, ids, query] if item is not None)
    if input_methods == 0:
        click.echo("ERROR: Must provide one of --id-file, --ids, or --query.", err=True)
        sys.exit(1)
    if input_methods > 1:
        click.echo("ERROR: Use only one of --id-file, --ids, or --query.", err=True)
        sys.exit(1)
        
    # Confirmation for query deletion
    if query and not yes:
        click.confirm(f"Are you sure you want to delete documents matching query '{query}' from '{target_collection}'?", abort=True)
        
    # Explicitly set log level if debug is on
    if ctx.obj.get('DEBUG', False):
        logging.getLogger('docstore_manager').setLevel(logging.DEBUG)
        logger.debug("Set docstore_manager log level to DEBUG.")
        
    try:
        success, message = cmd_remove_documents( # Unpack result
            client=client, 
            collection_name=target_collection,
            id_file=id_file, 
            ids=ids, 
            query=query, 
            commit=commit
        )
        logger.info(f"Remove documents command executed for collection '{target_collection}'. Message: {message}") # Log message
        if success:
             logger.info(f"Command successful, printing message to stdout: {message}") # DEBUG
             click.echo(message) # Print the success message to stdout
        else:
             # Should not happen if exceptions are raised correctly, but handle just in case
             logger.warning(f"Command returned success=False, printing WARN: {message}") # DEBUG
             click.echo(f"WARN: {message}", err=True)
             
    except DocumentStoreError as e:
        logger.error(f"Error removing documents from '{target_collection}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)
    except InvalidInputError as e:
        logger.error(f"Invalid input for removing documents from '{target_collection}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR: Invalid input - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error executing remove documents command for '{target_collection}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing remove documents command: {e}", err=True)
        sys.exit(1)

        # === Get Documents ===
@solr_cli.command("get")
@click.option('--collection', help='Target collection name (overrides profile default).')
@click.option('--id-file', type=click.Path(exists=True, dir_okay=False), help='Path to file containing document IDs (one per line).')
@click.option('--ids', help='Comma-separated list of document IDs.')
@click.option('--query', default='*:*', show_default=True, help='Solr query string to select documents.')
@click.option('--fields', default='*', show_default=True, help='Comma-separated list of fields to retrieve.')
@click.option('--limit', type=int, default=10, show_default=True, help='Maximum number of documents to retrieve.')
@click.option('--format', type=click.Choice(['json', 'csv'], case_sensitive=False), default='json', show_default=True, help='Output format.')
@click.option('--output', type=click.Path(dir_okay=False, writable=True), help='Output file path (prints to stdout if not specified).')
@click.pass_context
def get_documents_cli(ctx: click.Context, collection: Optional[str], id_file: Optional[str], ids: Optional[str], 
                      query: str, fields: str, limit: int, format: str, output: Optional[str]):
    """Retrieve documents from the specified Solr collection."""
    client: SolrClient = ctx.obj['client']
    target_collection = collection if collection else ctx.obj.get('SOLR_COLLECTION')

    if not target_collection:
        click.echo("ERROR: Collection name must be provided via --collection option or profile configuration.", err=True)
        sys.exit(1)
        
    # Input validation (Allow only one of ids, id_file)
    if ids and id_file:
        click.echo("ERROR: Use only one of --ids or --id-file.", err=True)
        sys.exit(1)
        
    try:
        # Call the imported function directly (assuming it's refactored)
        cmd_get_documents(
            client=client,
            collection_name=target_collection,
            id_file=id_file,
            ids=ids,
            query=query if not (ids or id_file) else None,
            fields=fields,
            limit=limit,
            output_format=format, # Map CLI option to function arg name
            output_path=output
        )
        logger.info(f"Get documents command executed for collection '{target_collection}'.")
    except DocumentStoreError as e:
        logger.error(f"Error getting documents from '{target_collection}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)
    except InvalidInputError as e:
        logger.error(f"Invalid input for getting documents from '{target_collection}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR: Invalid input - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error executing get documents command for '{target_collection}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing get documents command: {e}", err=True)
        sys.exit(1)

# === Config Info ===
@solr_cli.command("config")
# Takes profile/config_path from the group
@click.pass_context
def show_config_info_cli(ctx: click.Context):
    """Display Solr configuration information (directory, profiles)."""
    # This command doesn't need the initialized client
    try:
        # Call directly (assuming refactored function)
        cmd_show_config_info(profile=ctx.obj['PROFILE'], config_path=ctx.obj['CONFIG_PATH'])
    except ConfigurationError as e:
        logger.error(f"Error showing config info: {e}")
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error showing config info: {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR showing config info: {e}", err=True)
        sys.exit(1)
        
# === Search Documents === 
@solr_cli.command("search")
@click.option('--collection', help='Target collection name (overrides profile default).')
@click.option('--query', '-q', default='*:*', show_default=True, help='Solr query string (q parameter).')
@click.option('--filter', '-f', 'filter_query', multiple=True, help='Filter query (fq parameter). Can be used multiple times.')
@click.option('--fields', '-fl', help='Comma-separated list of fields to return (fl parameter).')
@click.option('--limit', '-l', type=int, default=10, show_default=True, help='Maximum number of documents to return (rows parameter).')
# Add format/output options if needed
@click.option('--format', type=click.Choice(['json', 'csv'], case_sensitive=False), default='json', show_default=True, help='Output format.')
@click.option('--output', type=click.Path(dir_okay=False, writable=True), help='Output file path (prints to stdout if not specified).')
@click.pass_context
def search_documents_cli(ctx: click.Context, collection: Optional[str], query: str, filter_query: Tuple[str], 
                         fields: Optional[str], limit: int, format: str, output: Optional[str]):
    """Search documents in the specified Solr collection."""
    client: SolrClient = ctx.obj['client']
    target_collection = collection if collection else ctx.obj.get('SOLR_COLLECTION')

    if not target_collection:
        click.echo("ERROR: Collection name must be provided via --collection option or profile configuration.", err=True)
        sys.exit(1)
        
    try:
        # Call the imported function directly (assuming it's refactored)
        cmd_search_documents(
            client=client,
            collection_name=target_collection,
            query=query,
            filter_query=list(filter_query), # Convert tuple
            fields=fields,
            limit=limit,
            output_format=format, # Map CLI option to function arg name
            output_path=output
        )
        logger.info(f"Search documents command executed for collection '{target_collection}'.")
    except DocumentStoreError as e:
        logger.error(f"Error searching documents in '{target_collection}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)
    except InvalidInputError as e:
        logger.error(f"Invalid input for searching documents in '{target_collection}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR: Invalid input - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error executing search command for '{target_collection}': {e}", exc_info=ctx.obj.get('DEBUG', False))
        click.echo(f"ERROR executing search command: {e}", err=True)
        sys.exit(1)

# Add other commands to the group here
solr_cli.add_command(list_collections_cli)
solr_cli.add_command(create_collection_cli)
solr_cli.add_command(delete_collection_cli)
solr_cli.add_command(collection_info_cli)
solr_cli.add_command(add_documents_cli)
solr_cli.add_command(remove_documents_cli)
solr_cli.add_command(get_documents_cli)
solr_cli.add_command(show_config_info_cli)
solr_cli.add_command(search_documents_cli)

# Main entry point (optional, if this module can be run directly)
# if __name__ == '__main__':
#     solr_cli()