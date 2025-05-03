#!/usr/bin/env python3
"""
Example: Searching Documents in a Qdrant Collection

This example demonstrates how to search for documents in a Qdrant collection
using vector similarity and filters with the docstore-manager CLI tool.
"""
import subprocess
import sys
import json
import os
import tempfile
import random

def main():
    """Run the example."""
    print("Example: Searching Documents in a Qdrant Collection")
    print("==============================================")
    
    # Define collection name and vector dimension
    collection_name = "example_collection"
    vector_size = 4  # Small dimension for the example
    
    print(f"Target collection: '{collection_name}' (vector size: {vector_size})")
    
    try:
        # First, ensure the collection exists with the right dimension
        list_result = subprocess.run(
            ["docstore-manager", "qdrant", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        collection_exists = False
        try:
            collections = json.loads(list_result.stdout)
            if collection_name in collections:
                collection_exists = True
        except json.JSONDecodeError:
            print("Warning: Could not parse collection list. Proceeding anyway.")
        
        if not collection_exists:
            print(f"\nCollection '{collection_name}' does not exist. Creating it...")
            
            # Create the collection with the specified vector size
            create_result = subprocess.run(
                [
                    "docstore-manager", "qdrant", "create",
                    "--collection", collection_name,
                    "--size", str(vector_size),
                    "--distance", "cosine"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            print("Collection created.")
        
        # Add some example documents to search
        print("\nAdding example documents to the collection...")
        documents = [
            {
                "id": "doc1",
                "vector": [0.1, 0.2, 0.3, 0.4],
                "payload": {
                    "text": "Red apple on a wooden table",
                    "category": "fruit",
                    "color": "red",
                    "price": 1.20
                }
            },
            {
                "id": "doc2",
                "vector": [0.2, 0.3, 0.4, 0.5],
                "payload": {
                    "text": "Green apple in a white bowl",
                    "category": "fruit",
                    "color": "green",
                    "price": 1.50
                }
            },
            {
                "id": "doc3",
                "vector": [0.3, 0.4, 0.5, 0.6],
                "payload": {
                    "text": "Yellow banana on a plate",
                    "category": "fruit",
                    "color": "yellow",
                    "price": 0.80
                }
            },
            {
                "id": "doc4",
                "vector": [0.4, 0.5, 0.6, 0.7],
                "payload": {
                    "text": "Orange carrot in a garden",
                    "category": "vegetable",
                    "color": "orange",
                    "price": 0.90
                }
            },
            {
                "id": "doc5",
                "vector": [0.5, 0.6, 0.7, 0.8],
                "payload": {
                    "text": "Red tomato on a vine",
                    "category": "vegetable",
                    "color": "red",
                    "price": 1.10
                }
            }
        ]
        
        # Create a temporary JSONL file for the documents
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as temp_file:
            temp_file_path = temp_file.name
            for doc in documents:
                temp_file.write(json.dumps(doc) + '\n')
        
        # Add documents from the file
        add_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "add-documents",
                "--collection", collection_name,
                "--file", temp_file_path
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("Documents added successfully!")
        
        # Method 1: Search by vector similarity
        print("\nMethod 1: Search by vector similarity")
        print("------------------------------------")
        
        # Create a query vector (similar to doc3 - banana)
        query_vector = [0.32, 0.42, 0.52, 0.62]  # Slightly modified from doc3's vector
        
        # Create a temporary file for the query vector
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as vector_file:
            vector_file_path = vector_file.name
            json.dump(query_vector, vector_file)
        
        print(f"Created query vector: {query_vector}")
        print(f"Saved to temporary file: {vector_file_path}")
        
        # Search by vector similarity
        print("\nSearching for similar documents...")
        search_vector_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "search",
                "--collection", collection_name,
                "--query-vector", json.dumps(query_vector),
                "--limit", "3",
                "--with-vectors"  # Include vectors in the output
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nSearch results (vector similarity):")
        print(search_vector_result.stdout)
        
        # Method 2: Search with filter
        print("\nMethod 2: Search with filter")
        print("---------------------------")
        
        # Create a filter for red items
        filter_json = json.dumps({
            "must": [
                {
                    "key": "color",
                    "match": {
                        "value": "red"
                    }
                }
            ]
        })
        
        print(f"Filter for red items: {filter_json}")
        
        # Search with filter
        print("\nSearching for documents matching filter...")
        search_filter_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "search",
                "--collection", collection_name,
                "--query-vector", json.dumps(query_vector),
                "--query-filter-json", filter_json,
                "--limit", "2"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nSearch results (with filter):")
        print(search_filter_result.stdout)
        
        # Method 3: Combine vector search with complex filter
        print("\nMethod 3: Combine vector search with complex filter")
        print("------------------------------------------------")
        
        # Create a complex filter for fruits with price > 1.00
        complex_filter_json = json.dumps({
            "must": [
                {
                    "key": "category",
                    "match": {
                        "value": "fruit"
                    }
                },
                {
                    "key": "price",
                    "range": {
                        "gt": 1.00
                    }
                }
            ]
        })
        
        print(f"Complex filter for fruits with price > 1.00: {complex_filter_json}")
        
        # Search with complex filter
        print("\nSearching for documents matching complex filter...")
        search_complex_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "search",
                "--collection", collection_name,
                "--query-vector", json.dumps(query_vector),
                "--query-filter-json", complex_filter_json,
                "--limit", "5"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nSearch results (with complex filter):")
        print(search_complex_result.stdout)
        
        # Clean up the temporary files
        print(f"\nCleaning up temporary files...")
        os.unlink(temp_file_path)
        os.unlink(vector_file_path)
        print("Temporary files deleted.")
        
        # Show additional options
        print("\nAdditional options for search command:")
        print("- Use --with-vectors to include vectors in the output")
        print("- Use --with-payload/--without-payload to control payload inclusion")
        print("- Use --limit to control the number of results")
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        # Clean up temp files if they exist
        for path_var in ['temp_file_path', 'vector_file_path']:
            if path_var in locals():
                try:
                    os.unlink(locals()[path_var])
                    print(f"Cleaned up temporary file: {locals()[path_var]}")
                except:
                    pass
        sys.exit(1)
    except FileNotFoundError:
        print("Error: docstore-manager command not found. Make sure it's installed and in your PATH.")
        print("Install with: pip install docstore-manager")
        # Clean up temp files if they exist
        for path_var in ['temp_file_path', 'vector_file_path']:
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
        for path_var in ['temp_file_path', 'vector_file_path']:
            if path_var in locals():
                try:
                    os.unlink(locals()[path_var])
                    print(f"Cleaned up temporary file: {locals()[path_var]}")
                except:
                    pass
        sys.exit(1)

if __name__ == "__main__":
    main()
