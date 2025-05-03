#!/usr/bin/env python3
"""
Example: Adding Documents to a Solr Collection

This example demonstrates how to add documents to a Solr collection
using the docstore-manager CLI tool.
"""
import subprocess
import sys
import json
import os
import tempfile

def main():
    """Run the example."""
    print("Example: Adding Documents to a Solr Collection")
    print("=========================================")
    
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
        
        # Prepare example documents
        print("\nPreparing example documents...")
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
            }
        ]
        
        # Method 1: Add documents from a file
        print("\nMethod 1: Adding documents from a file")
        print("--------------------------------------")
        
        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file_path = temp_file.name
            json.dump(documents, temp_file)
        
        print(f"Created temporary JSON file: {temp_file_path}")
        print("File contents (JSON array of documents):")
        print(json.dumps(documents, indent=2))
        
        # Add documents from the file
        print("\nAdding documents from file...")
        add_file_result = subprocess.run(
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
        
        print("\nCommand output:")
        print(add_file_result.stdout)
        
        # Method 2: Add documents directly with JSON string
        print("\nMethod 2: Adding documents with JSON string")
        print("------------------------------------------")
        
        # Create new documents
        direct_documents = [
            {
                "id": "direct1",
                "title": "Direct Document Example",
                "content": "This document was added directly via JSON string.",
                "category": "example",
                "tags": ["direct", "json", "string"],
                "published_date": "2025-04-01T10:00:00Z",
                "rating": 3.9
            }
        ]
        
        # Convert to JSON string
        docs_json = json.dumps(direct_documents)
        print(f"JSON string for direct addition: {docs_json}")
        
        # Add documents directly
        print("\nAdding documents directly...")
        add_direct_result = subprocess.run(
            [
                "docstore-manager", "solr", "add-documents",
                "--collection", collection_name,
                "--doc", docs_json,
                "--commit"  # Commit changes immediately
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nCommand output:")
        print(add_direct_result.stdout)
        
        # Verify documents were added
        print("\nVerifying documents were added...")
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
        
        print("\nDocuments in collection:")
        print(get_result.stdout)
        
        # Clean up the temporary file
        print(f"\nCleaning up temporary file...")
        os.unlink(temp_file_path)
        print("Temporary file deleted.")
        
        # Show additional information
        print("\nAdditional Information:")
        print("----------------------")
        print("1. Document Format:")
        print("   - Documents must be valid JSON objects")
        print("   - Each document must have a unique 'id' field")
        print("   - Field names must match the schema")
        print("   - Date fields should use ISO-8601 format (YYYY-MM-DDThh:mm:ssZ)")
        
        print("\n2. Commit Options:")
        print("   - Use --commit to make documents immediately searchable")
        print("   - Without --commit, documents are added but not visible until the next commit")
        print("   - For bulk indexing, consider batching documents and committing less frequently")
        
        print("\n3. Command Variations:")
        print("   docstore-manager solr add-documents --collection my_collection --doc @documents.json")
        print("   docstore-manager solr add-documents --collection my_collection --doc '[{\"id\":\"doc1\",\"title\":\"Example\"}]'")
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        # Clean up temp file if it exists
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
                print(f"Cleaned up temporary file: {temp_file_path}")
            except:
                pass
        print("\nPossible issues:")
        print("- Solr instance is not running")
        print("- Connection configuration is incorrect")
        print("- Collection does not exist")
        print("- Document format does not match schema")
        print("\nMake sure Solr is running and properly configured in your docstore-manager config file.")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: docstore-manager command not found. Make sure it's installed and in your PATH.")
        print("Install with: pip install docstore-manager")
        # Clean up temp file if it exists
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
                print(f"Cleaned up temporary file: {temp_file_path}")
            except:
                pass
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Clean up temp file if it exists
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
                print(f"Cleaned up temporary file: {temp_file_path}")
            except:
                pass
        sys.exit(1)

if __name__ == "__main__":
    main()
