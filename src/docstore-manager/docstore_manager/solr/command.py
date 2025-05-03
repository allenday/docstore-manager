"""Solr command handler implementation."""

from typing import Any, Dict, List, Optional, Union
import json
import pysolr
import requests
import logging

from docstore_manager.core.command import DocumentStoreCommand, CommandResponse
from docstore_manager.core.exceptions import CollectionError, DocumentError
from docstore_manager.solr.client import SolrClient


class SolrCommand(DocumentStoreCommand):
    """Command handler for Solr operations."""

    def __init__(self, solr_url: str, zk_hosts: Optional[str] = None):
        """Initialize the command handler.
        
        Args:
            solr_url: Base URL for Solr instance
            zk_hosts: Optional ZooKeeper connection string for SolrCloud
        """
        self.solr_url = solr_url
        self.zk_hosts = zk_hosts
        self.admin = pysolr.SolrCoreAdmin(self.solr_url)

    def _get_core(self, name: str) -> pysolr.Solr:
        """Get a Solr core instance.
        
        Args:
            name: Name of the core/collection
            
        Returns:
            Configured Solr instance for the core
        """
        return pysolr.Solr(f"{self.solr_url}/{name}")

    def create_collection(self, name: str, **kwargs) -> CommandResponse:
        try:
            # Use Collections API
            url = f"{self.solr_url}/admin/collections"
            params = {
                'action': 'CREATE',
                'name': name,
                'numShards': kwargs.get('numShards', 1),
                'replicationFactor': kwargs.get('replicationFactor', 1),
                'collection.configName': kwargs.get('config_set', '_default'),
                'wt': 'json'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            return CommandResponse(
                success=True,
                message=f"Collection '{name}' created successfully",
                data={"name": name}
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to create collection '{name}'",
                error=str(e)
            )

    def delete_collection(self, name: str) -> CommandResponse:
        try:
            # Use Collections API to delete collection
            url = f"{self.solr_url}/admin/collections"
            params = {
                'action': 'DELETE',
                'name': name,
                'wt': 'json'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            return CommandResponse(
                success=True,
                message=f"Collection '{name}' deleted successfully"
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to delete collection '{name}'",
                error=str(e)
            )

    def list_collections(self) -> CommandResponse:
        """List all collections.
        
        Returns:
            CommandResponse with list of collection names
        """
        try:
            # Use Collections API to list collections
            url = f"{self.solr_url}/admin/collections"
            params = {
                'action': 'LIST',
                'wt': 'json'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Parse the response to extract collection names
            # The response is in the format:
            # {
            #   "responseHeader": {...},
            #   "collections": ["coll1", "coll2", ...]
            # }
            collections_data = response.json()
            collections = collections_data.get("collections", [])
            
            return CommandResponse(
                success=True,
                message="Collections retrieved successfully",
                data=collections
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message="Failed to retrieve collections",
                error=str(e)
            )

    def get_collection_info(self, name: str) -> CommandResponse:
        """Get information about a collection.
        
        Args:
            name: Name of the collection
            
        Returns:
            CommandResponse with collection information
        """
        try:
            # Use Collections API to get collection info
            url = f"{self.solr_url}/admin/collections"
            params = {
                'action': 'CLUSTERSTATUS',
                'collection': name,
                'wt': 'json'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Parse the response to extract collection info
            cluster_status = response.json()
            collections = cluster_status.get("cluster", {}).get("collections", {})
            collection_info = collections.get(name)
            
            if not collection_info:
                return CommandResponse(
                    success=False,
                    message=f"Collection '{name}' not found",
                    error="Collection not found"
                )
            
            return CommandResponse(
                success=True,
                message=f"Collection '{name}' info retrieved successfully",
                data=collection_info
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to get info for collection '{name}'",
                error=str(e)
            )

    def add_documents(self, collection: str, documents: List[Dict[str, Any]], 
                     batch_size: int = 100, commit: bool = True) -> CommandResponse:
        try:
            solr = self._get_core(collection)
            
            # Process in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                solr.add(batch)
            
            if commit:
                solr.commit()
                
            return CommandResponse(
                success=True,
                message=f"Added {len(documents)} documents to collection '{collection}'",
                data={"count": len(documents)}
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to add documents to collection '{collection}'",
                error=str(e)
            )

    def delete_documents(self, collection: str, 
                        ids: Optional[List[str]] = None,
                        query: Optional[str] = None) -> CommandResponse:
        try:
            solr = self._get_core(collection)
            
            if ids:
                # Delete by ID
                solr.delete(id=ids)
            elif query:
                # Delete by query
                solr.delete(q=query)
            else:
                return CommandResponse(
                    success=False,
                    message="Either ids or query must be provided",
                    error="Missing deletion criteria"
                )
            
            solr.commit()
            return CommandResponse(
                success=True,
                message=f"Documents deleted from collection '{collection}'"
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to delete documents from collection '{collection}'",
                error=str(e)
            )

    def get_documents(self, collection: str, 
                     ids: Optional[List[str]] = None,
                     query: Optional[str] = None,
                     fields: Optional[List[str]] = None,
                     limit: int = 10) -> CommandResponse:
        try:
            solr = self._get_core(collection)
            
            if ids:
                # Build ID query
                id_query = " OR ".join([f"id:{id}" for id in ids])
                results = solr.search(id_query, **{
                    "fl": ",".join(fields) if fields else "*",
                    "rows": limit
                })
            elif query:
                # Search by query
                results = solr.search(query, **{
                    "fl": ",".join(fields) if fields else "*",
                    "rows": limit
                })
            else:
                return CommandResponse(
                    success=False,
                    message="Either ids or query must be provided",
                    error="Missing retrieval criteria"
                )
            
            return CommandResponse(
                success=True,
                message=f"Retrieved {len(results)} documents",
                data=[dict(doc) for doc in results]
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to retrieve documents from collection '{collection}'",
                error=str(e)
            )

    def search_documents(self, collection: str, query: Dict[str, Any]) -> CommandResponse:
        """Search for documents in a collection.
        
        Args:
            collection: Collection name
            query: Query parameters
            
        Returns:
            CommandResponse with search results
        """
        try:
            solr = self._get_core(collection)
            results = solr.search(**query)
            
            # Convert results to list of dicts
            docs = [dict(doc) for doc in results]
            
            return CommandResponse(
                success=True,
                message=f"Retrieved {len(docs)} documents",
                data=docs
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to search documents in collection '{collection}'",
                error=str(e)
            )

    def get_config(self) -> CommandResponse:
        try:
            # Get system info directly from Solr admin API
            response = requests.get(f"{self.solr_url}/admin/info/system", params={"wt": "json"})
            response.raise_for_status()
            system_info = response.json()
            
            return CommandResponse(
                success=True,
                message="Configuration retrieved successfully",
                data={
                    "solr_url": self.solr_url,
                    "zk_hosts": self.zk_hosts,
                    "system_info": system_info
                }
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message="Failed to retrieve configuration",
                error=str(e)
            )

    def update_config(self, config: Dict[str, Any]) -> CommandResponse:
        # Solr configuration updates typically require manual intervention
        return CommandResponse(
            success=False,
            message="Configuration updates not supported for Solr",
            error="Operation not supported"
        ) 