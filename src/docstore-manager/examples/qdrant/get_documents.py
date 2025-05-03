#!/usr/bin/env python3
"""
Example: Getting Documents from a Qdrant Collection

This example demonstrates how to retrieve documents by ID from a Qdrant collection
using the docstore-manager CLI tool.
"""
import subprocess
import sys
import json
import os
import tempfile

def main():
    """Run the example."""
    print("Example: Getting Documents from a Qdrant Collection")
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
        
        # Add some example documents to retrieve
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
                "id": "numeric_id_123",
                "vector": [0.4, 0.5, 0.6, 0.7],
                "payload": {
                    "text": "Document with numeric ID",
                    "category": "test",
                    "numeric_id": 123
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
        
        # Method 1: Get documents by ID list
        print("\nMethod 1: Get documents by ID list")
        print("---------------------------------")
        
        # IDs to retrieve
        ids_to_get = ["doc1", "doc3"]
        ids_str = ",".join(ids_to_get)
        
        print(f"Retrieving documents with IDs: {ids_str}")
        
        # Get documents by ID
        get_by_id_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "get",
                "--collection", collection_name,
                "--ids", ids_str
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nRetrieved documents:")
        print(get_by_id_result.stdout)
        
        # Method 2: Get documents by ID file
        print("\nMethod 2: Get documents by ID file")
        print("----------------------------------")
        
        # Create a temporary file with IDs
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as id_file:
            id_file_path = id_file.name
            id_file.write("doc2\nnumeric_id_123\n")  # One ID per line
        
        print(f"Created temporary ID file: {id_file_path}")
        print("File contents (one ID per line):")
        print("doc2")
        print("numeric_id_123")
        
        # Get documents by ID file
        get_by_file_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "get",
                "--collection", collection_name,
                "--file", id_file_path,
                "--with-vectors"  # Include vectors in the output
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nRetrieved documents (with vectors):")
        print(get_by_file_result.stdout)
        
        # Method 3: Get documents with filter
        print("\nMethod 3: Get documents with filter")
        print("----------------------------------")
        
        # Create a filter for fruit category
        filter_json = json.dumps({
            "must": [
                {
                    "key": "category",
                    "match": {
                        "value": "fruit"
                    }
                }
            ]
        })
        
        print(f"Filter for fruit category: {filter_json}")
        
        # Get documents by filter
        get_by_filter_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "get",
                "--collection", collection_name,
                "--filter-json", filter_json
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nRetrieved documents (with filter):")
        print(get_by_filter_result.stdout)
        
        # Method 4: Export to different formats
        print("\nMethod 4: Export to different formats")
        print("-----------------------------------")
        
        # Create a temporary file for CSV export
        csv_file_path = os.path.join(tempfile.gettempdir(), "qdrant_docs.csv")
        
        # Get documents and export as CSV
        get_csv_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "get",
                "--collection", collection_name,
                "--ids", "doc1,doc2",
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
        
        # Show additional options
        print("\nAdditional options for get command:")
        print("- Use --with-vectors to include vectors in the output")
        print("- Use --with-payload/--without-payload to control payload inclusion")
        print("- Use --format to specify output format (json, yaml, csv, table)")
        print("- Use --output to save results to a file")
        
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
