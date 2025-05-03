#!/usr/bin/env python3
"""
Example: Creating a Solr Collection

This example demonstrates how to create a new collection in Solr
using the docstore-manager CLI tool.
"""
import subprocess
import sys
import json

def main():
    """Run the example."""
    print("Example: Creating a Solr Collection")
    print("================================")
    
    # Define collection parameters
    collection_name = "example_collection"
    num_shards = 1
    replication_factor = 1
    configset = "basic_configs"  # Default Solr configset
    
    print(f"Creating collection '{collection_name}' with the following settings:")
    print(f"- Number of shards: {num_shards}")
    print(f"- Replication factor: {replication_factor}")
    print(f"- ConfigSet: {configset}")
    
    try:
        # First, check if the collection already exists
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
                print(f"\nCollection '{collection_name}' already exists. Deleting it first...")
                
                # Delete the existing collection
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
                print("Existing collection deleted.")
        except json.JSONDecodeError:
            print("Warning: Could not parse collection list. Proceeding anyway.")
        
        # Create the collection with specified parameters
        print("\nCreating new collection...")
        create_result = subprocess.run(
            [
                "docstore-manager", "solr", "create",
                collection_name,
                "--num-shards", str(num_shards),
                "--replication-factor", str(replication_factor),
                "--configset", configset
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nCommand output:")
        print(create_result.stdout)
        
        # Verify the collection was created
        verify_result = subprocess.run(
            ["docstore-manager", "solr", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        try:
            collections_after = json.loads(verify_result.stdout)
            if collection_name in collections_after:
                print(f"\nSuccess! Collection '{collection_name}' has been created.")
            else:
                print(f"\nWarning: Collection '{collection_name}' does not appear in the list after creation.")
        except json.JSONDecodeError:
            print("\nWarning: Could not parse collection list for verification.")
        
        # Show additional information
        print("\nAdditional Information:")
        print("----------------------")
        print("1. ConfigSets:")
        print("   - 'basic_configs': Default minimal configuration")
        print("   - 'data_driven_schema_configs': Schema that adapts based on data")
        print("   - 'sample_techproducts_configs': Example config with many features enabled")
        print("   - Custom configsets can be uploaded to Solr")
        
        print("\n2. Collection Parameters:")
        print("   - num_shards: Number of logical partitions for the collection")
        print("   - replication_factor: Number of copies of each document")
        print("   - maxShardsPerNode: Maximum shards per node (default: unlimited)")
        print("   - router.name: 'compositeId' (default) or 'implicit'")
        
        print("\n3. Command Variations:")
        print("   docstore-manager solr create my_collection --configset data_driven_schema_configs")
        print("   docstore-manager solr create my_collection --num-shards 2 --replication-factor 2")
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        print("\nPossible issues:")
        print("- Solr instance is not running")
        print("- Connection configuration is incorrect")
        print("- Insufficient permissions")
        print("- Invalid configset name")
        print("\nMake sure Solr is running and properly configured in your docstore-manager config file.")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: docstore-manager command not found. Make sure it's installed and in your PATH.")
        print("Install with: pip install docstore-manager")
        sys.exit(1)

if __name__ == "__main__":
    main()
