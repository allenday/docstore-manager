# Advanced Usage

This guide covers advanced usage of docstore-manager for more complex operations and scenarios.

## Batch Operations

docstore-manager supports batch operations for efficiently modifying multiple documents at once.

### Adding Fields to Documents

To add fields to documents matching a filter:

```bash
docstore-manager qdrant batch --collection my-collection \
  --filter '{"key":"category","match":{"value":"product"}}' \
  --add --doc '{"processed": true, "last_updated": "2025-05-04"}'
```

### Deleting Fields from Documents

To delete fields from specific documents:

```bash
docstore-manager qdrant batch --collection my-collection \
  --ids "doc1,doc2,doc3" \
  --delete --selector "metadata.temp_data"
```

### Replacing Fields in Documents

To replace fields in documents from an ID file:

```bash
docstore-manager qdrant batch --collection my-collection \
  --id-file my_ids.txt \
  --replace --selector "metadata.source" \
  --doc '{"provider": "new-provider", "date": "2025-05-04"}'
```

## Working with Filters

docstore-manager supports complex filters for targeting specific documents.

### Filter Syntax

Filters use a JSON structure to define conditions:

```json
{
  "key": "field_name",
  "match": {
    "value": "field_value"
  }
}
```

### Combining Filters

You can combine filters using logical operators:

```json
{
  "must": [
    {
      "key": "category",
      "match": {
        "value": "product"
      }
    },
    {
      "key": "price",
      "range": {
        "gt": 100,
        "lt": 200
      }
    }
  ]
}
```

### Using Filters in Commands

Filters can be used in various commands:

```bash
# Search with filter
docstore-manager qdrant search --collection my-collection \
  --vector-file query_vector.json \
  --filter '{"key":"category","match":{"value":"product"}}'

# Get documents with filter
docstore-manager qdrant get --collection my-collection \
  --filter '{"key":"status","match":{"value":"active"}}'

# Remove documents with filter
docstore-manager qdrant remove-documents --collection my-collection \
  --filter '{"key":"status","match":{"value":"deleted"}}'
```

## Working with Vectors

For Qdrant operations, you can work directly with vectors.

### Vector File Format

Vector files should be in JSON format:

```json
{
  "vector": [0.1, 0.2, 0.3, ..., 0.9]
}
```

### Searching with Vectors

To search using a vector:

```bash
docstore-manager qdrant search --collection my-collection \
  --vector-file query_vector.json \
  --limit 10 \
  --with-vectors
```

### Adding Documents with Vectors

To add documents with vectors:

```bash
docstore-manager qdrant add-documents --collection my-collection \
  --file documents_with_vectors.json
```

Where `documents_with_vectors.json` contains:

```json
[
  {
    "id": "doc1",
    "vector": [0.1, 0.2, 0.3, ..., 0.9],
    "payload": {
      "title": "Example Document",
      "content": "This is an example document."
    }
  }
]
```

## Advanced Solr Features

docstore-manager supports advanced Solr features for complex search scenarios.

### Faceted Search

To perform a faceted search:

```bash
docstore-manager solr search --collection my-collection \
  --query "*:*" \
  --facet-field "category" \
  --facet-field "author"
```

### Field Collapsing

To collapse results based on a field:

```bash
docstore-manager solr search --collection my-collection \
  --query "*:*" \
  --collapse-field "domain"
```

### Highlighting

To highlight search terms in results:

```bash
docstore-manager solr search --collection my-collection \
  --query "content:example" \
  --highlight-field "content"
```

## Scripting and Automation

docstore-manager can be used in scripts for automation.

### Exit Codes

docstore-manager returns exit codes that can be used in scripts:

- `0`: Success
- `1`: General error
- `2`: Command-line argument error
- `3`: Connection error
- `4`: Resource not found

### Scripting Example

Here's an example script that uses docstore-manager:

```bash
#!/bin/bash

# Create a collection if it doesn't exist
if ! docstore-manager qdrant info --collection my-collection &>/dev/null; then
  echo "Creating collection..."
  docstore-manager qdrant create --collection my-collection --size 1536 --distance cosine
fi

# Add documents
echo "Adding documents..."
docstore-manager qdrant add-documents --collection my-collection --file documents.json

# Search for documents
echo "Searching documents..."
docstore-manager qdrant search --collection my-collection --vector-file query_vector.json --limit 10
```

## Next Steps

For more examples, see the [Examples](../examples/qdrant.md) section.
