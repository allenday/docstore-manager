# docstore-manager

[![PyPI](https://img.shields.io/pypi/v/docstore-manager.svg)](https://pypi.org/project/docstore-manager/)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://allenday.github.io/docstore-manager/)
[![Tests](https://github.com/allenday/docstore-manager/workflows/tests/badge.svg)](https://github.com/allenday/docstore-manager/actions?query=workflow%3Atests)
[![License](https://img.shields.io/github/license/allenday/docstore-manager.svg)](https://github.com/allenday/docstore-manager/blob/main/LICENSE)

A general-purpose command-line tool for managing document store databases, currently supporting Qdrant vector database and Solr search platform. Simplifies common document store management tasks through a unified CLI interface.

## Table of Contents

- [Key Features](#key-features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Configuration](#configuration)
- [Examples](#examples)
- [Testing](#testing)
- [Changelog](#changelog)
- [Contributing](#contributing)
- [License](#license)

## Key Features

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
# From PyPI (recommended)
pipx install docstore-manager

# From source
git clone https://github.com/allenday/docstore-manager.git
cd docstore-manager
pipx install -e .
```

For detailed installation instructions, see the [Installation Guide](https://allenday.github.io/docstore-manager/user-guide/installation/).

## Quick Start

### Qdrant Quick Start

```bash
# Create a new collection
docstore-manager qdrant create --collection my-collection

# Add documents
docstore-manager qdrant add-documents --collection my-collection --file documents.json

# Search for similar vectors
docstore-manager qdrant search --collection my-collection --vector-file query_vector.json --limit 5
```

### Solr Quick Start

```bash
# Create a new collection
docstore-manager solr create --collection my-collection

# Add documents
docstore-manager solr add-documents --collection my-collection --file documents.json

# Search for documents
docstore-manager solr search --collection my-collection --query "title:example" --fields "id,title,score"
```

## Documentation

Comprehensive documentation is available at [https://allenday.github.io/docstore-manager/](https://allenday.github.io/docstore-manager/).

### Documentation Sections

- **[User Guide](https://allenday.github.io/docstore-manager/user-guide/basic-usage/)**: Installation, configuration, and basic usage instructions
- **[API Reference](https://allenday.github.io/docstore-manager/api-reference/)**: Detailed documentation of all modules and functions
- **[Developer Guide](https://allenday.github.io/docstore-manager/developer-guide/architecture/)**: Architecture, extension points, and contributing guidelines
- **[Examples](https://allenday.github.io/docstore-manager/examples/)**: Comprehensive usage examples for both Qdrant and Solr

## Configuration

When first run, docstore-manager will create a configuration file at:
- Linux/macOS: `~/.config/docstore-manager/config.yaml`
- Windows: `%APPDATA%\docstore-manager\config.yaml`

Example configuration:

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
```

You can switch between profiles using the `--profile` flag:

```bash
docstore-manager --profile production list
```

For detailed configuration options, see the [Configuration Guide](https://allenday.github.io/docstore-manager/user-guide/configuration/).

## Examples

### Qdrant Examples

```bash
# List all collections
docstore-manager qdrant list

# Get info about a collection
docstore-manager qdrant info --collection my-collection

# Search using vector similarity
docstore-manager qdrant search --vector-file query_vector.json --limit 10

# Batch update documents
docstore-manager qdrant batch --filter '{"key":"category","match":{"value":"product"}}' \
  --add --doc '{"processed": true}'
```

### Solr Examples

```bash
# List all collections
docstore-manager solr list

# Add documents from a file
docstore-manager solr add-documents --collection my-collection --file documents.json

# Search documents
docstore-manager solr search --collection my-collection --query "title:example" --fields "id,title,score"

# Remove documents by query
docstore-manager solr remove-documents --collection my-collection --query "category:obsolete"
```

For more examples, see the [Examples Documentation](https://allenday.github.io/docstore-manager/examples/).

## Testing

This project uses `pytest` for testing:

```bash
# Run unit tests
pytest -v

# Run integration tests (requires running services)
RUN_INTEGRATION_TESTS=true pytest -m integration -v

# Run all tests
RUN_INTEGRATION_TESTS=true pytest -v
```

## Changelog

### v0.1.1 (2025-05-04)
- Bug fixes and documentation improvements
- Updated dependency requirements
- Enhanced error handling

### v0.1.0 (2025-05-03)
- Initial release of docstore-manager
- Support for both Qdrant and Solr document stores
- Comprehensive usage examples for all operations
- Improved error handling and logging
- Standardized interfaces across document store implementations
- Configuration profiles for different environments
- Command-line interface for managing collections and documents
- Detailed documentation and API reference

For the full changelog, see the [Changelog](https://allenday.github.io/docstore-manager/changelog/).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

For development setup and guidelines, see the [Contributing Guide](https://allenday.github.io/docstore-manager/developer-guide/contributing/).

## License

Apache-2.0
