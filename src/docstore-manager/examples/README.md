# docstore-manager Examples

This directory contains example scripts demonstrating how to use the docstore-manager CLI tool for both Qdrant and Solr document stores.

## Directory Structure

- `qdrant/`: Examples for Qdrant vector database operations
- `solr/`: Examples for Solr search platform operations

## Running the Examples

Most examples are standalone Python scripts that use subprocess to call the docstore-manager CLI. To run an example:

1. Ensure docstore-manager is installed:
   ```bash
   pip install docstore-manager
   ```

2. Make sure the required document store (Qdrant or Solr) is running:
   - For Qdrant: `docker run -p 6333:6333 qdrant/qdrant`
   - For Solr: `docker run -p 8983:8983 solr:latest`

3. Run the example script:
   ```bash
   python examples/qdrant/create_collection.py
   ```

## Example Categories

### Qdrant Examples

- **Basic Operations**: List, create, delete, and get information about collections
- **Document Operations**: Add, remove, and retrieve documents
- **Search Operations**: Search documents, scroll through results, count documents

### Solr Examples

- **Basic Operations**: List, create, delete, and get information about collections/cores
- **Document Operations**: Add, remove, and retrieve documents
- **Search Operations**: Search documents with query strings and filters

## Configuration

The examples use the default configuration profile. To use a different profile, modify the examples to include the `--profile` option in the command calls.

## Notes

- These examples are for demonstration purposes and may need to be adapted for production use.
- Error handling in the examples is minimal to keep them concise and focused on the main functionality.
- Some examples create temporary files that are cleaned up after execution.
