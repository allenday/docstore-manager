#!/usr/bin/env python3
"""
Example: Searching Documents in a Solr Collection

This example demonstrates how to search for documents in a Solr collection
using various query types with the docstore-manager CLI tool.
"""
import subprocess
import sys
import json
import os
import tempfile

def main():
    """Run the example."""
    print("Example: Searching Documents in a Solr Collection")
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
        
        # Add some example documents to search
        print("\nAdding example documents to the collection...")
        documents = [
            {
                "id": "doc1",
                "title": "Introduction to Solr",
                "content": "Solr is an open-source search platform built on Apache Lucene.",
                "category": "technology",
                "tags": ["search", "apache", "lucene"],
                "published_date": "2025-01-15T12:00:00Z",
                "rating": 4.5,
                "views": 1200
            },
            {
                "id": "doc2",
                "title": "Advanced Solr Features",
                "content": "Solr provides faceting, highlighting, and spatial search capabilities.",
                "category": "technology",
                "tags": ["search", "advanced", "features"],
                "published_date": "2025-02-20T14:30:00Z",
                "rating": 4.8,
                "views": 950
            },
            {
                "id": "doc3",
                "title": "Solr vs Elasticsearch",
                "content": "Comparing two popular search platforms based on Lucene.",
                "category": "comparison",
                "tags": ["search", "elasticsearch", "comparison"],
                "published_date": "2025-03-10T09:15:00Z",
                "rating": 4.2,
                "views": 2500
            },
            {
                "id": "doc4",
                "title": "Solr Schema Design",
                "content": "Best practices for designing Solr schemas for optimal performance.",
                "category": "technology",
                "tags": ["search", "schema", "performance"],
                "published_date": "2025-04-05T16:45:00Z",
                "rating": 4.6,
                "views": 800
            },
            {
                "id": "doc5",
                "title": "Solr in Production",
                "content": "Deploying and maintaining Solr in production environments.",
                "category": "operations",
                "tags": ["search", "production", "deployment"],
                "published_date": "2025-05-12T11:30:00Z",
                "rating": 4.7,
                "views": 1500
            },
            {
                "id": "doc6",
                "title": "Optimizing Solr Performance",
                "content": "Tips and tricks for optimizing Solr for high-performance search applications.",
                "category": "performance",
                "tags": ["search", "optimization", "performance"],
                "published_date": "2025-06-18T10:00:00Z",
                "rating": 4.9,
                "views": 1800
            },
            {
                "id": "doc7",
                "title": "Solr Security Best Practices",
                "content": "Securing your Solr installation against common vulnerabilities.",
                "category": "security",
                "tags": ["search", "security", "best-practices"],
                "published_date": "2025-07-22T13:45:00Z",
                "rating": 4.7,
                "views": 1100
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
        
        # Method 1: Basic keyword search
        print("\nMethod 1: Basic keyword search")
        print("----------------------------")
        
        # Simple query
        query = "title:Solr"
        
        print(f"Searching for documents with query: '{query}'")
        
        # Search with basic query
        search_basic_result = subprocess.run(
            [
                "docstore-manager", "solr", "search",
                "--collection", collection_name,
                "--query", query,
                "--limit", "10"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nSearch results (basic keyword):")
        print(search_basic_result.stdout)
        
        # Method 2: Search with filter query
        print("\nMethod 2: Search with filter query")
        print("-------------------------------")
        
        # Main query and filter query
        main_query = "*:*"  # Match all documents
        filter_query = "category:technology"
        
        print(f"Searching with main query: '{main_query}' and filter: '{filter_query}'")
        
        # Search with filter
        search_filter_result = subprocess.run(
            [
                "docstore-manager", "solr", "search",
                "--collection", collection_name,
                "--query", main_query,
                "--filter", filter_query,
                "--limit", "10"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nSearch results (with filter):")
        print(search_filter_result.stdout)
        
        # Method 3: Search with multiple filters
        print("\nMethod 3: Search with multiple filters")
        print("-----------------------------------")
        
        # Main query and multiple filters
        main_query = "content:search"
        filter_queries = ["rating:[4.5 TO *]", "views:[1000 TO *]"]
        
        print(f"Searching with main query: '{main_query}' and filters: {filter_queries}")
        
        # Build command with multiple filter arguments
        command = [
            "docstore-manager", "solr", "search",
            "--collection", collection_name,
            "--query", main_query,
            "--limit", "10"
        ]
        
        # Add each filter query as a separate --filter argument
        for fq in filter_queries:
            command.extend(["--filter", fq])
        
        # Search with multiple filters
        search_multi_filter_result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nSearch results (with multiple filters):")
        print(search_multi_filter_result.stdout)
        
        # Method 4: Search with field selection
        print("\nMethod 4: Search with field selection")
        print("----------------------------------")
        
        # Query and fields to return
        query = "*:*"
        fields = "id,title,rating,views"
        
        print(f"Searching with query: '{query}' and returning fields: '{fields}'")
        
        # Search with field selection
        search_fields_result = subprocess.run(
            [
                "docstore-manager", "solr", "search",
                "--collection", collection_name,
                "--query", query,
                "--fields", fields,
                "--limit", "5"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nSearch results (with field selection):")
        print(search_fields_result.stdout)
        
        # Method 5: Search with sorting
        print("\nMethod 5: Search with sorting")
        print("---------------------------")
        
        # Query and sort field
        query = "category:technology"
        sort = "rating desc"  # Sort by rating in descending order
        
        print(f"Searching with query: '{query}' and sorting by: '{sort}'")
        
        # Search with sorting
        search_sort_result = subprocess.run(
            [
                "docstore-manager", "solr", "search",
                "--collection", collection_name,
                "--query", query,
                "--sort", sort,
                "--limit", "10"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nSearch results (with sorting):")
        print(search_sort_result.stdout)
        
        # Method 6: Export search results to file
        print("\nMethod 6: Export search results to file")
        print("------------------------------------")
        
        # Create a temporary file for CSV export
        csv_file_path = os.path.join(tempfile.gettempdir(), "solr_search.csv")
        
        # Search and export as CSV
        search_export_result = subprocess.run(
            [
                "docstore-manager", "solr", "search",
                "--collection", collection_name,
                "--query", "rating:[4.5 TO *]",
                "--sort", "views desc",
                "--fields", "id,title,rating,views",
                "--format", "csv",
                "--output", csv_file_path
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"\nExported search results to CSV: {csv_file_path}")
        
        # Read and display the CSV file
        with open(csv_file_path, 'r') as csv_file:
            csv_content = csv_file.read()
            print("\nCSV content:")
            print(csv_content)
        
        # Clean up the temporary files
        print(f"\nCleaning up temporary files...")
        os.unlink(temp_file_path)
        os.unlink(csv_file_path)
        print("Temporary files deleted.")
        
        # Show additional information
        print("\nAdditional Information:")
        print("----------------------")
        print("1. Query Syntax:")
        print("   - Simple field queries: field:value (e.g., title:Solr)")
        print("   - Wildcard queries: field:value* (e.g., title:Sol*)")
        print("   - Phrase queries: field:\"exact phrase\" (e.g., title:\"Solr Features\")")
        print("   - Range queries: field:[min TO max] (e.g., rating:[4.0 TO 5.0])")
        print("   - Boolean operators: AND, OR, NOT (e.g., title:Solr AND NOT category:security)")
        
        print("\n2. Filter Queries:")
        print("   - Used to narrow down results without affecting relevance scoring")
        print("   - Multiple filters can be applied (use --filter multiple times)")
        print("   - Filters are cached by Solr for better performance")
        
        print("\n3. Sorting:")
        print("   - Format: field direction (e.g., rating desc)")
        print("   - Multiple sort fields: field1 dir1,field2 dir2 (e.g., rating desc,views desc)")
        print("   - Direction can be 'asc' (ascending) or 'desc' (descending)")
        
        print("\n4. Output Options:")
        print("   - Format: json (default), csv, yaml, table")
        print("   - Fields: Specify which fields to include in the output")
        print("   - Limit: Control the number of results returned")
        print("   - Output: Save results to a file instead of displaying them")
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        # Clean up temp files if they exist
        for path_var in ['temp_file_path', 'csv_file_path']:
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
        for path_var in ['temp_file_path', 'csv_file_path']:
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
        for path_var in ['temp_file_path', 'csv_file_path']:
            if path_var in locals():
                try:
                    os.unlink(locals()[path_var])
                    print(f"Cleaned up temporary file: {locals()[path_var]}")
                except:
                    pass
        sys.exit(1)

if __name__ == "__main__":
    main()
