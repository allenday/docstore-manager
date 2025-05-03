#!/usr/bin/env python3
"""
Example: Deleting a Solr Collection

This example demonstrates how to delete a collection in Solr
using the docstore-manager CLI tool.
"""
import subprocess
import sys
import json

def main():
    """Run the example."""
    print("Example: Deleting a Solr Collection")
    print("===============================")
    
    # Define collection name
    collection_name = "example_collection"
    
    print(f"Deleting collection: '{collection_name}'")
    
    try:
        # First, check if the collection exists
        list_result = subprocess.run(
            ["docstore-manager", "solr", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        collection_exists = False
        try:
            collections = json.loads(list_result.stdout)
            if collection_name in collections:
                collection_exists = True
                print(f"\nCollection '{collection_name}' exists and will be deleted.")
            else:
                print(f"\nCollection '{collection_name}' does not exist. Creating it first...")
                
                # Create the collection
                create_result = subprocess.run(
                    [
                        "docstore-manager", "solr", "create",
                        collection_name,
                        "--num-shards", "1",
                        "--replication-factor", "1",
                        "--configset", "basic_configs"
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print("Collection created.")
                collection_exists = True
        except json.JSONDecodeError:
            print("Warning: Could not parse collection list. Proceeding anyway.")
        
        if not collection_exists:
            print(f"Unable to verify if collection '{collection_name}' exists. Proceeding anyway.")
        
        # Delete the collection
        print("\nDeleting collection...")
        delete_result = subprocess.run(
            [
                "docstore-manager", "solr", "delete",
                collection_name,
                "--yes"  # Skip confirmation prompt
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nCommand output:")
        print(delete_result.stdout)
        
        # Verify the collection is gone
        print("\nVerifying collection was deleted...")
        verify_result = subprocess.run(
            ["docstore-manager", "solr", "list"],
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
        
        # Show additional information
        print("\nAdditional Information:")
        print("----------------------")
        print("1. Deletion Process:")
        print("   - Solr removes the collection's data and metadata")
        print("   - The operation is irreversible")
        print("   - Configsets used by the collection remain available")
        
        print("\n2. Safety Considerations:")
        print("   - Without the --yes flag, you will be prompted for confirmation")
        print("   - Consider backing up important data before deletion")
        print("   - For production systems, consider using collection aliases for zero-downtime transitions")
        
        print("\n3. Command Variations:")
        print("   docstore-manager solr delete my_collection")
        print("   # Without --yes, you'll be prompted for confirmation")
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        print("\nPossible issues:")
        print("- Solr instance is not running")
        print("- Connection configuration is incorrect")
        print("- Collection is in use or locked")
        print("- Insufficient permissions")
        print("\nMake sure Solr is running and properly configured in your docstore-manager config file.")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: docstore-manager command not found. Make sure it's installed and in your PATH.")
        print("Install with: pip install docstore-manager")
        sys.exit(1)

if __name__ == "__main__":
    main()
