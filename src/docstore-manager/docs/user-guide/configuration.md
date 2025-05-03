# Configuration

This guide covers how to configure docstore-manager to connect to your document stores and customize its behavior.

## Configuration File

When first run, docstore-manager will create a configuration file at:

- Linux/macOS: `~/.config/docstore-manager/config.yaml`
- Windows: `%APPDATA%\docstore-manager\config.yaml`

You can edit this file to add your connection details and schema configuration.

## Configuration Structure

The configuration file uses YAML format and supports multiple profiles. Here's an example configuration:

```yaml
default:
  # Common settings for all document stores
  connection:
    type: qdrant  # or solr
    collection: my-collection

  # Qdrant-specific settings
  qdrant:
    url: localhost
    port: 6333
    api_key: ""
    vectors:
      size: 256
      distance: cosine
      indexing_threshold: 0
    payload_indices:
      - field: category
        type: keyword
      - field: created_at
        type: datetime
      - field: price
        type: float

  # Solr-specific settings
  solr:
    url: http://localhost:8983/solr
    username: ""
    password: ""
    schema:
      fields:
        - name: id
          type: string
        - name: title
          type: text_general
        - name: content
          type: text_general
        - name: category
          type: string
        - name: created_at
          type: pdate

production:
  connection:
    type: qdrant
    collection: production-collection

  qdrant:
    url: your-production-instance.region.cloud.qdrant.io
    port: 6333
    api_key: your-production-api-key
    vectors:
      size: 1536  # For OpenAI embeddings
      distance: cosine
      indexing_threshold: 1000
    payload_indices:
      - field: product_id
        type: keyword
      - field: timestamp
        type: datetime

  solr:
    url: https://your-production-solr.example.com/solr
    username: admin
    password: your-production-password
```

## Configuration Sections

### Common Settings

- `connection.type`: The document store type to use (`qdrant` or `solr`)
- `connection.collection`: The default collection name to use

### Qdrant Settings

- `qdrant.url`: The URL of the Qdrant server
- `qdrant.port`: The port of the Qdrant server
- `qdrant.api_key`: The API key for authentication (if required)
- `qdrant.vectors.size`: The dimension of the vectors
- `qdrant.vectors.distance`: The distance metric to use (`cosine`, `euclid`, or `dot`)
- `qdrant.vectors.indexing_threshold`: The threshold for indexing
- `qdrant.payload_indices`: The payload indices to create for optimized search

### Solr Settings

- `solr.url`: The URL of the Solr server
- `solr.username`: The username for authentication (if required)
- `solr.password`: The password for authentication (if required)
- `solr.schema.fields`: The fields to define in the schema

## Using Multiple Profiles

You can define multiple profiles in your configuration file and switch between them using the `--profile` flag:

```bash
docstore-manager --profile production qdrant list
```

This allows you to maintain separate configurations for different environments (development, testing, production).

## Command-Line Overrides

You can override any configuration setting with command-line arguments:

```bash
docstore-manager qdrant list --url localhost --port 6333 --collection my-collection
```

Command-line arguments take precedence over configuration file settings.

## Next Steps

Now that you've configured docstore-manager, you can start using it for [basic operations](basic-usage.md).
