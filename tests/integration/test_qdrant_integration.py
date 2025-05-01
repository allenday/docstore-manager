"""Integration tests for the Qdrant CLI commands."""

import pytest
import subprocess
import json
import time
import uuid

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

# --- Fixtures (TODO) ---
# - Fixture to ensure docker-compose services are up
# - Fixture to provide a unique collection name for each test
# - Fixture to clean up collections after tests

# --- Helper Functions (Optional) ---
def run_cli_command(command_args):
    """Helper to run the docstore-manager CLI command."""
    base_command = ["docstore-manager", "qdrant"]
    full_command = base_command + command_args
    print(f"\nRunning command: {' '.join(full_command)}")
    result = subprocess.run(full_command, capture_output=True, text=True, check=False)
    print(f"Exit Code: {result.returncode}")
    print(f"Stdout:\n{result.stdout}")
    print(f"Stderr:\n{result.stderr}")
    return result

# --- Test Cases ---

def test_qdrant_collection_lifecycle():
    """Test create, list, info, and delete collection lifecycle."""
    collection_name = f"test-integration-{uuid.uuid4()}"
    dimension = 4 # Small dimension for testing
    print(f"Using collection: {collection_name}")

    # 1. Create Collection
    create_args = ["create", collection_name, "--dimension", str(dimension)]
    create_result = run_cli_command(create_args)
    assert create_result.returncode == 0
    # Add assertion based on stdout or API check

    # Give Qdrant a moment
    time.sleep(1)

    # 2. List Collections - check if new one exists
    list_result = run_cli_command(["list"])
    assert list_result.returncode == 0
    assert collection_name in list_result.stdout

    # 3. Get Collection Info
    info_result = run_cli_command(["info", collection_name])
    assert info_result.returncode == 0
    # Add assertion based on stdout (e.g., check dimension)
    assert f'"name": "{collection_name}"' in info_result.stdout # Basic check
    assert f'"vector_size": {dimension}' in info_result.stdout

    # 4. Delete Collection
    delete_result = run_cli_command(["delete", collection_name])
    assert delete_result.returncode == 0

    # 5. List Collections Again - check it's gone
    list_result_after = run_cli_command(["list"])
    assert list_result_after.returncode == 0
    assert collection_name not in list_result_after.stdout

def test_qdrant_document_lifecycle():
    """Test add, get, search, scroll, count, delete documents."""
    collection_name = f"test-integration-docs-{uuid.uuid4()}"
    dimension = 2
    print(f"Using collection: {collection_name}")

    # 1. Create Collection first
    run_cli_command(["create", collection_name, "--dimension", str(dimension)])
    time.sleep(1)

    # 2. Add Documents (using --docs)
    docs_to_add = [
        {"id": 1, "vector": [0.1, 0.2], "payload": {"name": "doc1"}},
        {"id": "doc-2", "vector": [0.3, 0.4], "payload": {"name": "doc2"}},
        {"id": str(uuid.uuid4()), "vector": [0.5, 0.6], "payload": {"name": "doc3"}}
    ]
    add_result = run_cli_command(["add-documents", collection_name, "--docs", json.dumps(docs_to_add)])
    assert add_result.returncode == 0
    # TODO: Add assertion based on stdout/API check
    time.sleep(1) # Allow indexing

    # 3. Count Documents
    count_result = run_cli_command(["count", collection_name])
    assert count_result.returncode == 0
    # TODO: Assert count is 3 based on stdout
    assert '"count": 3' in count_result.stdout

    # 4. Get Documents (by ID)
    get_ids = "1,doc-2"
    get_result = run_cli_command(["get", collection_name, "--ids", get_ids, "--with-payload"])
    assert get_result.returncode == 0
    # TODO: Assert stdout contains data for IDs 1 and doc-2
    assert '"id": 1' in get_result.stdout
    assert '"id": "doc-2"' in get_result.stdout

    # 5. Search Documents
    query_vector = [0.11, 0.21] # Close to doc1
    search_result = run_cli_command(["search", collection_name, "--query", json.dumps({"vector": query_vector}), "--limit", "1"])
    assert search_result.returncode == 0
    # TODO: Assert stdout shows doc1 as the top result
    assert '"id": 1' in search_result.stdout

    # 6. Scroll Documents
    scroll_result = run_cli_command(["scroll", collection_name, "--batch-size", "2"])
    assert scroll_result.returncode == 0
    # TODO: Assert stdout contains data for (likely) 2 documents

    # 7. Delete Documents (by ID)
    delete_ids = "1,doc-2"
    delete_docs_result = run_cli_command(["delete-documents", collection_name, "--ids", delete_ids])
    assert delete_docs_result.returncode == 0
    # TODO: Assert based on stdout/API check
    time.sleep(1)

    # 8. Count Again
    count_after_delete_result = run_cli_command(["count", collection_name])
    assert count_after_delete_result.returncode == 0
    # TODO: Assert count is 1
    assert '"count": 1' in count_after_delete_result.stdout

    # 9. Cleanup: Delete Collection
    run_cli_command(["delete", collection_name])

# TODO: Add tests for:
# - add-documents --file
# - delete-documents --file
# - delete-documents --filter (requires more complex setup)
# - get --file
# - scroll with filter/offset
# - search with different query types (filter, etc.)
# - Error handling (e.g., non-existent collection, bad input)
# - Config options (--profile, --config-path) 