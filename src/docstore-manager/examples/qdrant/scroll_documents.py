#!/usr/bin/env python3
"""
Example: Scrolling Through Documents in a Qdrant Collection

This example demonstrates how to paginate through documents in a Qdrant collection
using the scroll command with the docstore-manager CLI tool.
"""
import subprocess
import sys
import json
import os
import tempfile

def main():
    """Run the example."""
    print("Example: Scrolling Through Documents in a Qdrant Collection")
    print("====================================================")
    
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
        
        # Add some example documents to scroll through
        print("\nAdding example documents to the collection...")
        documents = []
        
        # Create 20 documents for pagination example
        for i in range(1, 21):
            # Alternate between categories
            category = "product" if i % 2 == 0 else "service"
            # Cycle through colors
            colors = ["red", "blue", "green", "yellow"]
            color = colors[i % 4]
            
            documents.append({
                "id": f"doc{i}",
                "vector": [i/20, (i+1)/20, (i+2)/20, (i+3)/20],  # Simple vector pattern
                "payload": {
                    "title": f"Example document {i}",
                    "category": category,
                    "color": color,
                    "price": round(10 + i * 0.5, 2),
                    "index": i
                }
            })
        
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
        
        # Method 1: Basic scrolling with limit
        print("\nMethod 1: Basic scrolling with limit")
        print("---------------------------------")
        
        # First page (limit = 5)
        print("\nFetching first page (5 documents)...")
        scroll_page1_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "scroll",
                "--collection", collection_name,
                "--limit", "5"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the result to get the next offset
        try:
            page1_data = json.loads(scroll_page1_result.stdout)
            if page1_data and len(page1_data) > 0:
                # Get the ID of the last document for offset
                next_offset = page1_data[-1].get("id")
                print(f"\nFirst page results (5 documents):")
                print(f"Retrieved {len(page1_data)} documents")
                print(f"Next offset: {next_offset}")
                
                # Second page using the offset
                print("\nFetching second page (5 more documents)...")
                scroll_page2_result = subprocess.run(
                    [
                        "docstore-manager", "qdrant", "scroll",
                        "--collection", collection_name,
                        "--limit", "5",
                        "--offset", next_offset
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Parse the second page result
                try:
                    page2_data = json.loads(scroll_page2_result.stdout)
                    print(f"\nSecond page results (5 documents):")
                    print(f"Retrieved {len(page2_data)} documents")
                    if page2_data and len(page2_data) > 0:
                        next_offset2 = page2_data[-1].get("id")
                        print(f"Next offset: {next_offset2}")
                except json.JSONDecodeError:
                    print("Warning: Could not parse second page results.")
            else:
                print("No documents found in first page.")
        except json.JSONDecodeError:
            print("Warning: Could not parse first page results.")
        
        # Method 2: Scrolling with filter
        print("\nMethod 2: Scrolling with filter")
        print("-----------------------------")
        
        # Create a filter for product category
        filter_json = json.dumps({
            "must": [
                {
                    "key": "category",
                    "match": {
                        "value": "product"
                    }
                }
            ]
        })
        
        print(f"Filter for product category: {filter_json}")
        
        # First page with filter
        print("\nFetching first page of products (3 documents)...")
        scroll_filtered_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "scroll",
                "--collection", collection_name,
                "--limit", "3",
                "--filter-json", filter_json
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nFiltered scroll results (products only):")
        print(scroll_filtered_result.stdout)
        
        # Method 3: Scrolling with vectors included
        print("\nMethod 3: Scrolling with vectors included")
        print("---------------------------------------")
        
        # Scroll with vectors
        print("\nFetching documents with vectors included...")
        scroll_with_vectors_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "scroll",
                "--collection", collection_name,
                "--limit", "2",
                "--with-vectors"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nScroll results with vectors:")
        print(scroll_with_vectors_result.stdout)
        
        # Clean up the temporary file
        print(f"\nCleaning up temporary file...")
        os.unlink(temp_file_path)
        print("Temporary file deleted.")
        
        # Show additional information
        print("\nThe scroll command is useful for:")
        print("- Paginating through large collections")
        print("- Exporting all documents in batches")
        print("- Iterating through filtered subsets of documents")
        print("- Processing documents in manageable chunks")
        
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
