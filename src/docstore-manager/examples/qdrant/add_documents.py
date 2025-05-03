#!/usr/bin/env python3
"""
Example: Adding Documents to a Qdrant Collection

This example demonstrates how to add documents to a Qdrant collection
using the docstore-manager CLI tool, with both file-based and direct JSON input.
"""
import subprocess
import sys
import json
import os
import tempfile

def main():
    """Run the example."""
    print("Example: Adding Documents to a Qdrant Collection")
    print("============================================")
    
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
        
        # Prepare example documents
        print("\nPreparing example documents...")
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
            }
        ]
        
        # Method 1: Add documents from a file
        print("\nMethod 1: Adding documents from a file")
        print("--------------------------------------")
        
        # Create a temporary JSONL file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as temp_file:
            temp_file_path = temp_file.name
            for doc in documents:
                temp_file.write(json.dumps(doc) + '\n')
        
        print(f"Created temporary JSONL file: {temp_file_path}")
        print("File contents (JSONL format - one JSON object per line):")
        for i, doc in enumerate(documents):
            print(f"Line {i+1}: {json.dumps(doc)}")
        
        # Add documents from the file
        print("\nAdding documents from file...")
        add_file_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "add-documents",
                "--collection", collection_name,
                "--file", temp_file_path
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("Documents added successfully from file!")
        print("\nCommand output:")
        print(add_file_result.stdout)
        
        # Method 2: Add documents directly with JSON string
        print("\nMethod 2: Adding documents with JSON string")
        print("------------------------------------------")
        
        # Create new documents with different IDs
        direct_documents = [
            {
                "id": "direct1",
                "vector": [0.5, 0.6, 0.7, 0.8],
                "payload": {
                    "text": "Direct document 1",
                    "category": "direct",
                    "tags": ["json", "direct"]
                }
            },
            {
                "id": "direct2",
                "vector": [0.6, 0.7, 0.8, 0.9],
                "payload": {
                    "text": "Direct document 2",
                    "category": "direct",
                    "tags": ["json", "string"]
                }
            }
        ]
        
        # Convert to JSON string
        docs_json = json.dumps(direct_documents)
        print(f"JSON string for direct addition: {docs_json}")
        
        # Add documents directly
        print("\nAdding documents directly...")
        add_direct_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "add-documents",
                "--collection", collection_name,
                "--docs", docs_json
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("Documents added successfully via JSON string!")
        print("\nCommand output:")
        print(add_direct_result.stdout)
        
        # Verify documents were added by counting
        print("\nVerifying documents were added by counting...")
        count_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "count",
                "--collection", collection_name
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nCount result:")
        print(count_result.stdout)
        
        # Clean up the temporary file
        print(f"\nCleaning up temporary file: {temp_file_path}")
        os.unlink(temp_file_path)
        print("Temporary file deleted.")
        
        # Show additional options
        print("\nAdditional options for add-documents command:")
        print("- Use --batch-size to control the number of documents per batch")
        print("- Specify a different collection with --collection")
        
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
