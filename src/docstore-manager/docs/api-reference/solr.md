# Solr API Reference

This section provides detailed API reference for the Solr module of docstore-manager.

## Client

::: docstore_manager.solr.client
    options:
      show_root_heading: true
      show_source: true

## Command

::: docstore_manager.solr.command
    options:
      show_root_heading: true
      show_source: true

## CLI

::: docstore_manager.solr.cli
    options:
      show_root_heading: true
      show_source: true

## Config

::: docstore_manager.solr.config
    options:
      show_root_heading: true
      show_source: true

## Format

::: docstore_manager.solr.format
    options:
      show_root_heading: true
      show_source: true

## Utils

::: docstore_manager.solr.utils
    options:
      show_root_heading: true
      show_source: true

## Examples

### Example 1: Basic Client Usage

```python
from docstore_manager.solr.client import SolrClient

# Initialize the client
client = SolrClient(url="http://localhost:8983/solr")
client.initialize()

# List collections
collections = client.list_collections()
print(f"Available collections: {collections}")

# Create a new collection
client.create_collection(collection_name="my_collection")

# Add documents
documents = [
    {
        "id": "doc1",
        "title": "Document 1",
        "content": "This is the content of document 1",
        "category": "example"
    },
    {
        "id": "doc2",
        "title": "Document 2",
        "content": "This is the content of document 2",
        "category": "example"
    }
]
client.add_documents("my_collection", documents)

# Search documents
search_results = client.search(
    collection_name="my_collection",
    query="content:document",
    fields=["id", "title", "score"],
    limit=5
)
print(f"Search results: {search_results}")
```

### Example 2: Using the Command Interface

```python
from docstore_manager.solr.client import SolrClient
from docstore_manager.solr.command import SolrCommand

# Initialize the client and command
client = SolrClient(url="http://localhost:8983/solr")
command = SolrCommand(client)

# List collections with additional metadata
collections_info = command.list_collections()
print(f"Collections info: {collections_info}")

# Get detailed information about a collection
collection_info = command.get_collection_info("my_collection")
print(f"Collection info: {collection_info}")

# Search with filtering and faceting
search_results = command.search_documents(
    collection_name="my_collection",
    query="title:document",
    filter_query="category:example",
    fields=["id", "title", "category", "score"],
    facet_fields=["category"],
    limit=10
)
print(f"Search results with facets: {search_results}")

# Get documents by ID
documents = command.get_documents(
    collection_name="my_collection",
    ids=["doc1", "doc2"],
    fields=["id", "title", "content", "category"]
)
print(f"Retrieved documents: {documents}")
```
