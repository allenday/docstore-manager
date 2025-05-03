#!/usr/bin/env python3
"""
Example: Listing Solr Collections

This example demonstrates how to list all collections in a Solr instance
using the docstore-manager CLI tool.
"""
import subprocess
import sys
import json

def main():
    """Run the example."""
    print("Example: Listing Solr Collections")
    print("===============================")
    
    try:
        # Run the docstore-manager command to list collections
        result = subprocess.run(
            ["docstore-manager", "solr", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Display the results
        print("\nCommand output:")
        print(result.stdout)
        
        # Try to parse the output as JSON
        try:
            collections = json.loads(result.stdout)
            
            # Display the results in a more readable format
            if collections:
                print(f"\nFound {len(collections)} collections:")
                for i, collection in enumerate(collections, 1):
                    print(f"{i}. {collection}")
            else:
                print("\nNo collections found.")
                print("\nPossible reasons:")
                print("- Solr instance is empty")
                print("- Solr instance is not running")
                print("- Connection configuration is incorrect")
                
            # Example of saving the output to a file
            print("\nYou can also save the output to a file:")
            print("docstore-manager solr list --output collections.json")
            
        except json.JSONDecodeError:
            print("\nOutput is not in JSON format. Raw output shown above.")
    
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        print("\nPossible issues:")
        print("- Solr instance is not running")
        print("- Connection configuration is incorrect")
        print("- docstore-manager is not configured for Solr")
        print("\nMake sure Solr is running and properly configured in your docstore-manager config file.")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: docstore-manager command not found. Make sure it's installed and in your PATH.")
        print("Install with: pip install docstore-manager")
        sys.exit(1)

    # Show configuration information
    print("\nConfiguration Information:")
    print("-------------------------")
    print("The Solr connection details are read from your configuration file, typically located at:")
    print("- Linux/macOS: ~/.config/docstore-manager/config.yaml")
    print("- Windows: %APPDATA%\\docstore-manager\\config.yaml")
    print("\nExample configuration for Solr:")
    print("""
default:
  connection:
    type: solr
    collection: my-collection
  
  solr:
    url: http://localhost:8983/solr
    username: ""
    password: ""
    """)
    
    print("\nYou can also view your current configuration with:")
    print("docstore-manager solr config")

if __name__ == "__main__":
    main()
