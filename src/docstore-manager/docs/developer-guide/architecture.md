# Architecture

This page provides an overview of the docstore-manager architecture.

## Overview

docstore-manager is designed with a modular architecture that separates concerns and allows for easy extension to support additional document stores.

## Core Components

The architecture consists of the following core components:

### Client Interface

The client interface (`ClientInterface`) defines the common API for all document store clients. It provides methods for connecting to and interacting with document stores.

### Command Interface

The command interface (`CommandInterface`) defines the common API for all document store commands. It provides high-level operations that are implemented by specific document store commands.

### CLI Interface

The CLI interface provides a command-line interface for interacting with document stores. It uses Click to define commands and options.

### Formatter Interface

The formatter interface defines the common API for formatting responses from document stores. It provides methods for converting document store responses to various formats (JSON, YAML, CSV).

## Document Store Implementations

docstore-manager currently supports the following document stores:

### Qdrant

The Qdrant implementation provides classes and functions for interacting with Qdrant vector database. It includes:

- `QdrantClient`: Implements the client interface for Qdrant
- `QdrantCommand`: Implements the command interface for Qdrant
- `QdrantCLI`: Provides CLI commands for Qdrant
- `QdrantFormatter`: Formats Qdrant responses

### Solr

The Solr implementation provides classes and functions for interacting with Solr search platform. It includes:

- `SolrClient`: Implements the client interface for Solr
- `SolrCommand`: Implements the command interface for Solr
- `SolrCLI`: Provides CLI commands for Solr
- `SolrFormatter`: Formats Solr responses

## Configuration

docstore-manager uses a YAML configuration file to store connection details and other settings. The configuration is loaded at runtime and can be overridden with command-line arguments.

## Extension Points

docstore-manager is designed to be extensible. To add support for a new document store, you need to implement the following:

1. A client that implements the `ClientInterface`
2. A command that implements the `CommandInterface`
3. A CLI module that provides Click commands
4. A formatter that formats responses

See the [Extension Points](extension-points.md) page for more details.

## Dependency Diagram

```
docstore-manager
├── core
│   ├── client_interface.py
│   ├── command_interface.py
│   └── utils.py
├── qdrant
│   ├── client.py
│   ├── command.py
│   ├── cli.py
│   ├── config.py
│   ├── format.py
│   └── utils.py
├── solr
│   ├── client.py
│   ├── command.py
│   ├── cli.py
│   ├── config.py
│   ├── format.py
│   └── utils.py
└── cli.py
```
