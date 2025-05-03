# Solr Examples

This page provides examples of using docstore-manager with Apache Solr search platform.

## Basic Operations

### Listing Collections

```bash
# List all collections
docstore-manager solr list-collections

# List collections with detailed information
docstore-manager solr list-collections --detailed

# Output in JSON format
docstore-manager solr list-collections --output-format json
```

### Creating a Collection

```bash
# Create a collection with default settings
docstore-manager solr create-collection --collection-name my_collection

# Create a collection with custom settings
docstore-manager solr create-collection \
  --collection-name my_collection \
  --num-shards 2 \
  --replication-factor 2 \
  --config-set data_driven_schema_configs
```

### Getting Collection Information

```bash
# Get information about a collection
docstore-manager solr get-collection-info --collection-name my_collection

# Get information in YAML format
docstore-manager solr get-collection-info --collection-name my_collection --output-format yaml
```

### Deleting a Collection

```bash
# Delete a collection
docstore-manager solr delete-collection --collection-name my_collection

# Force delete without confirmation
docstore-manager solr delete-collection --collection-name my_collection --force
```

## Document Operations

### Adding Documents

```bash
# Add a single document from a JSON file
docstore-manager solr add-documents \
  --collection-name my_collection \
  --input-file document.json

# Add multiple documents from a JSON file
docstore-manager solr add-documents \
  --collection-name my_collection \
  --input-file documents.json

# Add documents with commit within
docstore-manager solr add-documents \
  --collection-name my_collection \
  --input-file documents.json \
  --commit-within 5000
```

### Getting Documents

```bash
# Get a document by ID
docstore-manager solr get-documents \
  --collection-name my_collection \
  --ids doc1

# Get multiple documents by ID
docstore-manager solr get-documents \
  --collection-name my_collection \
  --ids doc1 doc2 doc3

# Get documents with specific fields
docstore-manager solr get-documents \
  --collection-name my_collection \
  --ids doc1 \
  --fields title description price
```

### Removing Documents

```bash
# Remove a document by ID
docstore-manager solr remove-documents \
  --collection-name my_collection \
  --ids doc1

# Remove multiple documents by ID
docstore-manager solr remove-documents \
  --collection-name my_collection \
  --ids doc1 doc2 doc3

# Remove documents by query
docstore-manager solr remove-documents \
  --collection-name my_collection \
  --query "category:electronics"
```

### Searching Documents

```bash
# Search with a query string
docstore-manager solr search-documents \
  --collection-name my_collection \
  --query "title:smartphone"

# Search with a limit
docstore-manager solr search-documents \
  --collection-name my_collection \
  --query "title:smartphone" \
  --limit 10

# Search with field list
docstore-manager solr search-documents \
  --collection-name my_collection \
  --query "title:smartphone" \
  --fields id title price
```

### Counting Documents

```bash
# Count all documents in a collection
docstore-manager solr count-documents \
  --collection-name my_collection

# Count documents matching a query
docstore-manager solr count-documents \
  --collection-name my_collection \
  --query "category:electronics"
```

### Scrolling Through Documents

```bash
# Scroll through documents
docstore-manager solr scroll-documents \
  --collection-name my_collection \
  --limit 100

# Scroll with a query
docstore-manager solr scroll-documents \
  --collection-name my_collection \
  --limit 100 \
  --query "category:electronics"

# Continue scrolling with a cursor
docstore-manager solr scroll-documents \
  --collection-name my_collection \
  --limit 100 \
  --cursor "AoEpbWFyaw=="
```

## Advanced Examples

### Using Configuration Profiles

```bash
# Create a configuration profile
cat > ~/.config/docstore-manager/config.yaml << EOF
profiles:
  production:
    solr:
      host: production-solr.example.com
      port: 8983
      base_path: /solr
  development:
    solr:
      host: localhost
      port: 8983
      base_path: /solr
EOF

# Use a specific profile
docstore-manager solr list-collections --profile production
```

### Working with Facets

```bash
# Search with facets
docstore-manager solr search-documents \
  --collection-name my_collection \
  --query "*:*" \
  --facet-fields category brand \
  --facet-limit 10

# Search with range facets
docstore-manager solr search-documents \
  --collection-name my_collection \
  --query "*:*" \
  --facet-range price \
  --facet-range-start 0 \
  --facet-range-end 1000 \
  --facet-range-gap 100
```

### Working with Field Updates

```bash
# Add a field to all documents
docstore-manager solr add-field \
  --collection-name my_collection \
  --field-name updated_at \
  --field-value "2025-05-04T00:00:00Z" \
  --query "*:*"

# Remove a field from all documents
docstore-manager solr remove-field \
  --collection-name my_collection \
  --field-name temporary_flag \
  --query "*:*"

# Replace a field in all documents
docstore-manager solr replace-field \
  --collection-name my_collection \
  --field-name status \
  --field-value "active" \
  --query "status:pending"
```

### Batch Operations

```bash
# Batch add documents
cat documents.json | docstore-manager solr add-documents \
  --collection-name my_collection \
  --input-file -

# Export and import documents
docstore-manager solr search-documents \
  --collection-name source_collection \
  --query "*:*" \
  --limit 1000 \
  --output-file export.json

docstore-manager solr add-documents \
  --collection-name target_collection \
  --input-file export.json
```

### Schema Operations

```bash
# Add a new field to the schema
docstore-manager solr add-schema-field \
  --collection-name my_collection \
  --field-name tags \
  --field-type string \
  --multi-valued

# Get schema information
docstore-manager solr get-schema \
  --collection-name my_collection

# Get specific field information
docstore-manager solr get-schema-field \
  --collection-name my_collection \
  --field-name title
```

## Complete Example Workflow

Here's a complete workflow example for creating a collection, adding documents, searching, and cleaning up:

```bash
# Create a collection
docstore-manager solr create-collection \
  --collection-name products

# Add documents from a JSON file
docstore-manager solr add-documents \
  --collection-name products \
  --input-file products.json

# Search for products
docstore-manager solr search-documents \
  --collection-name products \
  --query "category:electronics AND price:[100 TO 500]" \
  --sort "price asc" \
  --limit 5 \
  --fields id title price category

# Get detailed information about a specific product
docstore-manager solr get-documents \
  --collection-name products \
  --ids product123

# Clean up when done
docstore-manager solr delete-collection \
  --collection-name products \
  --force
```

For more detailed examples, check the [examples directory](https://github.com/allenday/docstore-manager/tree/main/examples/solr) in the repository.
