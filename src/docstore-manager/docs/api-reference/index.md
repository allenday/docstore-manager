# API Reference

This section provides detailed API reference for docstore-manager.

## Modules

- [Core](core.md): Core interfaces and base classes
- [Qdrant](qdrant.md): Qdrant-specific implementation
- [Solr](solr.md): Solr-specific implementation

## Usage Examples

For usage examples, see the [Examples](../examples/index.md) section.

## Module Structure

The docstore-manager API is organized into three main modules:

### Core Module

The Core module provides the base interfaces and classes that define the common API for all document store implementations. This includes:

- **Client Interface**: Defines the common API for connecting to and interacting with document stores
- **Command Interface**: Defines the common API for high-level operations on document stores
- **Format Interface**: Defines the common API for formatting responses from document stores
- **Utilities**: Provides helper functions for document store operations

### Qdrant Module

The Qdrant module provides a concrete implementation of the Core interfaces for the Qdrant vector database. This includes:

- **Client**: Implements the Client Interface for Qdrant
- **Command**: Implements the Command Interface for Qdrant
- **CLI**: Provides a command-line interface for Qdrant operations
- **Config**: Provides classes for configuring Qdrant collections
- **Format**: Provides functions for formatting Qdrant responses
- **Utils**: Provides helper functions for Qdrant operations

### Solr Module

The Solr module provides a concrete implementation of the Core interfaces for the Solr search platform. This includes:

- **Client**: Implements the Client Interface for Solr
- **Command**: Implements the Command Interface for Solr
- **CLI**: Provides a command-line interface for Solr operations
- **Config**: Provides classes for configuring Solr collections
- **Format**: Provides functions for formatting Solr responses
- **Utils**: Provides helper functions for Solr operations
