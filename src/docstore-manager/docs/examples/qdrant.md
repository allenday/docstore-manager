# Qdrant Examples

This page provides examples of using docstore-manager with Qdrant vector database.

## Basic Operations

### Listing Collections

```bash
# List all collections
docstore-manager qdrant list-collections

# List collections with detailed information
docstore-manager qdrant list-collections --detailed

# Output in JSON format
docstore-manager qdrant list-collections --output-format json
```

### Creating a Collection

```bash
# Create a collection with default settings
docstore-manager qdrant create-collection --collection-name my_collection --vector-size 384

# Create a collection with custom settings
docstore-manager qdrant create-collection \
  --collection-name my_collection \
  --vector-size 384 \
  --distance cosine \
  --on-disk-payload \
  --hnsw-m 16 \
  --hnsw-ef-construct 100
```

### Getting Collection Information

```bash
# Get information about a collection
docstore-manager qdrant get-collection-info --collection-name my_collection

# Get information in YAML format
docstore-manager qdrant get-collection-info --collection-name my_collection --output-format yaml
```

### Deleting a Collection

```bash
# Delete a collection
docstore-manager qdrant delete-collection --collection-name my_collection

# Force delete without confirmation
docstore-manager qdrant delete-collection --collection-name my_collection --force
```

## Document Operations

### Adding Documents

```bash
# Add a single document from a JSON file
docstore-manager qdrant add-documents \
  --collection-name my_collection \
  --input-file document.json

# Add multiple documents from a JSON file
docstore-manager qdrant add-documents \
  --collection-name my_collection \
  --input-file documents.json

# Add documents with vectors
docstore-manager qdrant add-documents \
  --collection-name my_collection \
  --input-file documents_with_vectors.json \
  --vector-field embeddings
```

### Getting Documents

```bash
# Get a document by ID
docstore-manager qdrant get-documents \
  --collection-name my_collection \
  --ids doc1

# Get multiple documents by ID
docstore-manager qdrant get-documents \
  --collection-name my_collection \
  --ids doc1 doc2 doc3

# Get documents with vectors
docstore-manager qdrant get-documents \
  --collection-name my_collection \
  --ids doc1 \
  --with-vectors
```

### Removing Documents

```bash
# Remove a document by ID
docstore-manager qdrant remove-documents \
  --collection-name my_collection \
  --ids doc1

# Remove multiple documents by ID
docstore-manager qdrant remove-documents \
  --collection-name my_collection \
  --ids doc1 doc2 doc3
```

### Searching Documents

```bash
# Search by vector from a JSON file
docstore-manager qdrant search-documents \
  --collection-name my_collection \
  --vector-file query_vector.json

# Search with a limit
docstore-manager qdrant search-documents \
  --collection-name my_collection \
  --vector-file query_vector.json \
  --limit 10

# Search with a filter
docstore-manager qdrant search-documents \
  --collection-name my_collection \
  --vector-file query_vector.json \
  --filter '{"must": [{"key": "category", "match": {"value": "electronics"}}]}'
```

### Counting Documents

```bash
# Count all documents in a collection
docstore-manager qdrant count-documents \
  --collection-name my_collection

# Count documents matching a filter
docstore-manager qdrant count-documents \
  --collection-name my_collection \
  --filter '{"must": [{"key": "category", "match": {"value": "electronics"}}]}'
```

### Scrolling Through Documents

```bash
# Scroll through documents
docstore-manager qdrant scroll-documents \
  --collection-name my_collection \
  --limit 100

# Scroll with a filter
docstore-manager qdrant scroll-documents \
  --collection-name my_collection \
  --limit 100 \
  --filter '{"must": [{"key": "category", "match": {"value": "electronics"}}]}'

# Continue scrolling with a scroll ID
docstore-manager qdrant scroll-documents \
  --collection-name my_collection \
  --limit 100 \
  --scroll-id "previous_scroll_id"
```

## Advanced Examples

### Using Configuration Profiles

```bash
# Create a configuration profile
cat > ~/.config/docstore-manager/config.yaml << EOF
profiles:
  production:
    qdrant:
      host: production-qdrant.example.com
      port: 6333
  development:
    qdrant:
      host: localhost
      port: 6333
EOF

# Use a specific profile
docstore-manager qdrant list-collections --profile production
```

### Working with JSON Path Selectors

```bash
# Add a field to all documents
docstore-manager qdrant add-field \
  --collection-name my_collection \
  --field-path "metadata.updated_at" \
  --field-value "2025-05-04T00:00:00Z"

# Remove a field from all documents
docstore-manager qdrant remove-field \
  --collection-name my_collection \
  --field-path "metadata.temporary_flag"

# Replace a field in all documents
docstore-manager qdrant replace-field \
  --collection-name my_collection \
  --field-path "metadata.status" \
  --field-value "active"
```

### Batch Operations

```bash
# Batch add documents
cat documents.json | docstore-manager qdrant add-documents \
  --collection-name my_collection \
  --input-file -

# Export and import documents
docstore-manager qdrant get-documents \
  --collection-name source_collection \
  --limit 1000 \
  --output-file export.json

docstore-manager qdrant add-documents \
  --collection-name target_collection \
  --input-file export.json
```

## Complete Example Workflow

Here's a complete workflow example for creating a collection, adding documents, searching, and cleaning up:

```bash
# Create a collection
docstore-manager qdrant create-collection \
  --collection-name products \
  --vector-size 384

# Add documents from a JSON file
docstore-manager qdrant add-documents \
  --collection-name products \
  --input-file products.json

# Search for similar products
docstore-manager qdrant search-documents \
  --collection-name products \
  --vector-file query_vector.json \
  --limit 5 \
  --filter '{"must": [{"key": "in_stock", "match": {"value": true}}]}'

# Get detailed information about a specific product
docstore-manager qdrant get-documents \
  --collection-name products \
  --ids product123

# Clean up when done
docstore-manager qdrant delete-collection \
  --collection-name products \
  --force
```

For more detailed examples, check the [examples directory](https://github.com/allenday/docstore-manager/tree/main/examples/qdrant) in the repository.
