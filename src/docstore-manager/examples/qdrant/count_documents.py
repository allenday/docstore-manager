#!/usr/bin/env python3
"""
Example: Counting Documents in a Qdrant Collection

This example demonstrates how to count documents in a Qdrant collection,
both total count and filtered count, using the docstore-manager CLI tool.
"""
import subprocess
import sys
import json
import os
import tempfile

def main():
    """Run the example."""
    print("Example: Counting Documents in a Qdrant Collection")
    print("=============================================")
    
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
        
        # Add some example documents to count
        print("\nAdding example documents to the collection...")
        documents = [
            {
                "id": "fruit1",
                "vector": [0.1, 0.2, 0.3, 0.4],
                "payload": {
                    "text": "Red apple",
                    "category": "fruit",
                    "color": "red",
                    "price": 1.20
                }
            },
            {
                "id": "fruit2",
                "vector": [0.2, 0.3, 0.4, 0.5],
                "payload": {
                    "text": "Green apple",
                    "category": "fruit",
                    "color": "green",
                    "price": 1.50
                }
            },
            {
                "id": "fruit3",
                "vector": [0.3, 0.4, 0.5, 0.6],
                "payload": {
                    "text": "Yellow banana",
                    "category": "fruit",
                    "color": "yellow",
                    "price": 0.80
                }
            },
            {
                "id": "vegetable1",
                "vector": [0.4, 0.5, 0.6, 0.7],
                "payload": {
                    "text": "Orange carrot",
                    "category": "vegetable",
                    "color": "orange",
                    "price": 0.90
                }
            },
            {
                "id": "vegetable2",
                "vector": [0.5, 0.6, 0.7, 0.8],
                "payload": {
                    "text": "Red tomato",
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
        
        # Method 1: Count all documents
        print("\nMethod 1: Count all documents")
        print("----------------------------")
        
        # Count all documents
        count_all_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "count",
                "--collection", collection_name
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nTotal document count:")
        print(count_all_result.stdout)
        
        # Method 2: Count documents with filter
        print("\nMethod 2: Count documents with filter")
        print("-----------------------------------")
        
        # Create a filter for fruit category
        fruit_filter_json = json.dumps({
            "must": [
                {
                    "key": "category",
                    "match": {
                        "value": "fruit"
                    }
                }
            ]
        })
        
        print(f"Filter for fruit category: {fruit_filter_json}")
        
        # Count documents with fruit filter
        count_fruit_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "count",
                "--collection", collection_name,
                "--filter-json", fruit_filter_json
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nFruit document count:")
        print(count_fruit_result.stdout)
        
        # Method 3: Count documents with complex filter
        print("\nMethod 3: Count documents with complex filter")
        print("------------------------------------------")
        
        # Create a complex filter for red items with price > 1.00
        complex_filter_json = json.dumps({
            "must": [
                {
                    "key": "color",
                    "match": {
                        "value": "red"
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
        
        print(f"Complex filter for red items with price > 1.00: {complex_filter_json}")
        
        # Count documents with complex filter
        count_complex_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "count",
                "--collection", collection_name,
                "--filter-json", complex_filter_json
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nRed items with price > 1.00 count:")
        print(count_complex_result.stdout)
        
        # Clean up the temporary file
        print(f"\nCleaning up temporary file...")
        os.unlink(temp_file_path)
        print("Temporary file deleted.")
        
        # Show additional information
        print("\nThe count command is useful for:")
        print("- Verifying document additions or removals")
        print("- Checking how many documents match specific criteria")
        print("- Monitoring collection growth over time")
        print("- Validating filter expressions before using them in searches")
        
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
