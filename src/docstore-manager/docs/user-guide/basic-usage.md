# Basic Usage

This guide covers the basic usage of docstore-manager for common operations with Qdrant and Solr.

## Command Structure

docstore-manager commands follow this general structure:

```
docstore-manager <document-store> <command> [options]
```

Where:

- `<document-store>` is either `qdrant` or `solr`
- `<command>` is the operation to perform
- `[options]` are command-specific options

## Common Commands

### Listing Collections

To list all collections in a document store:

```bash
# For Qdrant
docstore-manager qdrant list

# For Solr
docstore-manager solr list
```

### Creating Collections

To create a new collection:

```bash
# For Qdrant
docstore-manager qdrant create --collection my-collection --size 1536 --distance cosine

# For Solr
docstore-manager solr create --collection my-collection
```

### Getting Collection Information

To get detailed information about a collection:

```bash
# For Qdrant
docstore-manager qdrant info --collection my-collection

# For Solr
docstore-manager solr info --collection my-collection
```

### Deleting Collections

To delete a collection:

```bash
# For Qdrant
docstore-manager qdrant delete --collection my-collection

# For Solr
docstore-manager solr delete --collection my-collection
```

## Working with Documents

### Adding Documents

To add documents to a collection:

```bash
# For Qdrant
docstore-manager qdrant add-documents --collection my-collection --file documents.json

# For Solr
docstore-manager solr add-documents --collection my-collection --file documents.json
```

### Retrieving Documents

To retrieve documents by ID:

```bash
# For Qdrant
docstore-manager qdrant get --collection my-collection --ids "1,2,3"

# For Solr
docstore-manager solr get --collection my-collection --ids "doc1,doc2,doc3"
```

### Searching Documents

To search for documents:

```bash
# For Qdrant (vector search)
docstore-manager qdrant search --collection my-collection --vector-file query_vector.json --limit 10

# For Solr (text search)
docstore-manager solr search --collection my-collection --query "title:example" --fields "id,title,score"
```

### Removing Documents

To remove documents:

```bash
# For Qdrant
docstore-manager qdrant remove-documents --collection my-collection --ids "1,2,3"

# For Solr
docstore-manager solr remove-documents --collection my-collection --ids "doc1,doc2,doc3"
```

## Using Configuration Profiles

To use a specific configuration profile:

```bash
docstore-manager --profile production qdrant list
```

## Output Formatting

docstore-manager supports different output formats:

```bash
# JSON output (default)
docstore-manager qdrant list

# YAML output
docstore-manager qdrant list --format yaml

# CSV output
docstore-manager qdrant list --format csv

# Save output to a file
docstore-manager qdrant list --format json --output collections.json
```

## Next Steps

For more advanced usage, see the [Advanced Usage](advanced-usage.md) guide.
