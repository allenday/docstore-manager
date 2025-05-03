# docstore-manager

A general-purpose command-line tool for managing document store databases, currently supporting Qdrant vector database and Solr search platform. Simplifies common document store management tasks through a unified CLI interface.

## Overview

docstore-manager provides a unified interface for managing different document store databases. Whether you're working with vector embeddings in Qdrant or full-text search in Solr, this tool offers a consistent experience through a simple command-line interface.

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

## Getting Started

Check out the [Installation](user-guide/installation.md) guide to get started with docstore-manager.

For a quick introduction to basic usage, see the [Basic Usage](user-guide/basic-usage.md) guide.

## Documentation Structure

- **[User Guide](user-guide/installation.md)**: Installation, configuration, and usage instructions
- **[API Reference](api-reference/core.md)**: Detailed documentation of the API
- **[Developer Guide](developer-guide/architecture.md)**: Information for developers who want to contribute
- **[Examples](examples/qdrant.md)**: Example use cases and code snippets
