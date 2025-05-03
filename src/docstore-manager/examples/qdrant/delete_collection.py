#!/usr/bin/env python3
"""
Example: Deleting a Qdrant Collection

This example demonstrates how to delete a collection in Qdrant
using the docstore-manager CLI tool.
"""
import subprocess
import sys
import json

def main():
    """Run the example."""
    print("Example: Deleting a Qdrant Collection")
    print("===================================")
    
    # Define collection name
    collection_name = "example_collection"
    
    print(f"Deleting collection: '{collection_name}'")
    
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
            else:
                print(f"\nCollection '{collection_name}' exists and will be deleted.")
        except json.JSONDecodeError:
            print("Warning: Could not parse collection list. Proceeding anyway.")
        
        # Delete the collection
        print("\nDeleting collection...")
        delete_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "delete",
                "--collection", collection_name,
                "--yes"  # Skip confirmation prompt
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("Collection deleted successfully!")
        print("\nCommand output:")
        print(delete_result.stdout)
        
        # Verify the collection is gone
        print("\nVerifying collection was deleted...")
        verify_result = subprocess.run(
            ["docstore-manager", "qdrant", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        try:
            collections_after = json.loads(verify_result.stdout)
            if collection_name not in collections_after:
                print(f"Confirmed: Collection '{collection_name}' no longer exists.")
            else:
                print(f"Warning: Collection '{collection_name}' still appears in the list.")
        except json.JSONDecodeError:
            print("Warning: Could not parse collection list for verification.")
        
        # Show the command without the --yes flag
        print("\nNote: Without the --yes flag, you will be prompted for confirmation:")
        print(f"docstore-manager qdrant delete --collection {collection_name}")
        
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
