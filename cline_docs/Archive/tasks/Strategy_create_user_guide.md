# Task: Create User Guide [DONE]
**Parent:** `implementation_plan_documentation_improvements.md`
**Children:** None
**Status:** Completed on 2025-05-04

## Objective
Create a comprehensive user guide for the docstore-manager project, covering installation, configuration, basic usage, and advanced usage, to help users get started and make the most of the tool.

## Context
The docstore-manager project has basic documentation in the form of a README, docstrings, and usage examples, but lacks a comprehensive user guide. A well-structured user guide will help users understand how to install, configure, and use the tool effectively. The user guide will be part of the MkDocs documentation site and will complement the API reference and developer guide.

## Steps
1. [DONE] Create user guide directory structure
   - Ensure the `docs/user-guide` directory exists (created as part of the [Strategy_integrate_mkdocs](Strategy_integrate_mkdocs.md) task)
   - Create the following files in the `docs/user-guide` directory:
     - `index.md`: Overview of the user guide
     - `installation.md`: Installation instructions
     - `configuration.md`: Configuration guide
     - `basic-usage.md`: Basic usage guide
     - `advanced-usage.md`: Advanced usage guide

2. [DONE] Create the user guide index page
   - Edit `docs/user-guide/index.md` with the following content:
     ```markdown
     # User Guide

     This user guide provides comprehensive information on how to install, configure, and use docstore-manager.

     ## Sections

     - [Installation](installation.md): How to install docstore-manager
     - [Configuration](configuration.md): How to configure docstore-manager
     - [Basic Usage](basic-usage.md): Basic usage examples
     - [Advanced Usage](advanced-usage.md): Advanced usage examples

     ## Getting Help

     If you encounter any issues or have questions, please [open an issue](https://github.com/allenday/docstore-manager/issues) on GitHub.
     ```

3. [DONE] Create the installation guide (already existed)
   - Edit `docs/user-guide/installation.md` with the following content:
     ```markdown
     # Installation

     This guide covers how to install docstore-manager.

     ## Prerequisites

     - Python 3.8 or later
     - pip (Python package installer)

     ## Installing from PyPI

     The recommended way to install docstore-manager is from PyPI:

     ```bash
     pip install docstore-manager
     ```

     For a more isolated installation, you can use [pipx](https://pypa.github.io/pipx/):

     ```bash
     pipx install docstore-manager
     ```

     ## Installing from Source

     To install from source:

     ```bash
     git clone https://github.com/allenday/docstore-manager.git
     cd docstore-manager
     pip install -e .
     ```

     ## Verifying Installation

     To verify that docstore-manager is installed correctly, run:

     ```bash
     docstore-manager --version
     ```

     This should display the version number of docstore-manager.

     ## Installing Optional Dependencies

     docstore-manager has optional dependencies for specific features:

     - For Qdrant support: `pip install docstore-manager[qdrant]`
     - For Solr support: `pip install docstore-manager[solr]`
     - For all features: `pip install docstore-manager[all]`

     ## Upgrading

     To upgrade to the latest version:

     ```bash
     pip install --upgrade docstore-manager
     ```
     ```

4. [DONE] Create the configuration guide (already existed)
   - Edit `docs/user-guide/configuration.md` with the following content:
     ```markdown
     # Configuration

     This guide covers how to configure docstore-manager.

     ## Configuration File

     docstore-manager uses a YAML configuration file to store connection details and schema configuration. When first run, docstore-manager will create a configuration file at:

     - Linux/macOS: `~/.config/docstore-manager/config.yaml`
     - Windows: `%APPDATA%\docstore-manager\config.yaml`

     You can specify a different configuration file using the `--config` option:

     ```bash
     docstore-manager --config /path/to/config.yaml qdrant list
     ```

     ## Configuration Profiles

     The configuration file supports multiple profiles, allowing you to define different settings for different environments (e.g., development, production).

     Each profile can define its own:
     - Connection settings for both Qdrant and Solr
     - Vector configuration for Qdrant (size, distance metric, indexing behavior)
     - Schema configuration for Solr
     - Payload indices for optimized search performance

     ### Example Configuration

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

     ## Switching Between Profiles

     You can switch between profiles using the `--profile` flag:

     ```bash
     docstore-manager --profile production qdrant list
     ```

     ## Command-Line Overrides

     You can override any configuration setting with command-line arguments:

     ```bash
     docstore-manager qdrant list --url localhost --port 6333 --api-key my-api-key
     ```

     ## Environment Variables

     You can also use environment variables to override configuration settings:

     ```bash
     DOCSTORE_MANAGER_QDRANT_API_KEY=my-api-key docstore-manager qdrant list
     ```

     Environment variables should be prefixed with `DOCSTORE_MANAGER_` and use uppercase with underscores.
     ```

5. [DONE] Create the basic usage guide (already existed)
   - Edit `docs/user-guide/basic-usage.md` with the following content:
     ```markdown
     # Basic Usage

     This guide covers the basic usage of docstore-manager.

     ## Command Structure

     docstore-manager commands follow this structure:

     ```
     docstore-manager <document-store> <command> [options]
     ```

     Where:
     - `<document-store>` is either `qdrant` or `solr`
     - `<command>` is the operation to perform (e.g., `list`, `create`, `delete`)
     - `[options]` are command-specific options

     ## Common Commands

     ### Listing Collections

     To list all collections:

     ```bash
     # For Qdrant
     docstore-manager qdrant list

     # For Solr
     docstore-manager solr list
     ```

     ### Creating a Collection

     To create a new collection:

     ```bash
     # For Qdrant
     docstore-manager qdrant create --collection my-collection --size 1536 --distance cosine

     # For Solr
     docstore-manager solr create --collection my-collection
     ```

     ### Getting Collection Information

     To get information about a collection:

     ```bash
     # For Qdrant
     docstore-manager qdrant info --collection my-collection

     # For Solr
     docstore-manager solr info --collection my-collection
     ```

     ### Deleting a Collection

     To delete a collection:

     ```bash
     # For Qdrant
     docstore-manager qdrant delete --collection my-collection

     # For Solr
     docstore-manager solr delete --collection my-collection
     ```

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
     docstore-manager solr get --collection my-collection --ids "1,2,3"
     ```

     ### Searching Documents

     To search for documents:

     ```bash
     # For Qdrant (vector search)
     docstore-manager qdrant search --collection my-collection --vector-file query_vector.json

     # For Solr (text search)
     docstore-manager solr search --collection my-collection --query "title:example"
     ```

     ## Output Formatting

     You can control the output format using the `--format` option:

     ```bash
     docstore-manager qdrant list --format json
     ```

     Supported formats:
     - `json` (default): JSON output
     - `yaml`: YAML output
     - `csv`: CSV output (for tabular data)

     You can also save the output to a file using the `--output` option:

     ```bash
     docstore-manager qdrant list --format json --output collections.json
     ```
     ```

6. [DONE] Create the advanced usage guide (already existed)
   - Edit `docs/user-guide/advanced-usage.md` with the following content:
     ```markdown
     # Advanced Usage

     This guide covers advanced usage of docstore-manager.

     ## Filtering

     You can filter documents using the `--filter` option:

     ```bash
     # For Qdrant
     docstore-manager qdrant get --collection my-collection --filter '{"key":"category","match":{"value":"product"}}'

     # For Solr
     docstore-manager solr search --collection my-collection --filter 'category:product'
     ```

     ## Batch Operations

     docstore-manager supports batch operations for modifying multiple documents at once.

     ### Adding Fields

     To add fields to documents matching a filter:

     ```bash
     docstore-manager qdrant batch --collection my-collection --filter '{"key":"category","match":{"value":"product"}}' --add --doc '{"processed": true}'
     ```

     ### Deleting Fields

     To delete fields from specific documents:

     ```bash
     docstore-manager qdrant batch --collection my-collection --ids "doc1,doc2,doc3" --delete --selector "metadata.temp_data"
     ```

     ### Replacing Fields

     To replace fields in documents from an ID file:

     ```bash
     docstore-manager qdrant batch --collection my-collection --id-file my_ids.txt --replace --selector "metadata.source" --doc '{"provider": "new-provider", "date": "2025-03-31"}'
     ```

     ## JSON Path Selectors

     docstore-manager supports JSON path selectors for precise document modifications:

     ```bash
     docstore-manager qdrant batch --collection my-collection --ids "doc1,doc2,doc3" --replace --selector "metadata.nested.field" --doc '{"value": 42}'
     ```

     ## Pagination

     For large result sets, you can use pagination:

     ```bash
     # For Qdrant
     docstore-manager qdrant scroll --collection my-collection --limit 100 --offset 0

     # For Solr
     docstore-manager solr search --collection my-collection --query "*:*" --limit 100 --offset 0
     ```

     ## Vector Operations (Qdrant)

     ### Vector Search

     To search using vector similarity:

     ```bash
     docstore-manager qdrant search --collection my-collection --vector-file query_vector.json --limit 10
     ```

     ### Hybrid Search

     To combine vector search with filtering:

     ```bash
     docstore-manager qdrant search --collection my-collection --vector-file query_vector.json --filter '{"key":"category","match":{"value":"product"}}' --limit 10
     ```

     ## Text Search (Solr)

     ### Basic Text Search

     To search using text queries:

     ```bash
     docstore-manager solr search --collection my-collection --query "title:example OR content:example"
     ```

     ### Faceted Search

     To perform faceted search:

     ```bash
     docstore-manager solr search --collection my-collection --query "*:*" --facet "category"
     ```

     ## Scripting

     docstore-manager can be used in scripts:

     ```bash
     #!/bin/bash
     # Example script to backup all collections

     collections=$(docstore-manager qdrant list --format json | jq -r '.collections[].name')
     for collection in $collections; do
       echo "Backing up $collection..."
       docstore-manager qdrant get --collection $collection --query "*:*" --format json --output "backup_$collection.json"
     done
     ```

     ## Using with Python

     docstore-manager can also be used as a Python library:

     ```python
     from docstore_manager.qdrant import QdrantClient

     # Initialize client
     client = QdrantClient(url="localhost", port=6333)

     # List collections
     collections = client.list_collections()
     print(collections)

     # Create collection
     client.create_collection(
         collection_name="my-collection",
         vector_size=1536,
         distance="cosine"
     )

     # Add documents
     client.add_documents(
         collection_name="my-collection",
         documents=[
             {"id": "1", "vector": [0.1, 0.2, ...], "payload": {"text": "Example document"}},
             {"id": "2", "vector": [0.3, 0.4, ...], "payload": {"text": "Another example"}},
         ]
     )

     # Search documents
     results = client.search(
         collection_name="my-collection",
         query_vector=[0.1, 0.2, ...],
         limit=10
     )
     print(results)
     ```
     ```

7. [DONE] Update the mkdocs.yml navigation
   - Ensure the user guide pages are properly included in the navigation
   - Update the `nav` section in `mkdocs.yml` to include the user guide index page:
     ```yaml
     nav:
       # ... existing navigation ...
       - User Guide:
         - Overview: user-guide/index.md
         - Installation: user-guide/installation.md
         - Configuration: user-guide/configuration.md
         - Basic Usage: user-guide/basic-usage.md
         - Advanced Usage: user-guide/advanced-usage.md
       # ... rest of navigation ...
     ```

8. [DONE] Test the user guide
   - Run `mkdocs serve` to start a local server
   - Navigate to the user guide pages in the browser
   - Verify that all pages are accessible and properly formatted
   - Check that all links work correctly
   - Ensure that code examples are properly highlighted

9. [DONE] Add a link to the user guide in the README (already existed)
   - Add a section to the README.md that points to the user guide
   - For example:
     ```markdown
     ## Documentation

     For detailed documentation, see the [User Guide](https://allenday.github.io/docstore-manager/user-guide/).
     ```

## Dependencies
- Requires: [Strategy_integrate_mkdocs] ✓
- Blocks: None

## Expected Output
- ✓ A comprehensive user guide covering installation, configuration, basic usage, and advanced usage
- ✓ User guide organized into clear sections with examples
- ✓ User guide accessible through the MkDocs site
- ✓ Link to the user guide in the README

## Completion Notes
The user guide has been successfully created and integrated into the MkDocs site. The following was accomplished:
- Created the user guide index page (docs/user-guide/index.md)
- Verified that the installation, configuration, basic-usage, and advanced-usage guides already existed
- Updated the mkdocs.yml navigation to include the user guide index page
- Tested the user guide by running mkdocs serve and verifying that all pages are accessible and properly formatted
- Confirmed that the README.md already had a link to the user guide
- All changes were committed to a dedicated branch (task/user-guide-creation), pushed to the remote repository, and merged into the dev branch
