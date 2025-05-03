# Task: Create Usage Examples [COMPLETED]
**Parent:** `implementation_plan_documentation.md`
**Children:** None

## Objective
Create comprehensive usage examples for both Qdrant and Solr interfaces, covering all major operations to help users understand how to effectively use the docstore-manager tool.

## Context
The docstore-manager project provides a unified command-line interface for managing both Qdrant and Solr document stores. Clear and comprehensive usage examples are essential for users to understand how to use the tool effectively. These examples should cover all major operations for both Qdrant and Solr, and should be provided in both the README and as standalone example scripts.

## Steps
1. ✅ Identify all major operations for both Qdrant and Solr
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

2. ✅ Create examples for Qdrant Basic Operations
   - ✅ List collections example
   - ✅ Create collection example with various parameters
   - ✅ Delete collection example
   - ✅ Get collection info example

3. ✅ Create examples for Qdrant Document Operations
   - ✅ Add documents example with various input methods (file, JSON string)
   - ✅ Remove documents example with various filtering options (IDs, filter)
   - ✅ Get documents example with various output formats

4. ✅ Create examples for Qdrant Search Operations
   - ✅ Search documents example with vector query
   - ✅ Search documents example with filter
   - ✅ Scroll through documents example
   - ✅ Count documents example

5. ✅ Create examples for Solr Basic Operations
   - ✅ List collections/cores example
   - ✅ Create collection/core example
   - ✅ Delete collection/core example
   - ✅ Get collection/core info example

6. ✅ Create examples for Solr Document Operations
   - ✅ Add documents example with various input methods
   - ✅ Remove documents example
   - ✅ Get documents example

7. ✅ Create examples for Solr Search Operations
   - ✅ Search documents example with query string
   - ✅ Search documents example with filter
   - ✅ Count documents example

8. ✅ Create standalone example scripts
   - ✅ Create a directory for example scripts
   - ✅ Create separate script files for each major operation
   - ✅ Include comments explaining each step
   - ✅ Ensure scripts are runnable with minimal modification

9. ✅ Update the README with selected examples
   - ✅ Add a balanced set of examples for both Qdrant and Solr
   - ✅ Ensure examples are clear and concise
   - ✅ Include examples for all major operations
   - ✅ Use consistent formatting and terminology

10. ✅ Test all examples
    - ✅ Verify that all examples work as expected
    - ✅ Ensure examples use the correct command syntax
    - ✅ Check for any errors or inconsistencies

## Dependencies
- Requires: None
- Blocks: None

## Expected Output
1. ✅ A comprehensive set of usage examples for both Qdrant and Solr interfaces, covering all major operations
2. ✅ Standalone example scripts in a dedicated directory
3. ✅ Updated README with selected examples
4. ✅ All examples should be clear, concise, and follow a consistent style
5. ✅ Examples should use the correct command syntax and work as expected

## Completion Notes
- Created a dedicated examples directory with subdirectories for Qdrant and Solr
- Created a README.md file for the examples directory explaining the purpose and structure
- Created comprehensive example scripts for all major Qdrant operations:
  - list_collections.py: Listing collections
  - create_collection.py: Creating a collection with custom settings
  - collection_info.py: Getting detailed information about a collection
  - delete_collection.py: Deleting a collection
  - add_documents.py: Adding documents to a collection (file and JSON methods)
  - remove_documents.py: Removing documents from a collection (ID, file, and filter methods)
  - get_documents.py: Retrieving documents by ID, file, and filter
  - search_documents.py: Searching documents with vector similarity and filters
  - count_documents.py: Counting documents with and without filters
  - scroll_documents.py: Paginating through documents in a collection
- Created comprehensive example scripts for all major Solr operations:
  - list_collections.py: Listing collections
  - create_collection.py: Creating a collection with custom settings
  - collection_info.py: Getting detailed information about a collection
  - delete_collection.py: Deleting a collection
  - add_documents.py: Adding documents to a collection (file and JSON methods)
  - remove_documents.py: Removing documents from a collection (ID, file, and query methods)
  - get_documents.py: Retrieving documents by ID, file, and query
  - search_documents.py: Searching documents with various query types and filters
- All examples include detailed comments, error handling, and cleanup of temporary files
- Examples demonstrate both basic and advanced usage of each command
- Updated the README with selected examples for both Qdrant and Solr
