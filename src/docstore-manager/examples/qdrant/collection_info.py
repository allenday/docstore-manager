#!/usr/bin/env python3
"""
Example: Getting Qdrant Collection Information

This example demonstrates how to retrieve detailed information about
a Qdrant collection using the docstore-manager CLI tool.
"""
import subprocess
import sys
import json

def main():
    """Run the example."""
    print("Example: Getting Qdrant Collection Information")
    print("============================================")
    
    # Define collection name
    collection_name = "example_collection"
    
    print(f"Getting information for collection: '{collection_name}'")
    
    try:
        # First, check if the collection exists
        list_result = subprocess.run(
            ["docstore-manager", "qdrant", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        try:
            collections = json.loads(list_result.stdout)
            if collection_name not in collections:
                print(f"\nCollection '{collection_name}' does not exist. Creating it first...")
                
                # Create the collection
                create_result = subprocess.run(
                    [
                        "docstore-manager", "qdrant", "create",
                        "--collection", collection_name,
                        "--size", "384",
                        "--distance", "cosine"
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print("Collection created.")
        except json.JSONDecodeError:
            print("Warning: Could not parse collection list. Proceeding anyway.")
        
        # Get collection information
        print("\nRetrieving collection information...")
        info_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "info",
                "--collection", collection_name
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nCollection Information:")
        print("----------------------")
        print(info_result.stdout)
        
        # Explain the output
        print("\nThe output includes:")
        print("- Vector configuration (size, distance metric)")
        print("- Storage details (on-disk vs in-memory)")
        print("- HNSW index parameters")
        print("- Quantization settings (if enabled)")
        print("- Payload schema and indexed fields")
        print("- Collection status and statistics")
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: docstore-manager command not found. Make sure it's installed and in your PATH.")
        print("Install with: pip install docstore-manager")
        sys.exit(1)

if __name__ == "__main__":
    main()
