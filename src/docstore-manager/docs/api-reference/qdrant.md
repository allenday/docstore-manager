# Qdrant API Reference

This section provides detailed API reference for the Qdrant module of docstore-manager.

## Client

::: docstore_manager.qdrant.client
    options:
      show_root_heading: true
      show_source: true

## Command

::: docstore_manager.qdrant.command
    options:
      show_root_heading: true
      show_source: true

## CLI

::: docstore_manager.qdrant.cli
    options:
      show_root_heading: true
      show_source: true

## Config

::: docstore_manager.qdrant.config
    options:
      show_root_heading: true
      show_source: true

## Format

::: docstore_manager.qdrant.format
    options:
      show_root_heading: true
      show_source: true

## Utils

::: docstore_manager.qdrant.utils
    options:
      show_root_heading: true
      show_source: true

## Examples

### Example 1: Basic Client Usage

```python
from docstore_manager.qdrant.client import QdrantClient

# Initialize the client
client = QdrantClient(url="localhost", port=6333)
client.initialize()

# List collections
collections = client.list_collections()
print(f"Available collections: {collections}")

# Create a new collection
vector_params = {
    "size": 384,
    "distance": "cosine"
}
client.create_collection(
    collection_name="my_collection",
    vectors_config=vector_params
)

# Add documents
documents = [
    {
        "id": "doc1",
        "vector": [0.1, 0.2, 0.3] * 128,  # 384-dimensional vector
        "payload": {"title": "Document 1", "category": "example"}
    },
    {
        "id": "doc2",
        "vector": [0.2, 0.3, 0.4] * 128,  # 384-dimensional vector
        "payload": {"title": "Document 2", "category": "example"}
    }
]
client.add_documents("my_collection", documents)

# Search documents
query_vector = [0.15, 0.25, 0.35] * 128  # 384-dimensional vector
search_results = client.search(
    collection_name="my_collection",
    query_vector=query_vector,
    limit=5
)
print(f"Search results: {search_results}")
```

### Example 2: Using the Command Interface

```python
from docstore_manager.qdrant.client import QdrantClient
from docstore_manager.qdrant.command import QdrantCommand

# Initialize the client and command
client = QdrantClient(url="localhost", port=6333)
command = QdrantCommand(client)

# List collections with additional metadata
collections_info = command.list_collections()
print(f"Collections info: {collections_info}")

# Get detailed information about a collection
collection_info = command.get_collection_info("my_collection")
print(f"Collection info: {collection_info}")

# Search with filtering
filter_condition = {
    "must": [
        {
            "key": "category",
            "match": {"value": "example"}
        }
    ]
}
search_results = command.search_documents(
    collection_name="my_collection",
    query_vector=[0.15, 0.25, 0.35] * 128,
    filter=filter_condition,
    limit=10
)
print(f"Filtered search results: {search_results}")
```
