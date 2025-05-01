import sys
import logging

def main():
    """Top-level dispatcher for docstore-manager CLI."""
    
    # Basic logging setup until specific CLI takes over
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if len(sys.argv) < 2:
        print("Usage: docstore-manager <store_type> [options...]")
        print("  store_type: qdrant | solr")
        sys.exit(1)

    store_type = sys.argv[1]
    
    # Modify sys.argv for the specific CLI: remove the store_type argument
    # The specific CLI's parser will see argv[0] as the script name 
    # (e.g., 'qdrant-manager' or 'docstore-manager') and argv[1:] as its own args.
    original_script_name = sys.argv[0]
    specific_cli_args = [original_script_name] + sys.argv[2:]
    sys.argv = specific_cli_args # Overwrite sys.argv for the sub-CLI

    if store_type == "qdrant":
        try:
            from .qdrant.cli import QdrantCLI
            # We might need to adjust QdrantCLI's run method later if it relies
            # strictly on sys.argv being set before instantiation.
            # For now, assume its run() method uses the modified sys.argv.
            cli_instance = QdrantCLI()
            cli_instance.run() # run() should handle parsing the modified sys.argv
        except ImportError:
            logging.error("Failed to import Qdrant dependencies. Is qdrant-client installed?")
            sys.exit(1)
        except Exception as e:
            logging.error(f"An error occurred running the Qdrant manager: {e}", exc_info=True)
            sys.exit(1)
            
    elif store_type == "solr":
        try:
            from .solr.cli import SolrCLI
            # Similar assumption for SolrCLI
            cli_instance = SolrCLI()
            cli_instance.run()
        except ImportError:
             logging.error("Failed to import Solr dependencies. Is pysolr installed?")
             sys.exit(1)
        except Exception as e:
            logging.error(f"An error occurred running the Solr manager: {e}", exc_info=True)
            sys.exit(1)
            
    else:
        logging.error(f"Unknown store type: {store_type}")
        print("Valid store types are: qdrant, solr")
        sys.exit(1)

if __name__ == "__main__":
    main() 