# Task: Create Usage Examples
**Parent:** `implementation_plan_documentation.md`
**Children:** None

## Objective
Create comprehensive usage examples for both Qdrant and Solr interfaces, covering all major operations to help users understand how to effectively use the docstore-manager tool.

## Context
The docstore-manager project provides a unified command-line interface for managing both Qdrant and Solr document stores. Clear and comprehensive usage examples are essential for users to understand how to use the tool effectively. These examples should cover all major operations for both Qdrant and Solr, and should be provided in both the README and as standalone example scripts.

## Steps
1. Identify all major operations for both Qdrant and Solr
   - Basic Operations
     - list collections
     - create collection
     - delete collection
     - get collection info
   - Document Operations
     - add documents
     - remove documents
     - get documents
   - Search Operations
     - search documents
     - scroll through documents (Qdrant)
     - count documents

2. Create examples for Qdrant Basic Operations
   - List collections example
   - Create collection example with various parameters
   - Delete collection example
   - Get collection info example

3. Create examples for Qdrant Document Operations
   - Add documents example with various input methods (file, JSON string)
   - Remove documents example with various filtering options (IDs, filter)
   - Get documents example with various output formats

4. Create examples for Qdrant Search Operations
   - Search documents example with vector query
   - Search documents example with filter
   - Scroll through documents example
   - Count documents example

5. Create examples for Solr Basic Operations
   - List collections/cores example
   - Create collection/core example
   - Delete collection/core example
   - Get collection/core info example

6. Create examples for Solr Document Operations
   - Add documents example with various input methods
   - Remove documents example
   - Get documents example

7. Create examples for Solr Search Operations
   - Search documents example with query string
   - Search documents example with filter
   - Count documents example

8. Create standalone example scripts
   - Create a directory for example scripts
   - Create separate script files for each major operation
   - Include comments explaining each step
   - Ensure scripts are runnable with minimal modification

9. Update the README with selected examples
   - Add a balanced set of examples for both Qdrant and Solr
   - Ensure examples are clear and concise
   - Include examples for all major operations
   - Use consistent formatting and terminology

10. Test all examples
    - Verify that all examples work as expected
    - Ensure examples use the correct command syntax
    - Check for any errors or inconsistencies

## Dependencies
- Requires: None
- Blocks: None

## Expected Output
1. A comprehensive set of usage examples for both Qdrant and Solr interfaces, covering all major operations
2. Standalone example scripts in a dedicated directory
3. Updated README with selected examples
4. All examples should be clear, concise, and follow a consistent style
5. Examples should use the correct command syntax and work as expected

Example format for CLI examples in the README:
```bash
# List all collections in Qdrant
docstore-manager qdrant list

# Create a new Qdrant collection with custom settings
docstore-manager qdrant create --collection my-collection --size 1536 --distance euclid

# List all collections/cores in Solr
docstore-manager solr list

# Create a new Solr collection with custom settings
docstore-manager solr create --collection my-collection --config basic_configs
```

Example format for standalone script:
```python
#!/usr/bin/env python
"""
Example: Adding documents to a Qdrant collection
"""
import subprocess
import json

# Define the collection name
COLLECTION_NAME = "example_collection"

# Create a collection if it doesn't exist
subprocess.run([
    "docstore-manager", "qdrant", "create",
    "--collection", COLLECTION_NAME,
    "--size", "4",  # Vector dimension
    "--distance", "cosine"
])

# Prepare some example documents
documents = [
    {"id": "doc1", "vector": [0.1, 0.2, 0.3, 0.4], "payload": {"text": "Example document 1"}},
    {"id": "doc2", "vector": [0.2, 0.3, 0.4, 0.5], "payload": {"text": "Example document 2"}},
    {"id": "doc3", "vector": [0.3, 0.4, 0.5, 0.6], "payload": {"text": "Example document 3"}}
]

# Save documents to a temporary file
with open("example_docs.jsonl", "w") as f:
    for doc in documents:
        f.write(json.dumps(doc) + "\n")

# Add documents from the file
subprocess.run([
    "docstore-manager", "qdrant", "add-documents",
    "--collection", COLLECTION_NAME,
    "--file", "example_docs.jsonl"
])

# Verify documents were added
subprocess.run([
    "docstore-manager", "qdrant", "count",
    "--collection", COLLECTION_NAME
])

print("Documents successfully added to the collection.")
