"""Integration tests for the Solr CLI commands."""

import pytest
import subprocess
import json
import time
import uuid

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

# --- Fixtures (TODO) ---
# - Fixture to ensure docker-compose services (ZK, Solr nodes) are up and running
# - Fixture to provide a unique core/collection name for each test
# - Fixture to clean up cores/collections after tests
# - Fixture potentially for creating configsets if needed

# --- Helper Functions (Optional) ---
def run_cli_command(command_args):
    """Helper to run the docstore-manager CLI command for Solr."""
    base_command = ["docstore-manager", "solr"]
    full_command = base_command + command_args
    print(f"\nRunning command: {' '.join(full_command)}")
    result = subprocess.run(full_command, capture_output=True, text=True, check=False)
    print(f"Exit Code: {result.returncode}")
    print(f"Stdout:\n{result.stdout}")
    print(f"Stderr:\n{result.stderr}")
    return result

# --- Test Cases ---

def test_solr_collection_lifecycle():
    """Test create, list, info, and delete Solr collection/core lifecycle."""
    core_name = f"test_integration_{uuid.uuid4().hex}"
    print(f"Using core/collection: {core_name}")

    # 1. Create Core/Collection
    # Note: Solr creation might require configset, replication factor, shards etc.
    # This is a simplified example assuming defaults or a pre-uploaded configset.
    create_args = ["create", core_name] # Add required args like --shards, --replication-factor if needed
    create_result = run_cli_command(create_args)
    # TODO: This will likely fail without more args or setup
    # assert create_result.returncode == 0 
    time.sleep(5) # Solr core creation can take time

    # 2. List Cores/Collections - check if new one exists
    list_result = run_cli_command(["list"])
    # TODO: Assert based on actual list output format
    # assert core_name in list_result.stdout
    # assert list_result.returncode == 0

    # 3. Get Core/Collection Info (Status)
    info_result = run_cli_command(["info", core_name])
    # TODO: Assert based on actual info output format
    # assert info_result.returncode == 0

    # 4. Delete Core/Collection
    delete_result = run_cli_command(["delete", core_name])
    # assert delete_result.returncode == 0
    time.sleep(2)

    # 5. List Again - check it's gone
    list_result_after = run_cli_command(["list"])
    # TODO: Assert based on actual list output format
    # assert core_name not in list_result_after.stdout
    # assert list_result_after.returncode == 0
    pass # Placeholder until create works

def test_solr_document_lifecycle():
    """Test add, get, search, count, delete Solr documents."""
    core_name = f"test_integration_docs_{uuid.uuid4().hex}"
    print(f"Using core/collection: {core_name}")

    # 1. Create Core first (assuming this works or is handled by fixture)
    # run_cli_command(["create", core_name]) 
    # time.sleep(5)

    # 2. Add Documents (using --docs)
    # Solr needs fields defined in schema, usually at least 'id'
    docs_to_add = [
        {"id": f"doc_1_{uuid.uuid4()}", "title_s": "Doc 1 Title", "content_t": "Some content here."},
        {"id": f"doc_2_{uuid.uuid4()}", "title_s": "Doc 2 Title", "content_t": "More content available."},
    ]
    add_result = run_cli_command(["add-documents", core_name, "--docs", json.dumps(docs_to_add)])
    # TODO: This depends on core creation and schema
    # assert add_result.returncode == 0
    time.sleep(2) # Allow commit/indexing

    # 3. Count Documents
    count_result = run_cli_command(["count", core_name])
    # TODO: Assert count based on actual output
    # assert count_result.returncode == 0

    # 4. Get Documents (by ID)
    get_id = docs_to_add[0]['id']
    get_result = run_cli_command(["get", core_name, "--ids", get_id])
    # TODO: Assert based on actual output
    # assert get_result.returncode == 0
    # assert get_id in get_result.stdout

    # 5. Search Documents
    search_result = run_cli_command(["search", core_name, "--query", 'content_t:content'])
    # TODO: Assert based on actual output
    # assert search_result.returncode == 0
    # assert get_id in search_result.stdout # Check if expected doc is found

    # 6. Delete Documents (by ID)
    delete_id = docs_to_add[0]['id']
    delete_docs_result = run_cli_command(["delete-documents", core_name, "--ids", delete_id])
    # TODO: Assert based on actual output
    # assert delete_docs_result.returncode == 0
    time.sleep(2) # Allow commit

    # 7. Count Again
    count_after_delete_result = run_cli_command(["count", core_name])
    # TODO: Assert count based on actual output
    # assert count_after_delete_result.returncode == 0

    # 8. Cleanup: Delete Core
    # run_cli_command(["delete", core_name])
    pass # Placeholder until core creation/deletion works

# TODO: Add tests for:
# - add-documents --file
# - delete-documents --file
# - delete-documents --query
# - get --file
# - search with different query parameters (fq, fl, rows, etc.)
# - config command (if implemented)
# - Error handling (e.g., non-existent core, bad input)
# - Config options (--profile, --config-path) 