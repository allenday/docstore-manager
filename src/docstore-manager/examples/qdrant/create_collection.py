#!/usr/bin/env python3
"""
Example: Creating a Qdrant Collection

This example demonstrates how to create a new collection in Qdrant
with custom settings using the docstore-manager CLI tool.
"""
import subprocess
import sys
import json

def main():
    """Run the example."""
    print("Example: Creating a Qdrant Collection")
    print("====================================")
    
    # Define collection parameters
    collection_name = "example_collection"
    vector_size = 384  # Dimension of vectors (e.g., for text embeddings)
    distance = "cosine"  # Distance metric: cosine, euclid, or dot
    
    print(f"Creating collection '{collection_name}' with the following settings:")
    print(f"- Vector size: {vector_size}")
    print(f"- Distance metric: {distance}")
    
    try:
        # First, check if the collection already exists
        list_result = subprocess.run(
            ["docstore-manager", "qdrant", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        try:
            collections = json.loads(list_result.stdout)
            if collection_name in collections:
                print(f"\nCollection '{collection_name}' already exists. Deleting it first...")
                
                # Delete the existing collection
                delete_result = subprocess.run(
                    ["docstore-manager", "qdrant", "delete", "--yes"],
                    env={"DOCSTORE_MANAGER_COLLECTION": collection_name},
                    capture_output=True,
                    text=True,
                    check=True
                )
                print("Existing collection deleted.")
        except json.JSONDecodeError:
            print("Warning: Could not parse collection list. Proceeding anyway.")
        
        # Create the collection with specified parameters
        print("\nCreating new collection...")
        create_result = subprocess.run(
            [
                "docstore-manager", "qdrant", "create",
                "--collection", collection_name,
                "--size", str(vector_size),
                "--distance", distance
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("Collection created successfully!")
        print("\nCommand output:")
        print(create_result.stdout)
        
        # Show how to create with additional parameters
        print("\nYou can also create collections with additional parameters:")
        print("docstore-manager qdrant create \\")
        print("  --collection my_collection \\")
        print("  --size 1536 \\")
        print("  --distance euclid \\")
        print("  --on-disk \\")
        print("  --hnsw-ef 128 \\")
        print("  --hnsw-m 16 \\")
        print("  --shards 2 \\")
        print("  --replication-factor 1")
        
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
