import click
import sys
import logging
from typing import Optional
from pathlib import Path

# Now perform regular imports
from docstore_manager.core.config.base import load_config, DEFAULT_CONFIG_PATH
from docstore_manager.core.logging import setup_logging
from docstore_manager.core.exceptions import DocumentStoreError, ConfigurationError
# Import Qdrant command(s) and helpers
from docstore_manager.qdrant.cli import list_collections_cli, initialize_client as initialize_qdrant_client
# Import the rest of the Qdrant CLI commands
from docstore_manager.qdrant.cli import (
    create_collection_cli,
    delete_collection_cli,
    collection_info_cli,
    count_documents_cli,
    add_documents_cli,
    remove_documents_cli,
    scroll_documents_cli,
    get_documents_cli,
    search_documents_cli
)
# Import Solr command(s)
from docstore_manager.solr.cli import list_collections_cli as solr_list_cli, initialize_solr_command
# Import the rest of the Solr CLI commands
from docstore_manager.solr.cli import (
    create_collection_cli as solr_create_cli,
    delete_collection_cli as solr_delete_cli,
    collection_info_cli as solr_info_cli,
    add_documents_cli as solr_add_cli,
    delete_documents_cli as solr_delete_docs_cli,
    get_documents_cli as solr_get_cli,
    show_config_info_cli as solr_config_cli,
)

# Setup logger for the main CLI module
logger = setup_logging()

# Main group that orchestrates subcommands for different store types
@click.group()
@click.option('--debug', is_flag=True, default=False, help='Enable debug logging.')
@click.option(
    '--config', 'config_path', 
    type=click.Path(dir_okay=False, path_type=Path, resolve_path=True),
    default=DEFAULT_CONFIG_PATH, 
    show_default=True, 
    help='Path to configuration file.'
)
@click.option(
    '--profile', 
    default='default', 
    show_default=True, 
    help='Configuration profile name.'
)
@click.pass_context
def main(ctx, debug, config_path: Path, profile: str):
    """Document Store Manager CLI for Qdrant and Solr."""
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug
    # Store global options in context
    ctx.obj['CONFIG_PATH'] = config_path
    ctx.obj['PROFILE'] = profile

    # Setup logging level based on debug flag
    log_level = logging.DEBUG if debug else logging.INFO
    setup_logging(level=log_level) # Re-apply level if flag is set
    logger.setLevel(log_level)

    # Suppress noisy libraries if needed
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.INFO if debug else logging.WARNING)
    logging.getLogger("pysolr").setLevel(logging.INFO if debug else logging.WARNING)

# --- Qdrant Group --- 
@main.group('qdrant')
@click.pass_context
def qdrant(ctx: click.Context):
    """Commands for managing Qdrant."""
    # Retrieve global options from context
    profile = ctx.obj['PROFILE']
    config_path = ctx.obj['CONFIG_PATH']
    # Initialize client using context values
    initialize_qdrant_client(ctx, profile, config_path)
    is_debug = ctx.obj.get('DEBUG', False) # Get debug flag from context
    # Set logger level for qdrant operations specifically if needed
    logging.getLogger('docstore_manager.qdrant').setLevel(logging.DEBUG if is_debug else logging.INFO)
    
# Add Qdrant commands to the qdrant group
try:
    qdrant.add_command(list_collections_cli)
    # Add other imported qdrant commands here
    qdrant.add_command(create_collection_cli)
    qdrant.add_command(delete_collection_cli)
    qdrant.add_command(collection_info_cli)
    qdrant.add_command(count_documents_cli)
    qdrant.add_command(add_documents_cli)
    qdrant.add_command(remove_documents_cli)
    qdrant.add_command(scroll_documents_cli)
    qdrant.add_command(get_documents_cli)
    qdrant.add_command(search_documents_cli)
except NameError: # Should not happen if qdrant group is defined correctly
    logger.error("Failed to add commands to qdrant group. Group not defined?")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error adding qdrant commands: {e}", exc_info=True)
    sys.exit(1)
    
# --- Solr Group --- 
@main.group('solr')
@click.pass_context
def solr(ctx: click.Context):
    """Commands for managing Solr."""
    # Retrieve global options from context
    profile = ctx.obj['PROFILE']
    config_path = ctx.obj['CONFIG_PATH']
    # Initialize SolrCommand handler using context values
    initialize_solr_command(ctx, profile, config_path)
    is_debug = ctx.obj.get('DEBUG', False) 
    logging.getLogger('docstore_manager.solr').setLevel(logging.DEBUG if is_debug else logging.INFO)
    
# Add Solr commands to the solr group
try:
    # Add refactored Solr commands here
    solr.add_command(solr_list_cli)
    solr.add_command(solr_create_cli)
    solr.add_command(solr_delete_cli)
    solr.add_command(solr_info_cli)
    solr.add_command(solr_add_cli)
    solr.add_command(solr_delete_docs_cli)
    solr.add_command(solr_get_cli)
    solr.add_command(solr_config_cli)
except NameError:
    logger.error("Failed to add commands to solr group. Group not defined?")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error adding solr commands: {e}", exc_info=True)
    sys.exit(1)

if __name__ == "__main__":
    # Add a try-except block around the main call for better top-level error handling
    try:
        main()
    except DocumentStoreError as e:
        details_str = f" Details: {e.details}" if hasattr(e, 'details') and e.details else ""
        logger.error(f"Error: {e}{details_str}")
        click.echo(f"ERROR: {e}{details_str}", err=True)
        sys.exit(1)
    except Exception as e:
        # Log traceback only if debug is potentially enabled (check logger level)
        is_debug = logger.isEnabledFor(logging.DEBUG)
        logger.error(f"An unexpected error occurred: {e}", exc_info=is_debug)
        click.echo(f"ERROR: An unexpected error occurred: {e}", err=True)
        sys.exit(1) 