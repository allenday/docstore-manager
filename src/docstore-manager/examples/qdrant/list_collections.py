#!/usr/bin/env python3
"""
Example: Listing Qdrant Collections

This example demonstrates how to list all collections in a Qdrant instance
using the docstore-manager CLI tool.
"""
import subprocess
import json
import sys

def main():
    """Run the example."""
    print("Example: Listing Qdrant Collections")
    print("===================================")
    
    try:
        # Run the docstore-manager command to list collections
        result = subprocess.run(
            ["docstore-manager", "qdrant", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the JSON output
        try:
            collections = json.loads(result.stdout)
            
            # Display the results
            if collections:
                print(f"\nFound {len(collections)} collections:")
                for i, collection in enumerate(collections, 1):
                    print(f"{i}. {collection}")
            else:
                print("\nNo collections found.")
                
            # Example of saving the output to a file
            print("\nYou can also save the output to a file:")
            print("docstore-manager qdrant list --output collections.json")
            
        except json.JSONDecodeError:
            print("Error parsing output. Raw output:")
            print(result.stdout)
    
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
