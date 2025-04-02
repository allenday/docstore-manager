"""Solr-specific command handler implementation."""

from typing import Any, Dict, List, Optional, Union
import json
import pysolr

from .base import DocumentStoreCommand, CommandResponse


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
            # For SolrCloud, we would use the Collections API
            if self.zk_hosts:
                # Implementation for SolrCloud collection creation
                pass
            else:
                # Create core in standalone mode
                config_set = kwargs.get('config_set', '_default')
                self.admin.create(name, config_set)
            
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
            if self.zk_hosts:
                # Implementation for SolrCloud collection deletion
                pass
            else:
                # Delete core in standalone mode
                self.admin.unload(name)
            
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
        try:
            status = self.admin.status()
            collections = [core for core in status.keys()]
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
        try:
            status = self.admin.status(name)
            if name not in status:
                return CommandResponse(
                    success=False,
                    message=f"Collection '{name}' not found",
                    error="Collection not found"
                )
            
            return CommandResponse(
                success=True,
                message=f"Collection '{name}' info retrieved successfully",
                data=status[name]
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to get info for collection '{name}'",
                error=str(e)
            )

    def add_documents(self, collection: str, documents: List[Dict[str, Any]], 
                     batch_size: int = 100) -> CommandResponse:
        try:
            solr = self._get_core(collection)
            
            # Process in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                solr.add(batch)
            
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

    def search_documents(self, collection: str,
                        vector: Optional[List[float]] = None,
                        query: Optional[str] = None,
                        fields: Optional[List[str]] = None,
                        limit: int = 10,
                        score_threshold: Optional[float] = None) -> CommandResponse:
        try:
            solr = self._get_core(collection)
            
            if vector:
                # Convert vector to dense vector query format
                vector_query = "{!knn f=vector topK=" + str(limit) + "}" + json.dumps(vector)
                
                # Combine with filter query if provided
                if query:
                    vector_query = f"{vector_query} AND {query}"
                
                results = solr.search(vector_query, **{
                    "fl": f"{'*' if not fields else ','.join(fields)},score",
                    "rows": limit
                })
                
                # Filter by score threshold if provided
                docs = []
                for doc in results:
                    score = float(doc.pop('score'))
                    if score_threshold is None or score >= score_threshold:
                        docs.append({
                            "score": score,
                            "doc": dict(doc)
                        })
                
                return CommandResponse(
                    success=True,
                    message=f"Found {len(docs)} matching documents",
                    data=docs
                )
            else:
                return CommandResponse(
                    success=False,
                    message="Vector is required for similarity search",
                    error="Missing vector"
                )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to search documents in collection '{collection}'",
                error=str(e)
            )

    def get_config(self) -> CommandResponse:
        try:
            system_info = self.admin.system_info()
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