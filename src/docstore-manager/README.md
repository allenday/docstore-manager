# docstore-manager

A general-purpose command-line tool for managing document store databases, currently supporting Qdrant vector database and Solr search platform. Simplifies common document store management tasks through a unified CLI interface.

## Features

- **Multi-platform Support**:
  - Qdrant vector database for similarity search and vector operations
  - Solr search platform for text search and faceted navigation
- **Collection Management**:
  - Create, delete, and list collections
  - Get detailed information about collections
- **Document Operations**:
  - Add/update documents to collections
  - Remove documents from collections
  - Retrieve documents by ID
- **Search Capabilities**:
  - Vector similarity search (Qdrant)
  - Full-text search (Solr)
  - Filtering and faceting
- **Batch Operations**:
  - Add fields to documents
  - Delete fields from documents
  - Replace fields in documents
- **Advanced Features**:
  - Support for JSON path selectors for precise document modifications
  - Multiple configuration profiles support
  - Flexible output formatting (JSON, YAML, CSV)

## Installation

```bash
# From PyPI
pipx install docstore-manager

# From source
git clone https://github.com/allenday/docstore-manager.git
cd docstore-manager
pipx install -e .
```

## Configuration

When first run, docstore-manager will create a configuration file at:
- Linux/macOS: `~/.config/docstore-manager/config.yaml`
- Windows: `%APPDATA%\docstore-manager\config.yaml`

You can edit this file to add your connection details and schema configuration:

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

Each profile can define its own:
- Connection settings for both Qdrant and Solr
- Vector configuration for Qdrant (size, distance metric, indexing behavior)
- Schema configuration for Solr
- Payload indices for optimized search performance

The YAML format makes it easy to maintain a clean, organized configuration across multiple environments.

You can switch between profiles using the `--profile` flag:

```bash
docstore-manager --profile production list
```

You can also override any setting with command-line arguments.

## Testing

This project uses `pytest` for testing. Tests are divided into two main categories:

*   **Unit Tests:** These tests verify individual components in isolation and do not require external services. They are fast and should be run frequently during development.
*   **Integration Tests:** These tests verify the interaction between the CLI tool and external services (Qdrant, Solr). They require these services to be running (e.g., via `docker-compose up -d`) and are marked with `@pytest.mark.integration`.

**Running Tests:**

*   **Run only Unit Tests (Default Behavior):**
    ```bash
    pytest -v
    ```
    *(Integration tests are skipped by default)*

*   **Run only Integration Tests:**
    ```bash
    # First, ensure Qdrant/Solr containers are running (e.g., docker-compose up -d)
    RUN_INTEGRATION_TESTS=true pytest -m integration -v
    ```
    *(Requires setting the RUN_INTEGRATION_TESTS environment variable)*

*   **Run All Tests (Unit + Integration):**
    ```bash
    # First, ensure Qdrant/Solr containers are running
    RUN_INTEGRATION_TESTS=true pytest -v
    ```

## Usage

```
docstore-manager <document-store> <command> [options]
```

### Document Stores:

- `qdrant`: Commands for Qdrant vector database
- `solr`: Commands for Solr search platform

### Available Commands:

- `list`: List all collections
- `create`: Create a new collection
- `delete`: Delete an existing collection
- `info`: Get detailed information about a collection
- `add-documents`: Add documents to a collection
- `remove-documents`: Remove documents from a collection
- `get`: Retrieve documents by ID
- `search`: Search documents in a collection
- `scroll`: Scroll through documents in a collection (Qdrant only)
- `count`: Count documents in a collection (Qdrant only)
- `config`: View available configuration profiles

### Connection Options:

```
--profile PROFILE  Configuration profile to use
--url URL          Server URL
--port PORT        Server port (Qdrant only)
--api-key API_KEY  API key (Qdrant only)
--username USER    Username (Solr only)
--password PASS    Password (Solr only)
--collection NAME  Collection name
```

### Examples:

#### Qdrant Examples:

```bash
# List all Qdrant collections
docstore-manager qdrant list

# Create a new Qdrant collection with custom settings
docstore-manager qdrant create --collection my-collection --size 1536 --distance euclid

# Get info about a Qdrant collection
docstore-manager qdrant info --collection my-collection

# Retrieve points by ID from Qdrant
docstore-manager qdrant get --ids "1,2,3" --with-vectors

# Search Qdrant using vector similarity
docstore-manager qdrant search --vector-file query_vector.json --limit 10

# Retrieve points using a filter and save as CSV
docstore-manager qdrant get --filter '{"key":"category","match":{"value":"product"}}' \
  --format csv --output results.csv

# Add a field to documents matching a filter
docstore-manager qdrant batch --filter '{"key":"category","match":{"value":"product"}}' \
  --add --doc '{"processed": true}'

# Delete a field from specific documents
docstore-manager qdrant batch --ids "doc1,doc2,doc3" --delete --selector "metadata.temp_data"

# Replace fields in documents from an ID file
docstore-manager qdrant batch --id-file my_ids.txt --replace --selector "metadata.source" \
  --doc '{"provider": "new-provider", "date": "2025-03-31"}'
```

#### Solr Examples:

```bash
# List all Solr collections
docstore-manager solr list

# Create a new Solr collection
docstore-manager solr create --collection my-collection

# Get info about a Solr collection
docstore-manager solr info --collection my-collection

# Add documents to Solr from a file
docstore-manager solr add-documents --collection my-collection --file documents.json

# Search documents in Solr
docstore-manager solr search --collection my-collection --query "title:example" --fields "id,title,score"

# Get documents by ID from Solr
docstore-manager solr get --collection my-collection --ids "doc1,doc2,doc3"

# Remove documents from Solr by query
docstore-manager solr remove-documents --collection my-collection --query "category:obsolete"
```

### Switching Between Profiles:

```bash
# Use the production profile with Qdrant
docstore-manager --profile production qdrant list

# Use the production profile with Solr
docstore-manager --profile production solr list
```

## Changelog

### v0.1.0 (2025-05-03)
- Initial release of docstore-manager
- Support for both Qdrant and Solr document stores
- Comprehensive usage examples for all operations
- Improved error handling and logging
- Standardized interfaces across document store implementations
- Configuration profiles for different environments
- Command-line interface for managing collections and documents
- Detailed documentation and API reference
- Renamed from "Qdrant Manager" to "docstore-manager"
- Consolidated CLI entry points to a single `docstore-manager` command
- Improved test coverage and reliability
- Enhanced formatting options for command outputs
- Fixed collection info formatting issues
- Fixed CLI testing context handling
- Fixed parameter validation in get_documents function
- Fixed CollectionConfig validation

## License

Apache-2.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
