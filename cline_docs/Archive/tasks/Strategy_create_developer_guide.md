# Task: Create Developer Guide
**Parent:** `implementation_plan_documentation_improvements.md`
**Children:** None

## Objective
Create a comprehensive developer guide for the docstore-manager project, covering architecture, contributing guidelines, development setup, and extension points, to help developers understand the codebase and contribute effectively.

## Context
The docstore-manager project has basic documentation in the form of a README, docstrings, and usage examples, but lacks a comprehensive developer guide. A well-structured developer guide will help developers understand the architecture, set up a development environment, and contribute to the project. The developer guide will be part of the MkDocs documentation site and will complement the API reference and user guide.

## Steps
1. [DONE] Create developer guide directory structure
   - Ensure the `docs/developer-guide` directory exists (created as part of the [Strategy_integrate_mkdocs](Strategy_integrate_mkdocs.md) task)
   - Create the following files in the `docs/developer-guide` directory:
     - `index.md`: Overview of the developer guide
     - `architecture.md`: Architecture overview
     - `contributing.md`: Contributing guidelines
     - `development-setup.md`: Development setup instructions
     - `extension-points.md`: Extension points documentation

2. [DONE] Create the developer guide index page
   - Edit `docs/developer-guide/index.md` with the following content:
     ```markdown
     # Developer Guide

     This developer guide provides comprehensive information for developers who want to understand the docstore-manager codebase and contribute to the project.

     ## Sections

     - [Architecture](architecture.md): Overview of the docstore-manager architecture
     - [Contributing](contributing.md): Guidelines for contributing to the project
     - [Development Setup](development-setup.md): How to set up a development environment
     - [Extension Points](extension-points.md): How to extend docstore-manager

     ## Getting Help

     If you encounter any issues or have questions, please [open an issue](https://github.com/allenday/docstore-manager/issues) on GitHub.
     ```

3. Create the architecture overview
   - Edit `docs/developer-guide/architecture.md` with the following content:
     ```markdown
     # Architecture

     This document provides an overview of the docstore-manager architecture.

     ## High-Level Architecture

     docstore-manager is designed with a modular architecture that separates concerns and allows for easy extension. The main components are:

     - **Core**: Defines interfaces and base classes for document store operations
     - **Qdrant**: Implements the core interfaces for Qdrant vector database
     - **Solr**: Implements the core interfaces for Solr search platform
     - **CLI**: Provides a command-line interface for interacting with document stores

     ```mermaid
     graph TD
         A[CLI] --> B[Core]
         A --> C[Qdrant]
         A --> D[Solr]
         C --> B
         D --> B
         C --> E[Qdrant API]
         D --> F[Solr API]
     ```

     ## Core Module

     The Core module defines interfaces and base classes that are implemented by the Qdrant and Solr modules. This ensures a consistent API across different document stores.

     ### Key Interfaces

     - **ClientInterface**: Defines methods for connecting to a document store
     - **CommandInterface**: Defines methods for executing commands on a document store
     - **FormatterInterface**: Defines methods for formatting command results

     ## Qdrant Module

     The Qdrant module implements the core interfaces for the Qdrant vector database.

     ### Key Components

     - **QdrantClient**: Implements ClientInterface for Qdrant
     - **QdrantCommand**: Implements CommandInterface for Qdrant
     - **QdrantFormatter**: Implements FormatterInterface for Qdrant

     ## Solr Module

     The Solr module implements the core interfaces for the Solr search platform.

     ### Key Components

     - **SolrClient**: Implements ClientInterface for Solr
     - **SolrCommand**: Implements CommandInterface for Solr
     - **SolrFormatter**: Implements FormatterInterface for Solr

     ## CLI Module

     The CLI module provides a command-line interface for interacting with document stores. It uses Click to define commands and options.

     ### Command Structure

     The CLI follows a hierarchical command structure:

     ```
     docstore-manager
     ├── qdrant
     │   ├── list
     │   ├── create
     │   ├── delete
     │   ├── info
     │   ├── add-documents
     │   ├── remove-documents
     │   ├── get
     │   ├── search
     │   ├── scroll
     │   ├── count
     │   └── batch
     └── solr
         ├── list
         ├── create
         ├── delete
         ├── info
         ├── add-documents
         ├── remove-documents
         ├── get
         └── search
     ```

     ## Data Flow

     The following diagram illustrates the data flow for a typical command:

     ```mermaid
     sequenceDiagram
         participant User
         participant CLI
         participant Command
         participant Client
         participant Formatter
         participant DocumentStore

         User->>CLI: Execute command
         CLI->>Command: Create command
         Command->>Client: Initialize client
         Command->>DocumentStore: Execute operation
         DocumentStore-->>Command: Return result
         Command->>Formatter: Format result
         Formatter-->>Command: Return formatted result
         Command-->>CLI: Return formatted result
         CLI-->>User: Display result
     ```

     ## Configuration

     docstore-manager uses a YAML configuration file to store connection details and schema configuration. The configuration is loaded by the CLI and passed to the appropriate client.

     ## Error Handling

     docstore-manager uses a consistent error handling approach:

     - **CLI**: Catches exceptions and displays user-friendly error messages
     - **Command**: Raises exceptions with detailed error information
     - **Client**: Raises exceptions for API errors and connection issues
     ```

4. Create the contributing guidelines
   - Edit `docs/developer-guide/contributing.md` with the following content:
     ```markdown
     # Contributing

     This document provides guidelines for contributing to the docstore-manager project.

     ## Code of Conduct

     Please be respectful and considerate of others when contributing to the project. We strive to maintain a welcoming and inclusive community.

     ## Getting Started

     1. Fork the repository on GitHub
     2. Clone your fork locally
     3. Set up a development environment as described in the [Development Setup](development-setup.md) guide
     4. Create a branch for your changes
     5. Make your changes
     6. Run tests to ensure your changes don't break existing functionality
     7. Submit a pull request

     ## Pull Request Process

     1. Ensure your code follows the project's coding style
     2. Add tests for any new functionality
     3. Update documentation to reflect your changes
     4. Ensure all tests pass
     5. Submit a pull request with a clear description of the changes

     ## Coding Style

     docstore-manager follows the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code. We use [flake8](https://flake8.pycqa.org/) and [black](https://black.readthedocs.io/) to enforce coding style.

     ## Testing

     docstore-manager uses [pytest](https://pytest.org/) for testing. All new code should include tests. To run tests:

     ```bash
     # Run unit tests
     pytest

     # Run integration tests (requires running Qdrant and Solr instances)
     RUN_INTEGRATION_TESTS=true pytest tests/integration/
     ```

     ## Documentation

     All new code should include docstrings following the [Google docstring format](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings). Example:

     ```python
     def add_documents(collection_name, documents, batch_size=100):
         """Add documents to a collection.

         Args:
             collection_name (str): The name of the collection.
             documents (list): A list of documents to add.
             batch_size (int, optional): The batch size for adding documents.
                 Defaults to 100.

         Returns:
             dict: A dictionary containing the operation result.

         Raises:
             ValueError: If collection_name is empty or documents is empty.
             ClientError: If the client fails to add documents.

         Examples:
             >>> add_documents("my-collection", [{"id": "1", "text": "example"}])
             {'status': 'success', 'count': 1}
         """
     ```

     ## Commit Messages

     Write clear and concise commit messages that explain the changes you've made. Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

     ```
     <type>(<scope>): <description>

     [optional body]

     [optional footer]
     ```

     Types:
     - `feat`: A new feature
     - `fix`: A bug fix
     - `docs`: Documentation changes
     - `style`: Changes that do not affect the meaning of the code (formatting, etc.)
     - `refactor`: Code changes that neither fix a bug nor add a feature
     - `perf`: Code changes that improve performance
     - `test`: Adding or modifying tests
     - `chore`: Changes to the build process or auxiliary tools

     Examples:
     - `feat(qdrant): add support for hybrid search`
     - `fix(solr): handle empty response from server`
     - `docs: update README with new examples`

     ## Versioning

     docstore-manager follows [Semantic Versioning](https://semver.org/). Version numbers are in the format MAJOR.MINOR.PATCH:

     - MAJOR: Incompatible API changes
     - MINOR: Add functionality in a backwards-compatible manner
     - PATCH: Backwards-compatible bug fixes

     ## Release Process

     1. Update version number in:
        - `pyproject.toml`
        - `setup.py`
        - `docstore_manager/__init__.py`
     2. Update `CHANGELOG.md` with the changes in the new version
     3. Create a git tag for the new version
     4. Push the tag to GitHub
     5. Build and upload the package to PyPI
     ```

5. Create the development setup instructions
   - Edit `docs/developer-guide/development-setup.md` with the following content:
     ```markdown
     # Development Setup

     This document provides instructions for setting up a development environment for docstore-manager.

     ## Prerequisites

     - Python 3.8 or later
     - pip (Python package installer)
     - git
     - Docker and Docker Compose (for running Qdrant and Solr locally)

     ## Clone the Repository

     ```bash
     git clone https://github.com/allenday/docstore-manager.git
     cd docstore-manager
     ```

     ## Create a Virtual Environment

     ```bash
     # Using venv
     python -m venv .venv
     source .venv/bin/activate  # On Windows: .venv\Scripts\activate

     # Or using conda
     conda create -n docstore-manager python=3.8
     conda activate docstore-manager
     ```

     ## Install Dependencies

     ```bash
     # Install development dependencies
     pip install -e ".[dev]"
     ```

     ## Start Qdrant and Solr

     For development and testing, you can use Docker Compose to start Qdrant and Solr:

     ```bash
     docker-compose up -d
     ```

     This will start:
     - Qdrant on http://localhost:6333
     - Solr on http://localhost:8983

     ## Run Tests

     ```bash
     # Run unit tests
     pytest

     # Run integration tests (requires running Qdrant and Solr instances)
     RUN_INTEGRATION_TESTS=true pytest tests/integration/
     ```

     ## Code Formatting

     docstore-manager uses [black](https://black.readthedocs.io/) for code formatting and [flake8](https://flake8.pycqa.org/) for linting:

     ```bash
     # Format code
     black .

     # Check code style
     flake8
     ```

     ## Pre-commit Hooks

     docstore-manager uses [pre-commit](https://pre-commit.com/) to run checks before each commit:

     ```bash
     # Install pre-commit hooks
     pre-commit install

     # Run pre-commit hooks manually
     pre-commit run --all-files
     ```

     ## Building Documentation

     docstore-manager uses [MkDocs](https://www.mkdocs.org/) with the [Material theme](https://squidfunk.github.io/mkdocs-material/) for documentation:

     ```bash
     # Install documentation dependencies
     pip install -e ".[docs]"

     # Serve documentation locally
     mkdocs serve

     # Build documentation
     mkdocs build
     ```

     ## Building the Package

     ```bash
     # Install build dependencies
     pip install build

     # Build the package
     python -m build
     ```

     ## Running the CLI

     During development, you can run the CLI directly:

     ```bash
     # Run the CLI
     python -m docstore_manager.cli qdrant list

     # Or use the entry point
     docstore-manager qdrant list
     ```
     ```

6. Create the extension points documentation
   - Edit `docs/developer-guide/extension-points.md` with the following content:
     ```markdown
     # Extension Points

     This document describes how to extend docstore-manager with new functionality.

     ## Adding a New Document Store

     docstore-manager is designed to be extensible with new document store implementations. To add a new document store:

     1. Create a new module in the `docstore_manager` package
     2. Implement the core interfaces:
        - `ClientInterface`
        - `CommandInterface`
        - `FormatterInterface`
     3. Add CLI commands for the new document store

     ### Example: Adding a New Document Store

     Here's an example of how to add a new document store called "NewStore":

     ```python
     # docstore_manager/newstore/client.py
     from docstore_manager.core.client_interface import ClientInterface

     class NewStoreClient(ClientInterface):
         def __init__(self, url, **kwargs):
             self.url = url
             self.kwargs = kwargs

         def initialize(self):
             # Initialize the client
             pass

         def list_collections(self):
             # List collections
             pass

         def create_collection(self, collection_name, **kwargs):
             # Create a collection
             pass

         def delete_collection(self, collection_name):
             # Delete a collection
             pass

         def get_collection_info(self, collection_name):
             # Get collection info
             pass

         def add_documents(self, collection_name, documents, **kwargs):
             # Add documents
             pass

         def remove_documents(self, collection_name, ids=None, filter=None):
             # Remove documents
             pass

         def get_documents(self, collection_name, ids=None, filter=None, **kwargs):
             # Get documents
             pass

         def search(self, collection_name, query=None, filter=None, **kwargs):
             # Search documents
             pass
     ```

     ```python
     # docstore_manager/newstore/command.py
     from docstore_manager.core.command_interface import CommandInterface
     from docstore_manager.newstore.client import NewStoreClient
     from docstore_manager.newstore.format import NewStoreFormatter

     class NewStoreCommand(CommandInterface):
         def __init__(self, config=None):
             self.config = config or {}
             self.client = None
             self.formatter = NewStoreFormatter()

         def initialize_client(self, **kwargs):
             # Initialize the client
             self.client = NewStoreClient(**kwargs)
             self.client.initialize()
             return self.client

         def list_collections(self, **kwargs):
             # List collections
             result = self.client.list_collections()
             return self.formatter.format_collections(result)

         def create_collection(self, collection_name, **kwargs):
             # Create a collection
             result = self.client.create_collection(collection_name, **kwargs)
             return self.formatter.format_create_result(result)

         def delete_collection(self, collection_name):
             # Delete a collection
             result = self.client.delete_collection(collection_name)
             return self.formatter.format_delete_result(result)

         def get_collection_info(self, collection_name):
             # Get collection info
             result = self.client.get_collection_info(collection_name)
             return self.formatter.format_collection_info(result)

         def add_documents(self, collection_name, documents, **kwargs):
             # Add documents
             result = self.client.add_documents(collection_name, documents, **kwargs)
             return self.formatter.format_add_result(result)

         def remove_documents(self, collection_name, ids=None, filter=None):
             # Remove documents
             result = self.client.remove_documents(collection_name, ids, filter)
             return self.formatter.format_remove_result(result)

         def get_documents(self, collection_name, ids=None, filter=None, **kwargs):
             # Get documents
             result = self.client.get_documents(collection_name, ids, filter, **kwargs)
             return self.formatter.format_documents(result)

         def search(self, collection_name, query=None, filter=None, **kwargs):
             # Search documents
             result = self.client.search(collection_name, query, filter, **kwargs)
             return self.formatter.format_search_result(result)
     ```

     ```python
     # docstore_manager/newstore/format.py
     from docstore_manager.core.format.formatter_interface import FormatterInterface

     class NewStoreFormatter(FormatterInterface):
         def format_collections(self, collections):
             # Format collections
             pass

         def format_create_result(self, result):
             # Format create result
             pass

         def format_delete_result(self, result):
             # Format delete result
             pass

         def format_collection_info(self, info):
             # Format collection info
             pass

         def format_add_result(self, result):
             # Format add result
             pass

         def format_remove_result(self, result):
             # Format remove result
             pass

         def format_documents(self, documents):
             # Format documents
             pass

         def format_search_result(self, result):
             # Format search result
             pass
     ```

     ```python
     # docstore_manager/newstore/cli.py
     import click
     from docstore_manager.newstore.command import NewStoreCommand

     @click.group()
     @click.pass_context
     def newstore(ctx):
         """Commands for NewStore document store."""
         ctx.obj = NewStoreCommand()

     @newstore.command()
     @click.pass_obj
     def list(cmd):
         """List all collections."""
         cmd.initialize_client()
         result = cmd.list_collections()
         click.echo(result)

     @newstore.command()
     @click.option("--collection", required=True, help="Collection name")
     @click.pass_obj
     def create(cmd, collection):
         """Create a new collection."""
         cmd.initialize_client()
         result = cmd.create_collection(collection)
         click.echo(result)

     # Add more commands...
     ```

     ```python
     # docstore_manager/cli.py
     import click
     from docstore_manager.qdrant.cli import qdrant
     from docstore_manager.solr.cli import solr
     from docstore_manager.newstore.cli import newstore

     @click.group()
     def cli():
         """docstore-manager CLI."""
         pass

     cli.add_command(qdrant)
     cli.add_command(solr)
     cli.add_command(newstore)  # Add the new document store

     if __name__ == "__main__":
         cli()
     ```

     ## Adding a New Command

     To add a new command to an existing document store:

     1. Add the command to the client implementation
     2. Add the command to the command implementation
     3. Add the command to the CLI

     ### Example: Adding a New Command

     Here's an example of how to add a new command called "export" to the Qdrant document store:

     ```python
     # docstore_manager/qdrant/client.py
     def export_collection(self, collection_name, file_path):
         # Export collection
         pass
     ```

     ```python
     # docstore_manager/qdrant/command.py
     def export_collection(self, collection_name, file_path):
         # Export collection
         result = self.client.export_collection(collection_name, file_path)
         return self.formatter.format_export_result(result)
     ```

     ```python
     # docstore_manager/qdrant/format.py
     def format_export_result(self, result):
         # Format export result
         pass
     ```

     ```python
     # docstore_manager/qdrant/cli.py
     @qdrant.command()
     @click.option("--collection", required=True, help="Collection name")
     @click.option("--file", required=True, help="File path")
     @click.pass_obj
     def export(cmd, collection, file):
         """Export a collection to a file."""
         cmd.initialize_client()
         result = cmd.export_collection(collection, file)
         click.echo(result)
     ```

     ## Adding a New Formatter

     To add a new formatter:

     1. Create a new formatter class that implements `FormatterInterface`
     2. Add the formatter to the command implementation

     ### Example: Adding a New Formatter

     Here's an example of how to add a new formatter called "XML" to the Qdrant document store:

     ```python
     # docstore_manager/qdrant/format_xml.py
     from docstore_manager.core.format.formatter_interface import FormatterInterface
     import xml.etree.ElementTree as ET

     class QdrantXmlFormatter(FormatterInterface):
         def format_collections(self, collections):
             # Format collections as XML
             root = ET.Element("collections")
             for collection in collections:
                 ET.SubElement(root, "collection", name=collection)
             return ET.tostring(root, encoding="unicode")

         # Implement other methods...
     ```

     ```python
     # docstore_manager/qdrant/command.py
     from docstore_manager.qdrant.format_xml import QdrantXmlFormatter

     def initialize_client(self, format="json", **kwargs):
         # Initialize the client
         self.client = QdrantClient(**kwargs)
         self.client.initialize()

         # Set formatter based on format
         if format == "xml":
             self.formatter = QdrantXmlFormatter()
         else:
             self.formatter = QdrantFormatter()

         return self.client
     ```

     ```python
     # docstore_manager/qdrant/cli.py
     @qdrant.command()
     @click.option("--format", default="json", help="Output format (json, yaml, csv, xml)")
     @click.pass_obj
     def list(cmd, format):
         """List all collections."""
         cmd.initialize_client(format=format)
         result = cmd.list_collections()
         click.echo(result)
     ```
     ```

7. [DONE] Update the mkdocs.yml navigation
   - Ensure the developer guide pages are properly included in the navigation
   - Update the `nav` section in `mkdocs.yml` to include the developer guide index page:
     ```yaml
     nav:
       # ... existing navigation ...
       - Developer Guide:
         - Overview: developer-guide/index.md
         - Architecture: developer-guide/architecture.md
         - Contributing: developer-guide/contributing.md
         - Development Setup: developer-guide/development-setup.md
         - Extension Points: developer-guide/extension-points.md
       # ... rest of navigation ...
     ```

8. [DONE] Test the developer guide
   - Run `mkdocs serve` to start a local server
   - Navigate to the developer guide pages in the browser
   - Verify that all pages are accessible and properly formatted
   - Check that all links work correctly
   - Ensure that code examples are properly highlighted
   - Verify that the Mermaid diagrams render correctly

9. [DONE] Add a link to the developer guide in the README
   - Add a section to the README.md that points to the developer guide
   - For example:
     ```markdown
     ## Contributing

     For information on how to contribute to the project, see the [Developer Guide](https://allenday.github.io/docstore-manager/developer-guide/).
     ```

## Dependencies
- Requires: [Strategy_integrate_mkdocs]
- Blocks: None

## Expected Output
- A comprehensive developer guide covering architecture, contributing guidelines, development setup, and extension points
- Developer guide organized into clear sections with examples and diagrams
- Developer guide accessible through the MkDocs site
- Link to the developer guide in the README
