#!/usr/bin/env python3
"""
Example: Getting Solr Collection Information

This example demonstrates how to retrieve detailed information about
a Solr collection using the docstore-manager CLI tool.
"""
import subprocess
import sys
import json

def main():
    """Run the example."""
    print("Example: Getting Solr Collection Information")
    print("========================================")
    
    # Define collection name
    collection_name = "example_collection"
    
    print(f"Getting information for collection: '{collection_name}'")
    
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
        
        # Get collection information
        print("\nRetrieving collection information...")
        info_result = subprocess.run(
            [
                "docstore-manager", "solr", "info",
                collection_name
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
        print("- Collection configuration (shards, replicas)")
        print("- Router information")
        print("- Replication factor")
        print("- Max shards per node")
        print("- Auto-add replicas setting")
        print("- Collection state")
        print("- Schema information (if available)")
        
        # Show additional information
        print("\nAdditional Information:")
        print("----------------------")
        print("1. Schema Information:")
        print("   The schema defines field types, fields, and other indexing directives.")
        print("   It controls how Solr processes and indexes documents.")
        
        print("\n2. Config Information:")
        print("   The config includes request handlers, search components, and other settings.")
        print("   It controls how Solr processes queries and returns results.")
        
        print("\n3. Aliases:")
        print("   Collection aliases allow you to use a single name to refer to multiple collections.")
        print("   Useful for collection rotation and zero-downtime schema changes.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        print("\nPossible issues:")
        print("- Solr instance is not running")
        print("- Connection configuration is incorrect")
        print("- Collection does not exist")
        print("\nMake sure Solr is running and properly configured in your docstore-manager config file.")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: docstore-manager command not found. Make sure it's installed and in your PATH.")
        print("Install with: pip install docstore-manager")
        sys.exit(1)

if __name__ == "__main__":
    main()
