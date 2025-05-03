#!/usr/bin/env python3
"""
Example: Getting Documents from a Solr Collection

This example demonstrates how to retrieve documents from a Solr collection
using the docstore-manager CLI tool, with both ID-based and query-based retrieval.
"""
import subprocess
import sys
import json
import os
import tempfile

def main():
    """Run the example."""
    print("Example: Getting Documents from a Solr Collection")
    print("===========================================")
    
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
        
        # Method 1: Get documents by ID list
        print("\nMethod 1: Get documents by ID list")
        print("--------------------------------")
        
        # IDs to retrieve
        ids_to_get = ["doc1", "doc3"]
        ids_str = ",".join(ids_to_get)
        
        print(f"Retrieving documents with IDs: {ids_str}")
        
        # Get documents by ID
        get_by_id_result = subprocess.run(
            [
                "docstore-manager", "solr", "get",
                "--collection", collection_name,
                "--ids", ids_str
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nRetrieved documents by ID:")
        print(get_by_id_result.stdout)
        
        # Method 2: Get documents by ID file
        print("\nMethod 2: Get documents by ID file")
        print("--------------------------------")
        
        # Create a temporary file with IDs
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as id_file:
            id_file_path = id_file.name
            id_file.write("doc2\ndoc4\n")  # One ID per line
        
        print(f"Created temporary ID file: {id_file_path}")
        print("File contents (one ID per line):")
        print("doc2")
        print("doc4")
        
        # Get documents by ID file
        get_by_file_result = subprocess.run(
            [
                "docstore-manager", "solr", "get",
                "--collection", collection_name,
                "--id-file", id_file_path
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nRetrieved documents by ID file:")
        print(get_by_file_result.stdout)
        
        # Method 3: Get documents by query
        print("\nMethod 3: Get documents by query")
        print("------------------------------")
        
        # Query to match documents
        query = "category:technology"
        
        print(f"Retrieving documents matching query: '{query}'")
        
        # Get documents by query
        get_by_query_result = subprocess.run(
            [
                "docstore-manager", "solr", "get",
                "--collection", collection_name,
                "--query", query,
                "--limit", "10"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nRetrieved documents by query:")
        print(get_by_query_result.stdout)
        
        # Method 4: Get documents with specific fields
        print("\nMethod 4: Get documents with specific fields")
        print("----------------------------------------")
        
        # Fields to retrieve
        fields = "id,title,rating"
        
        print(f"Retrieving documents with specific fields: {fields}")
        
        # Get documents with specific fields
        get_with_fields_result = subprocess.run(
            [
                "docstore-manager", "solr", "get",
                "--collection", collection_name,
                "--query", "*:*",
                "--fields", fields,
                "--limit", "3"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nRetrieved documents with specific fields:")
        print(get_with_fields_result.stdout)
        
        # Method 5: Export to different formats
        print("\nMethod 5: Export to different formats")
        print("----------------------------------")
        
        # Create a temporary file for CSV export
        csv_file_path = os.path.join(tempfile.gettempdir(), "solr_docs.csv")
        
        # Get documents and export as CSV
        get_csv_result = subprocess.run(
            [
                "docstore-manager", "solr", "get",
                "--collection", collection_name,
                "--query", "rating:[4.5 TO *]",  # Documents with rating >= 4.5
                "--format", "csv",
                "--output", csv_file_path
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"\nExported documents to CSV: {csv_file_path}")
        
        # Read and display the CSV file
        with open(csv_file_path, 'r') as csv_file:
            csv_content = csv_file.read()
            print("\nCSV content:")
            print(csv_content)
        
        # Clean up the temporary files
        print(f"\nCleaning up temporary files...")
        os.unlink(temp_file_path)
        os.unlink(id_file_path)
        os.unlink(csv_file_path)
        print("Temporary files deleted.")
        
        # Show additional information
        print("\nAdditional Information:")
        print("----------------------")
        print("1. Retrieval Methods:")
        print("   - By ID: Retrieves specific documents by their unique IDs")
        print("   - By ID file: Retrieves documents listed in a file (one ID per line)")
        print("   - By query: Retrieves all documents matching a Solr query")
        
        print("\n2. Query Syntax:")
        print("   - Simple queries: field:value (e.g., category:technology)")
        print("   - Wildcard queries: field:value* (e.g., title:Intro*)")
        print("   - Range queries: field:[min TO max] (e.g., rating:[4.0 TO 5.0])")
        print("   - Boolean operators: AND, OR, NOT (e.g., category:technology AND rating:[4.0 TO *])")
        
        print("\n3. Output Options:")
        print("   - Format: json (default), csv, yaml, table")
        print("   - Fields: Specify which fields to include in the output")
        print("   - Limit: Control the number of results returned")
        print("   - Output: Save results to a file instead of displaying them")
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        # Clean up temp files if they exist
        for path_var in ['temp_file_path', 'id_file_path', 'csv_file_path']:
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
        for path_var in ['temp_file_path', 'id_file_path', 'csv_file_path']:
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
        for path_var in ['temp_file_path', 'id_file_path', 'csv_file_path']:
            if path_var in locals():
                try:
                    os.unlink(locals()[path_var])
                    print(f"Cleaned up temporary file: {locals()[path_var]}")
                except:
                    pass
        sys.exit(1)

if __name__ == "__main__":
    main()
