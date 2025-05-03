#!/usr/bin/env python3
"""
Example: Removing Documents from a Qdrant Collection

This example demonstrates how to remove documents from a Qdrant collection
using the docstore-manager CLI tool, with both ID-based and filter-based removal.
"""
import subprocess
import sys
import json
import os
import tempfile

def main():
    """Run the example."""
    print("Example: Removing Documents from a Qdrant Collection")
    print("===============================================")
    
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
        
        # Add some example documents to work with
        print("\nAdding example documents to the collection...")
        documents = [
            {
                "id": "doc1",
                "vector": [0.1, 0.2, 0.3, 0.4],
                "payload": {
                    "text": "Example document 1",
                    "category": "example",
                    "tags": ["sample", "test"]
                }
            },
            {
                "id": "doc2",
                "vector": [0.2, 0.3, 0.4, 0.5],
                "payload": {
                    "text": "Example document 2",
                    "category": "example",
                    "tags": ["sample", "demo"]
                }
            },
            {
                "id": "doc3",
                "vector": [0.3, 0.4, 0.5, 0.6],
                "payload": {
                    "text": "Example document 3",
                    "category": "test",
                    "tags": ["demo", "test"]
                }
            },
            {
                "id": "doc4",
                "vector": [0.4, 0.5, 0.6, 0.7],
                "payload": {
                    "text": "Example document 4",
                    "category": "test",
                    "tags": ["sample", "test"]
                }
            },
            {
                "id": "doc5",
                "vector": [0.5, 0.6, 0.7, 0.8],
                "payload": {
                    "text": "Example document 5",
                    "category": "example",
                    "tags": ["demo", "example"]
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
        
        # Verify documents were added by counting
        count_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "count",
                "--collection", collection_name
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"Initial document count: {count_result.stdout.strip()}")
        
        # Method 1: Remove documents by ID list
        print("\nMethod 1: Removing documents by ID list")
        print("--------------------------------------")
        
        # IDs to remove
        ids_to_remove = ["doc1", "doc3"]
        ids_str = ",".join(ids_to_remove)
        
        print(f"Removing documents with IDs: {ids_str}")
        
        # Remove documents by ID
        remove_by_id_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "remove-documents",
                "--collection", collection_name,
                "--ids", ids_str
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("Documents removed successfully by ID!")
        print("\nCommand output:")
        print(remove_by_id_result.stdout)
        
        # Verify documents were removed by counting
        count_after_id_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "count",
                "--collection", collection_name
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"Document count after ID removal: {count_after_id_result.stdout.strip()}")
        
        # Method 2: Remove documents by ID file
        print("\nMethod 2: Removing documents by ID file")
        print("---------------------------------------")
        
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
                "docstore-manager", "qdrant", "remove-documents",
                "--collection", collection_name,
                "--file", id_file_path
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("Documents removed successfully by ID file!")
        print("\nCommand output:")
        print(remove_by_file_result.stdout)
        
        # Verify documents were removed by counting
        count_after_file_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "count",
                "--collection", collection_name
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"Document count after ID file removal: {count_after_file_result.stdout.strip()}")
        
        # Method 3: Remove documents by filter
        print("\nMethod 3: Removing documents by filter")
        print("-------------------------------------")
        
        # Create a filter to match documents with category "example"
        filter_json = json.dumps({
            "must": [
                {
                    "key": "category",
                    "match": {
                        "value": "example"
                    }
                }
            ]
        })
        
        print(f"Filter to remove documents with category 'example': {filter_json}")
        
        # Remove documents by filter
        remove_by_filter_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "remove-documents",
                "--collection", collection_name,
                "--filter-json", filter_json,
                "--yes"  # Skip confirmation prompt
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("Documents removed successfully by filter!")
        print("\nCommand output:")
        print(remove_by_filter_result.stdout)
        
        # Verify documents were removed by counting
        count_after_filter_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "count",
                "--collection", collection_name
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"Document count after filter removal: {count_after_filter_result.stdout.strip()}")
        
        # Clean up the temporary files
        print(f"\nCleaning up temporary files...")
        os.unlink(temp_file_path)
        os.unlink(id_file_path)
        print("Temporary files deleted.")
        
        # Show additional options
        print("\nAdditional options for remove-documents command:")
        print("- Use --batch-size to control the number of documents per batch")
        print("- Without --yes, you'll be prompted for confirmation when using filters")
        
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
