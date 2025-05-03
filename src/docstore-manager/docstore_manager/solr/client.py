"""
Solr client implementation.
"""
from typing import Dict, Any, Optional, List
import pysolr
from kazoo.client import KazooClient
import logging
import requests # Add requests import
import urllib.parse # For URL joining


from docstore_manager.core.client import DocumentStoreClient # Absolute, new path
from docstore_manager.core.exceptions import ConfigurationError, ConnectionError # Absolute, new path
from docstore_manager.solr.utils import kazoo_imported # Absolute

from pysolr import Solr, SolrError

from docstore_manager.core.response import Response 
from docstore_manager.core.exceptions import (
    CollectionError,
    DocumentError,
    DocumentStoreError,
    InvalidInputError
)
# Remove the unused/missing utils import
# from docstore_manager.core.utils import validate_document_paths, load_and_validate_documents # Absolute

logger = logging.getLogger(__name__)

class SolrClient(DocumentStoreClient):
    """Client for interacting with a Solr instance."""

    def __init__(self, config: Dict[str, Any]): # Changed signature
        """Initialize the client with configuration dictionary.
        
        Args:
            config: Dictionary containing Solr connection details (e.g., url, zk_hosts, timeout).
        """
        # super().__init__(config_converter) # Removed call to base with converter
        logger.debug(f"SolrClient.__init__ received config: {config}") # DEBUG
        self.config = config
        self.client_instance = self.create_client(config) # Store the pysolr instance

    @property
    def client(self) -> pysolr.Solr: # Added property for unified access
        """Provides access to the underlying pysolr client instance."""
        if not self.client_instance:
            raise ConnectionError("Solr client is not initialized.")
        return self.client_instance
    
    def validate_config(self, config: Dict[str, Any]):
        """Validate Solr configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Either solr_url or zk_hosts is required
        if not config.get("solr_url") and not config.get("zk_hosts"):
            raise ConfigurationError("Either solr_url or zk_hosts must be provided")
    
    def _get_solr_url_via_zk(self, zk_hosts: str) -> str:
        """Connects to ZK, finds a live Solr node URL, and disconnects."""
        zk = None
        try:
            zk = KazooClient(hosts=zk_hosts)
            zk.start()
            # Get live nodes from /live_nodes
            live_nodes = zk.get_children("/live_nodes")
            if not live_nodes:
                raise ConnectionError("No live Solr nodes found in ZooKeeper")
            
            # Basic: Use the first live node. 
            # TODO: Implement better node selection (random, load balancing)
            node_path = live_nodes[0]
            node_data_bytes, _ = zk.get(f"/live_nodes/{node_path}")
            node_data = node_data_bytes.decode('utf-8')
            # Extract host and port (assuming format like host:port_solr)
            # This might need adjustment based on actual ZK data format
            solr_node_address = node_data.split('_')[0]
            return f"http://{solr_node_address}" # Construct base URL
            
        except Exception as e:
            # Catch Kazoo errors or others during ZK interaction
            # Chain the original exception using 'from e'
            raise ConnectionError(f"Failed to get Solr URL from ZooKeeper: {e}") from e
        finally:
            if zk:
                zk.stop()
                zk.close() # Ensure Kazoo client is closed

    def create_client(self, config: Dict[str, Any]) -> pysolr.Solr:
        """Create a new Solr client instance pointed at the specific collection."""
        try:
            # Get the base URL first (either from config or ZK)
            logger.debug(f"create_client: self.config BEFORE calling _get_base_solr_url: {self.config}") # DEBUG
            solr_url_base = self._get_base_solr_url()
            
            # Get the target collection for data operations
            collection = config.get('collection')
            if not collection:
                 # This should ideally be caught by init validation but check again
                 raise ConfigurationError("Target Solr collection name is missing in config.")

            # Construct final URL by joining base and collection
            # Ensure no double slashes
            final_solr_url = f"{solr_url_base.rstrip('/')}/{collection.lstrip('/')}"
            logger.debug(f"Creating pysolr.Solr instance for URL: {final_solr_url}")
                 
            timeout = config.get('timeout', 10) 

            # Create the Solr client pointed at the specific collection URL
            return pysolr.Solr(final_solr_url, timeout=timeout)
            
        except ConnectionError: # Re-raise specific connection errors
            raise
        except Exception as e:
            # Wrap other exceptions
            raise ConnectionError(f"Failed to create Solr client: {e}")
    
    def validate_connection(self, client: pysolr.Solr) -> bool:
        """Validate connection to Solr server.
        
        Args:
            client: Solr client instance to validate
            
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to ping Solr as a connection test
            client.ping()
            return True
        except Exception:
            return False
    
    def close(self, client: pysolr.Solr):
        """Close the Solr client connection.
        
        Args:
            client: Solr client instance to close
        """
        try:
            client.get_session().close()
        except Exception:
            pass  # Best effort

    # --- Implement required abstract methods --- 
    def list_collections(self) -> list[str]:
        """List Solr collections using the Collections API."""
        # Always use Collections API List action
        action = "LIST"
        api_path = "admin/collections" 
        
        base_url = self._get_base_solr_url()
        admin_url = urllib.parse.urljoin(base_url + '/', api_path)
        params = {'action': action, 'wt': 'json'}
        
        try:
            logger.debug(f"Listing collections via {api_path} action {action} at {admin_url}")
            response = self.client.get_session().get(admin_url, params=params, timeout=self.config.get('timeout', 10))
            response.raise_for_status()
            data = response.json()
            
            # Collections API LIST response: {"responseHeader":{...}, "collections":["name1", "name2"]}
            if 'collections' in data:
                return data['collections']
            else:
                raise CollectionError(f"Unexpected LIST response format: {data}")

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP Error listing Solr collections/cores: {e}")
            raise ConnectionError(f"HTTP Error listing Solr collections/cores: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error listing Solr collections/cores: {e}", exc_info=True)
            raise ConnectionError(f"Unexpected error listing Solr collections/cores: {e}") from e
            
    def create_collection(
        self,
        name: str,
        num_shards: Optional[int] = None,
        replication_factor: Optional[int] = None,
        config_name: Optional[str] = None,
    ) -> None:
        """Create a new Solr collection using the Collections API."""
        # Always use Collections API Create action
        api_path = "admin/collections"
        action = "CREATE"
        
        base_url = self._get_base_solr_url()
        admin_url = urllib.parse.urljoin(base_url + '/', api_path)
        
        params = {'action': action, 'name': name, 'wt': 'json'}
        # Add Collections API parameters
        if num_shards is not None:
            params['numShards'] = num_shards
        if replication_factor is not None:
            # Check exact param names - often replicationFactor for Collections API
            params['replicationFactor'] = replication_factor 
        if config_name is not None:
            # For Collections API, it's often collection.configName
            params['collection.configName'] = config_name
        # Add other SolrCloud specific params if needed (e.g., maxShardsPerNode)
            
        logger.info(f"Requesting {action} for collection: {name} at {admin_url}")
        logger.debug(f"API Params: {params}")

        try:
            # Use GET request for Collections API admin commands
            response = self.client.get_session().get(admin_url, params=params, timeout=self.config.get('timeout', 60)) 
            response.raise_for_status()
            data = response.json()
            
            if data.get('responseHeader', {}).get('status', -1) != 0:
                error_msg = data.get('error', {}).get('msg', f"Unknown error in Solr response: {data}")
                # Check for specific "already exists" error
                if "already exists" in error_msg.lower():
                    # Re-raise as a specific exception if needed, or handle gracefully
                     logger.warning(f"Collection '{name}' already exists (API message: {error_msg}).")
                     # Decide if this should be an error or just a warning if overwrite=False
                     # For now, let's raise CollectionError, commands/create.py handles overwrite logic
                     raise CollectionError(f"Collection '{name}' already exists.")
                else:
                    raise CollectionError(f"Failed to {action} '{name}': {error_msg}")
            
            logger.info(f"Successfully sent {action} request for '{name}'.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP Error during {action} for '{name}': {e}")
            error_detail = str(e)
            if e.response is not None:
                # Check if it was a 404 trying to delete a non-existent collection
                if e.response.status_code == 404:
                     logger.warning(f"Collection '{name}' not found during delete (HTTP 404). Treating as success.")
                     return # Exit gracefully
                try:
                    error_detail += f" | Response: {e.response.text}"
                except Exception: pass
            raise CollectionError(f"HTTP Error during {action} for '{name}': {error_detail}") from e
        except Exception as e:
            logger.error(f"Unexpected error during {action} for '{name}': {e}", exc_info=True)
            raise CollectionError(f"Unexpected error during {action} for '{name}': {e}") from e
            
    def delete_collection(self, name: str) -> None:
        """Delete a Solr collection using the Collections API."""
        # Always use Collections API Delete action
        api_path = "admin/collections"
        action = "DELETE"
        
        base_url = self._get_base_solr_url()
        admin_url = urllib.parse.urljoin(base_url + '/', api_path)
        params = {'action': action, 'name': name, 'wt': 'json'}
        
        logger.info(f"Requesting {action} for collection: {name} at {admin_url}")
        
        try:
            response = self.client.get_session().get(admin_url, params=params, timeout=self.config.get('timeout', 60))
            response.raise_for_status()
            data = response.json()
            
            if data.get('responseHeader', {}).get('status', -1) != 0:
                error_msg = data.get('error', {}).get('msg', f"Unknown error in Solr response: {data}")
                # Check for specific "does not exist" error?
                if "does not exist" in error_msg.lower():
                    logger.warning(f"Collection '{name}' not found during delete (API message: {error_msg}).")
                    # Treat as success? Or raise specific NotFound error?
                    # Let's just log warning for now, as goal is deletion.
                else:
                    raise CollectionError(f"Failed to {action} '{name}': {error_msg}")
            
            logger.info(f"Successfully sent {action} request for '{name}'.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP Error during {action} for '{name}': {e}")
            error_detail = str(e)
            if e.response is not None:
                # Check if it was a 404 trying to delete a non-existent collection
                if e.response.status_code == 404:
                     logger.warning(f"Collection '{name}' not found during delete (HTTP 404). Treating as success.")
                     return # Exit gracefully
                try:
                    error_detail += f" | Response: {e.response.text}"
                except Exception: pass
            raise CollectionError(f"HTTP Error during {action} for '{name}': {error_detail}") from e
        except Exception as e:
            logger.error(f"Unexpected error during {action} for '{name}': {e}", exc_info=True)
            raise CollectionError(f"Unexpected error during {action} for '{name}': {e}") from e

    def is_healthy(self) -> bool:
        """Check if the Solr connection is healthy by pinging."""
        try:
            self.client.ping() # Use the property
            return True
        except SolrError:
            return False
        except Exception as e:
            logger.error(f"Unexpected error during Solr health check: {e}", exc_info=True)
            return False

    def _get_base_solr_url(self) -> str:
        """Helper to get the base Solr URL (e.g., http://host:port/solr)."""
        logger.debug(f"_get_base_solr_url called. self.config is: {self.config}") # DEBUG
        if self.config.get("zk_hosts"):
            # If using ZK, discover a node URL.
            logger.debug("Attempting to get base URL via ZK.") # DEBUG
            try:
                return self._get_solr_url_via_zk(self.config["zk_hosts"]) 
            except ConnectionError as e:
                 logger.error(f"Failed to get base URL from ZK for admin task: {e}")
                 raise # Re-raise the specific connection error
        elif self.config.get("solr_url"):
            # Assume the configured URL is the base admin URL
            logger.debug(f"Using base URL from config key 'solr_url': {self.config.get('solr_url')}") # DEBUG
            return self.config["solr_url"].rstrip('/')
        else:
            # Should be caught by init validation
            logger.error("_get_base_solr_url: Could not find 'zk_hosts' or 'solr_url' in self.config") # DEBUG
            raise ConfigurationError("Cannot determine base Solr URL for admin tasks (missing url or zk_hosts).")

    # --- Data Operations ---
    
    def add_documents(
        self, 
        collection_name: str, # Included for logging/context, though client URL is collection-specific
        documents: List[Dict],
        commit: bool = True,
        batch_size: Optional[int] = None # Note: pysolr handles internal batching
    ) -> None:
        """Add or update documents in the Solr collection.
        
        Args:
            collection_name: Name of the target collection (for logging).
            documents: A list of documents (dictionaries).
            commit: Whether to perform a hard commit after adding.
            batch_size: (Currently ignored) pysolr handles its own batching.
        """
        logger.info(f"Adding/updating {len(documents)} documents in '{collection_name}'. Commit={commit}")
        
        try:
            # pysolr's add method takes a list of docs
            self.client.add(documents, commit=commit)
            logger.info(f"Successfully sent add request for {len(documents)} documents to '{collection_name}'.")
        except SolrError as e:
            logger.error(f"SolrError adding documents to '{collection_name}': {e}")
            # Attempt to parse potential error details from Solr's response if possible
            # This depends heavily on how Solr formats errors for bulk updates
            error_detail = str(e)
            # TODO: Improve error detail extraction if needed
            raise DocumentStoreError(f"SolrError adding documents: {error_detail}") from e
        except Exception as e:
            logger.error(f"Unexpected error adding documents to '{collection_name}': {e}", exc_info=True)
            raise DocumentStoreError(f"Unexpected error adding documents: {e}") from e

    def delete_documents(
        self,
        collection_name: str, # For logging/context
        ids: Optional[List[str]] = None,
        query: Optional[str] = None,
        commit: bool = True
    ) -> None:
        """Delete documents by ID or query.
        
        Args:
            collection_name: Name of the target collection (for logging).
            ids: A list of document IDs to delete.
            query: A Solr query string specifying documents to delete.
                   Exactly one of `ids` or `query` must be provided.
            commit: Whether to perform a hard commit after deleting.
        """
        if not ids and not query:
             raise ValueError("Either ids or query must be provided for deletion.")
        if ids and query:
            raise ValueError("Only one of ids or query can be provided for deletion.")
        
        target_desc = f"IDs {ids[:5]}... ({len(ids)} total)" if ids else f"query '{query}'"
        logger.info(f"Deleting documents by {target_desc} from '{collection_name}'. Commit={commit}")
        
        try:
            # pysolr's delete method handles both by ID and by query
            if ids:
                 self.client.delete(id=ids, commit=commit)
            elif query:
                 self.client.delete(q=query, commit=commit)
            
            logger.info(f"Successfully sent delete request by {target_desc} to '{collection_name}'.")
            
        except SolrError as e:
            logger.error(f"SolrError deleting documents from '{collection_name}': {e}")
            error_detail = str(e)
            # TODO: Improve error detail extraction
            raise DocumentStoreError(f"SolrError deleting documents: {error_detail}") from e
        except Exception as e:
            logger.error(f"Unexpected error deleting documents from '{collection_name}': {e}", exc_info=True)
            raise DocumentStoreError(f"Unexpected error deleting documents: {e}") from e

    def search(self, **kwargs) -> pysolr.Results:
        """Perform a search query against the Solr collection.
        
        Args:
            **kwargs: Search parameters (e.g., q, fq, fl, rows, sort, start).
                      See pysolr documentation for available parameters.
                      
        Returns:
            A pysolr.Results object containing search results.
            
        Raises:
            SolrError: If the search request fails.
        """
        # Note: collection_name is implicit in self.client URL
        logger.debug(f"Executing search with params: {kwargs}")
        try:
            # Pass parameters directly to pysolr search
            results = self.client.search(**kwargs)
            logger.debug(f"Search returned {results.hits} hits.")
            return results
        except SolrError as e:
            # Log the error and re-raise for the command layer to handle
            logger.error(f"SolrError during search: {e}")
            raise # Re-raise SolrError
        except Exception as e:
            # Catch unexpected errors during search
            logger.error(f"Unexpected error during search: {e}", exc_info=True)
            # Wrap in SolrError or a custom QueryError? Let's re-raise SolrError for now
            # to be handled by the command layer consistently.
            raise SolrError(f"Unexpected error during search: {e}") from e

# Remove the singleton instance creation at the end
# client = SolrClient() 