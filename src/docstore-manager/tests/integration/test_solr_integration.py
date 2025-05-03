"""Integration tests for the Solr CLI commands."""

import pytest
import subprocess
import json
import time
import uuid
import os
import sys
import logging
from pathlib import Path

# Mark all tests in this module as integration tests
_integration_mark = pytest.mark.integration

# --- Skip integration tests by default --- 
# Require RUN_INTEGRATION_TESTS=true environment variable to run
RUN_INTEGRATION_ENV_VAR = "RUN_INTEGRATION_TESTS"
SKIP_INTEGRATION = os.environ.get(RUN_INTEGRATION_ENV_VAR, "false").lower() != "true"
REASON_TO_SKIP = f"Skipping integration tests. Set {RUN_INTEGRATION_ENV_VAR}=true to enable."

# Apply the skip condition to all tests in this module
# Ensure pytestmark is treated as a list
_skip_mark = pytest.mark.skipif(SKIP_INTEGRATION, reason=REASON_TO_SKIP)
pytestmark = [_integration_mark, _skip_mark]

# Setup logger for this test module
logger = logging.getLogger(__name__)

# Define paths relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent 
CONFIG_FILE = BASE_DIR / "tests" / "integration" / "config.yaml"
FIXTURES_DIR = BASE_DIR / "tests" / "fixtures"
SOLR_DOC_FILE = FIXTURES_DIR / "test_solr_docs.jsonl"

# Revert to assuming a relative path from BASE_DIR for the virtual env
VENV_BIN_PATH = BASE_DIR / ".venv" / "bin"
EXECUTABLE_PATH = VENV_BIN_PATH / "docstore-manager"

assert EXECUTABLE_PATH.exists(), (
    f"Executable not found at expected path: {EXECUTABLE_PATH}\n"
    f"Ensure the virtual environment exists at {BASE_DIR / '.venv'} "
    f"and the package is installed correctly ('pip install -e .')."
)

# Helper Functions 
def run_cli_command(command_args, expected_exit_code=0):
    """Helper to run the docstore-manager CLI command.
    Asserts the exit code matches expected_exit_code.
    """
    # Use hardcoded relative executable path
    # Add --debug flag back to enable verbose logging from the subprocess
    base_command = [str(EXECUTABLE_PATH), "--debug", "--config", str(CONFIG_FILE), "--profile", "default"]
    # Insert 'solr' subgroup before specific command args
    # Note: Need to check if first arg is already 'solr' from the test calls
    if command_args and command_args[0] == 'solr':
         full_command = base_command + command_args
    else:
         # If 'solr' is not passed, prepend it
         full_command = base_command + ['solr'] + command_args
    cmd_str = ' '.join(map(str, full_command))
    # Use logging instead of print for command info
    logger.info(f"---> Running command: {cmd_str}")
    
    result = subprocess.run(full_command, capture_output=True, text=True, check=False)
    logger.info(f"     Exit Code: {result.returncode} (Expected: {expected_exit_code})")
    if result.returncode != expected_exit_code:
        # Keep print for raw output on failure, but add logs
        logger.error(f"Command failed! Stdout:\n{result.stdout}")
        logger.error(f"Command failed! Stderr:\n{result.stderr}")
        print(f"     Stdout:\n{result.stdout}") # Keep raw print on error
        print(f"     Stderr:\n{result.stderr}") # Keep raw print on error
    assert result.returncode == expected_exit_code
    return result

# --- Test Cases ---

# Comment out old collection lifecycle test as it's covered implicitly
# def test_solr_collection_lifecycle():
#     # ... (old code) ...
#     pass

def test_solr_document_lifecycle():
    """Test add, search, remove Solr documents via CLI."""
    # Use collection name from config for simplicity in this test
    # Ideally, use a unique name and manage its lifecycle, but requires more fixture setup
    # For now, assume 'test_solr' exists or will be created/overwritten.
    # collection_name = f"test_integration_docs_{uuid.uuid4().hex}"
    collection_name = "test_solr" # Matching default profile in config.yaml
    logger.info(f"---> Testing document lifecycle for Solr collection: {collection_name}")

    # 1. Ensure collection exists (create/overwrite)
    logger.info(f"--- Step 1: Creating/overwriting collection '{collection_name}'...")
    run_cli_command(["solr", "create", collection_name, "--overwrite"])
    time.sleep(5) # Allow time for core creation

    # 2. Add Documents
    logger.info(f"--- Step 2: Adding documents from {SOLR_DOC_FILE}...")
    add_result = run_cli_command(["solr", "add-documents", "--doc", f"@{SOLR_DOC_FILE}"])
    assert "Successfully added/updated 3 documents" in add_result.stdout
    time.sleep(2) # Allow commit/indexing

    # 3. Search for all added documents
    logger.info("--- Step 3: Searching for all documents (*:*) to verify addition...")
    search_all_result = run_cli_command(["solr", "search", "-q", "*:*", "-fl", "id", "--limit", "10"])
    try:
        search_data = json.loads(search_all_result.stdout)
        assert isinstance(search_data, list)
        found_ids = {doc.get('id') for doc in search_data}
        expected_ids = {"solr_doc_1", "solr_doc_2", "solr_doc_3"}
        assert found_ids == expected_ids, f"Expected IDs {expected_ids}, but found {found_ids}"
        logger.info(f"     Verified all 3 documents exist.")
    except json.JSONDecodeError:
        pytest.fail(f"Search output was not valid JSON:\n{search_all_result.stdout}")
    except AssertionError as e:
         pytest.fail(f"Assertion failed during search verification: {e}\nSearch Output:\n{search_all_result.stdout}")

    # 4. Remove two documents by ID
    ids_to_remove = "solr_doc_1,solr_doc_2"
    logger.info(f"--- Step 4: Removing documents with IDs: {ids_to_remove}...")
    remove_result = run_cli_command(["solr", "remove-documents", "--ids", ids_to_remove])
    assert "Successfully deleted documents" in remove_result.stdout
    time.sleep(2) # Allow commit

    # 5. Search Again - check only remaining doc exists
    logger.info("--- Step 5: Searching again (*:*) to verify removal...")
    search_after_delete_result = run_cli_command(["solr", "search", "-q", "*:*", "-fl", "id"])
    try:
        search_data_after = json.loads(search_after_delete_result.stdout)
        assert isinstance(search_data_after, list)
        found_ids_after = {doc.get('id') for doc in search_data_after}
        expected_ids_after = {"solr_doc_3"}
        assert found_ids_after == expected_ids_after, f"Expected IDs {expected_ids_after}, but found {found_ids_after}"
        logger.info(f"     Verified only remaining document exists.")
    except json.JSONDecodeError:
        pytest.fail(f"Search output after delete was not valid JSON:\n{search_after_delete_result.stdout}")
    except AssertionError as e:
        pytest.fail(f"Assertion failed during search verification after delete: {e}\nSearch Output:\n{search_after_delete_result.stdout}")

    # 6. Cleanup: Delete Collection (Optional, but good practice)
    logger.info(f"--- Step 6: Cleaning up collection '{collection_name}'...")
    # run_cli_command(["solr", "delete", collection_name, "--yes"])
    logger.info(f"---> Test finished for {collection_name}")

# TODO: Add specific tests for --filter in search, remove by query, etc.

# TODO: Add tests for:
# - add-documents --file
# - delete-documents --file
# - delete-documents --query
# - get --file
# - search with different query parameters (fq, fl, rows, etc.)
# - config command (if implemented)
# - Error handling (e.g., non-existent core, bad input)
# - Config options (--profile, --config-path)
