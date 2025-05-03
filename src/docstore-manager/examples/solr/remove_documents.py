#!/usr/bin/env python3
"""
Example: Removing Documents from a Solr Collection

This example demonstrates how to remove documents from a Solr collection
using the docstore-manager CLI tool, with both ID-based and query-based removal.
"""
import subprocess
import sys
import json
import os
import tempfile

def main():
    """Run the example."""
    print("Example: Removing Documents from a Solr Collection")
    print("============================================")
    
    # Define collection name
    collection_name = "example_collection"
    
    print(f"Target collection: '{collection_name}'")
    
    try:
        # First, check if the collection exists
        list_result = subprocess.run(
            ["docstore-manager", "solr", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        collection_exists = False
        try:
            collections = json.loads(list_result.stdout)
            if collection_name in collections:
                collection_exists = True
            else:
                print(f"\nCollection '{collection_name}' does not exist. Creating it first...")
                
                # Create the collection
                create_result = subprocess.run(
                    [
                        "docstore-manager", "solr", "create",
                        collection_name,
                        "--num-shards", "1",
                        "--replication-factor", "1",
                        "--configset", "basic_configs"
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print("Collection created.")
                collection_exists = True
        except json.JSONDecodeError:
            print("Warning: Could not parse collection list. Proceeding anyway.")
        
        if not collection_exists:
            print(f"Unable to verify if collection '{collection_name}' exists. Proceeding anyway.")
        
        # Add some example documents to work with
        print("\nAdding example documents to the collection...")
        documents = [
            {
                "id": "doc1",
                "title": "Introduction to Solr",
                "content": "Solr is an open-source search platform built on Apache Lucene.",
                "category": "technology",
                "tags": ["search", "apache", "lucene"],
                "published_date": "2025-01-15T12:00:00Z",
                "rating": 4.5
            },
            {
                "id": "doc2",
                "title": "Advanced Solr Features",
                "content": "Solr provides faceting, highlighting, and spatial search capabilities.",
                "category": "technology",
                "tags": ["search", "advanced", "features"],
                "published_date": "2025-02-20T14:30:00Z",
                "rating": 4.8
            },
            {
                "id": "doc3",
                "title": "Solr vs Elasticsearch",
                "content": "Comparing two popular search platforms based on Lucene.",
                "category": "comparison",
                "tags": ["search", "elasticsearch", "comparison"],
                "published_date": "2025-03-10T09:15:00Z",
                "rating": 4.2
            },
            {
                "id": "doc4",
                "title": "Solr Schema Design",
                "content": "Best practices for designing Solr schemas for optimal performance.",
                "category": "technology",
                "tags": ["search", "schema", "performance"],
                "published_date": "2025-04-05T16:45:00Z",
                "rating": 4.6
            },
            {
                "id": "doc5",
                "title": "Solr in Production",
                "content": "Deploying and maintaining Solr in production environments.",
                "category": "operations",
                "tags": ["search", "production", "deployment"],
                "published_date": "2025-05-12T11:30:00Z",
                "rating": 4.7
            }
        ]
        
        # Create a temporary JSON file for the documents
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file_path = temp_file.name
            json.dump(documents, temp_file)
        
        # Add documents from the file
        add_result = subprocess.run(
            [
                "docstore-manager", "solr", "add-documents",
                "--collection", collection_name,
                "--doc", f"@{temp_file_path}",
                "--commit"  # Commit changes immediately
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("Documents added successfully!")
        
        # Verify documents were added
        get_result = subprocess.run(
            [
                "docstore-manager", "solr", "get",
                "--collection", collection_name,
                "--query", "*:*",
                "--limit", "10"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nInitial documents in collection:")
        print(get_result.stdout)
        
        # Method 1: Remove documents by ID list
        print("\nMethod 1: Remove documents by ID list")
        print("-----------------------------------")
        
        # IDs to remove
        ids_to_remove = ["doc1", "doc3"]
        ids_str = ",".join(ids_to_remove)
        
        print(f"Removing documents with IDs: {ids_str}")
        
        # Remove documents by ID
        remove_by_id_result = subprocess.run(
            [
                "docstore-manager", "solr", "remove-documents",
                "--collection", collection_name,
                "--ids", ids_str,
                "--commit"  # Commit changes immediately
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nCommand output:")
        print(remove_by_id_result.stdout)
        
        # Verify documents were removed
        get_after_id_result = subprocess.run(
            [
                "docstore-manager", "solr", "get",
                "--collection", collection_name,
                "--query", "*:*",
                "--limit", "10"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nDocuments after ID removal:")
        print(get_after_id_result.stdout)
        
        # Method 2: Remove documents by ID file
        print("\nMethod 2: Remove documents by ID file")
        print("-----------------------------------")
        
        # Create a temporary file with IDs
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as id_file:
            id_file_path = id_file.name
            id_file.write("doc2\n")  # One ID per line
        
        print(f"Created temporary ID file: {id_file_path}")
        print("File contents (one ID per line):")
        print("doc2")
        
        # Remove documents by ID file
        remove_by_file_result = subprocess.run(
            [
                "docstore-manager", "solr", "remove-documents",
                "--collection", collection_name,
                "--id-file", id_file_path,
                "--commit"  # Commit changes immediately
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nCommand output:")
        print(remove_by_file_result.stdout)
        
        # Verify documents were removed
        get_after_file_result = subprocess.run(
            [
                "docstore-manager", "solr", "get",
                "--collection", collection_name,
                "--query", "*:*",
                "--limit", "10"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nDocuments after ID file removal:")
        print(get_after_file_result.stdout)
        
        # Method 3: Remove documents by query
        print("\nMethod 3: Remove documents by query")
        print("---------------------------------")
        
        # Query to match documents
        query = "category:operations"
        
        print(f"Removing documents matching query: '{query}'")
        
        # Remove documents by query
        remove_by_query_result = subprocess.run(
            [
                "docstore-manager", "solr", "remove-documents",
                "--collection", collection_name,
                "--query", query,
                "--commit",  # Commit changes immediately
                "--yes"  # Skip confirmation prompt
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nCommand output:")
        print(remove_by_query_result.stdout)
        
        # Verify documents were removed
        get_after_query_result = subprocess.run(
            [
                "docstore-manager", "solr", "get",
                "--collection", collection_name,
                "--query", "*:*",
                "--limit", "10"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nDocuments after query removal:")
        print(get_after_query_result.stdout)
        
        # Clean up the temporary files
        print(f"\nCleaning up temporary files...")
        os.unlink(temp_file_path)
        os.unlink(id_file_path)
        print("Temporary files deleted.")
        
        # Show additional information
        print("\nAdditional Information:")
        print("----------------------")
        print("1. Removal Methods:")
        print("   - By ID: Removes specific documents by their unique IDs")
        print("   - By ID file: Removes documents listed in a file (one ID per line)")
        print("   - By query: Removes all documents matching a Solr query")
        
        print("\n2. Commit Options:")
        print("   - Use --commit to make changes immediately visible")
        print("   - Without --commit, documents are removed but still appear in search results until the next commit")
        
        print("\n3. Safety Considerations:")
        print("   - Query-based removal requires --yes flag or confirmation")
        print("   - Consider backing up important data before bulk removals")
        print("   - Use specific queries to avoid accidentally removing too many documents")
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        # Clean up temp files if they exist
        for path_var in ['temp_file_path', 'id_file_path']:
            if path_var in locals():
                try:
                    os.unlink(locals()[path_var])
                    print(f"Cleaned up temporary file: {locals()[path_var]}")
                except:
                    pass
        print("\nPossible issues:")
        print("- Solr instance is not running")
        print("- Connection configuration is incorrect")
        print("- Collection does not exist")
        print("- Invalid query syntax")
        print("\nMake sure Solr is running and properly configured in your docstore-manager config file.")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: docstore-manager command not found. Make sure it's installed and in your PATH.")
        print("Install with: pip install docstore-manager")
        # Clean up temp files if they exist
        for path_var in ['temp_file_path', 'id_file_path']:
            if path_var in locals():
                try:
                    os.unlink(locals()[path_var])
                    print(f"Cleaned up temporary file: {locals()[path_var]}")
                except:
                    pass
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Clean up temp files if they exist
        for path_var in ['temp_file_path', 'id_file_path']:
            if path_var in locals():
                try:
                    os.unlink(locals()[path_var])
                    print(f"Cleaned up temporary file: {locals()[path_var]}")
                except:
                    pass
        sys.exit(1)

if __name__ == "__main__":
    main()
