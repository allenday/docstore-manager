"""Integration tests for the Qdrant CLI commands."""

import pytest
import subprocess
import json
import time
import uuid
import os
import sys 
import logging # Import logging
from pathlib import Path 
import yaml 

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
QDRANT_DOC_FILE = FIXTURES_DIR / "test_qdrant_docs.jsonl"

# Revert AGAIN to assuming a relative path from BASE_DIR for the virtual env
# as sys.prefix didn't work reliably either in this Homebrew env.
VENV_BIN_PATH = BASE_DIR / ".venv" / "bin"
EXECUTABLE_PATH = VENV_BIN_PATH / "docstore-manager"

assert EXECUTABLE_PATH.exists(), (
    f"Executable not found at expected path: {EXECUTABLE_PATH}\n"
    f"Ensure the virtual environment exists at {BASE_DIR / '.venv'} "
    f"and the package is installed correctly ('pip install -e .')."
)

# Define constants for paths and parameters
PROFILE = "default"
DOCS_PATH = FIXTURES_DIR / "test_qdrant_docs.jsonl"
IDS_PATH = FIXTURES_DIR / "test_qdrant_docs_ids.txt" # Keep track but might not use
COLLECTION_NAME = "test_qdrant_integration" # Use a dedicated name for tests
TEST_UUID = "40000000-0000-0000-0000-000000000000" # From the updated fixtures
DOC_ID_INT_1 = 1
DOC_ID_INT_2 = 2
DOC_ID_INT_3 = 3
VECTOR_DIM = 256 # Assuming from previous context

# Helper Functions ---
def run_cli_command(command_args, expected_exit_code=0):
    """Helper to run the docstore-manager CLI command.
    Asserts the exit code matches expected_exit_code.
    """
    # Use hardcoded relative executable path
    base_command = [str(EXECUTABLE_PATH), "--config", str(CONFIG_FILE), "--profile", "default"]
    # Insert 'qdrant' subgroup before specific command args
    full_command = base_command + ["qdrant"] + command_args 
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

def generate_vector_json(val: float, dim: int) -> str:
    """Generates a JSON string for a vector."""
    vector = [val] * dim
    return json.dumps(vector)

# --- Fixture to ensure config uses the test-specific collection name ---
@pytest.fixture(scope="module", autouse=True)
def patch_config_collection_name():
    """Patches the config file to use a test-specific collection name."""
    original_content = None
    if CONFIG_FILE.exists():
        original_content = CONFIG_FILE.read_text()
        try:
            # Use yaml.safe_load for YAML parsing
            config_data = yaml.safe_load(original_content)
            if not isinstance(config_data, dict): # Basic check
                 pytest.fail(f"Config file {CONFIG_FILE} did not parse as a dictionary.")
                 
            # Access profile directly at the top level
            if PROFILE in config_data and \
               'qdrant' in config_data[PROFILE] and \
               'connection' in config_data[PROFILE]['qdrant']:
                config_data[PROFILE]['qdrant']['connection']['collection'] = COLLECTION_NAME
                # Use yaml.dump to write back
                with open(CONFIG_FILE, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            else:
                 pytest.fail(f"Config file {CONFIG_FILE} is missing profile '{PROFILE}' or expected qdrant/connection keys.")
        except yaml.YAMLError as e:
             pytest.fail(f"Failed to parse YAML config {CONFIG_FILE}: {e}")
        except Exception as e:
             pytest.fail(f"An unexpected error occurred patching config: {e}")

    yield # Run tests

    # Restore original config content
    if original_content is not None:
        CONFIG_FILE.write_text(original_content)
    elif CONFIG_FILE.exists(): # Cleanup if created during test
         try:
             CONFIG_FILE.unlink()
         except OSError as e:
              print(f"Warning: Failed to clean up {CONFIG_FILE}: {e}")


# --- Test Function ---

def test_qdrant_e2e_lifecycle():
    """Runs the full end-to-end test sequence for Qdrant commands."""

    # 1. Create Collection (or ensure it's clean)
    logger.info("--- Step 1: Create Collection (Overwrite) ---")
    result = run_cli_command(["create", "--overwrite"])
    assert result.returncode == 0 # Already checked in helper, but explicit check here is fine
    assert f"Successfully recreated collection '{COLLECTION_NAME}'" in result.stdout or \
           f"Successfully created collection '{COLLECTION_NAME}'" in result.stdout # Handle both messages

    # 2. Add Documents
    logger.info("--- Step 2: Add Documents ---")
    result = run_cli_command(["add-documents", "--file", str(DOCS_PATH)])
    assert result.returncode == 0
    assert f"Successfully added/updated 4 documents" in result.stderr # Partial match is safer

    # 3. Count Documents (should be 4)
    logger.info("--- Step 3: Count Documents (Initial) ---")
    result = run_cli_command(["count"])
    assert result.returncode == 0
    # Check stderr for the log message instead of stdout
    assert f"Collection '{COLLECTION_NAME}' contains 4 documents." in result.stderr

    # 4a. Get Document (UUID)
    logger.info(f"--- Step 4a: Get Document (UUID: {TEST_UUID}) ---")
    result = run_cli_command(["get", "--ids", TEST_UUID])
    assert result.returncode == 0
    # TODO: Add check for logged output in stderr if needed, for now just check exit code

    # 4b. Get Document (Int)
    logger.info(f"--- Step 4b: Get Document (Int: {DOC_ID_INT_1}) ---")
    result = run_cli_command(["get", "--ids", str(DOC_ID_INT_1)])
    assert result.returncode == 0
    # TODO: Add check for logged output in stderr if needed, for now just check exit code

    # 5. Scroll Documents (Page 1)
    logger.info("--- Step 5: Scroll Documents (Page 1, Limit 2) ---")
    result = run_cli_command(["scroll", "--limit", "2"])
    assert result.returncode == 0
    # Check stderr for the actual log message format
    assert "Next page offset: " in result.stderr

    # 5b. Scroll Documents (Offset Test)
    logger.info(f"--- Step 5b: Scroll Documents (Offset {TEST_UUID}, Limit 2) ---")
    result = run_cli_command(["scroll", "--limit", "2", "--offset", TEST_UUID])
    assert result.returncode == 0
    # This scroll should get the remaining 2 docs and reach the end
    assert "Reached the end of the scroll results." in result.stderr

    # 6. Search Documents (No Filter)
    logger.info("--- Step 6: Search Documents (No Filter) ---")
    # Use a sample vector - replace with actual embedding logic if applicable
    query_vector = json.dumps([0.1] * 256) # Correct dimension from config
    result = run_cli_command(["search", "--query-vector", query_vector, "--limit", "1"])
    assert result.returncode == 0
    # TODO: Check stderr for success log

    # 7. Remove Document (UUID)
    logger.info(f"--- Step 7: Remove Document (UUID: {TEST_UUID}) ---")
    result = run_cli_command(["remove-documents", "--ids", TEST_UUID])
    assert result.returncode == 0
    # Check for the log confirmation instead of a specific echo
    assert f"Delete operation response: operation_id=" in result.stderr
    assert "status=<UpdateStatus.COMPLETED: 'completed'>" in result.stderr

    # 8. Count Documents (should be 3)
    logger.info("--- Step 8: Count Documents (After UUID Remove) ---")
    result = run_cli_command(["count"])
    assert result.returncode == 0
    assert f"Collection '{COLLECTION_NAME}' contains 3 documents." in result.stderr

    # 8b. Scroll with filter to see what *should* be deleted
    logger.info("--- Step 8b: Scroll with Filter (Before Remove) ---")
    scroll_filter = json.dumps({"must": [{ "key": "metadata.source", "match": { "value": "source1" }}]})
    result = run_cli_command(["scroll", "--filter-json", scroll_filter, "--limit", "10"])
    assert result.returncode == 0
    logger.info(f"Scroll with filter result (stderr):\n{result.stderr}") # Log for debugging

    # 9. Remove Documents by Filter
    logger.info("--- Step 9: Remove Documents (Filter) ---")
    filter_json = json.dumps({"must": [{"key": "metadata.source", "match": {"value": "source1"}}]})
    # Add --yes to bypass confirmation
    result = run_cli_command(["remove-documents", "--filter-json", filter_json, "--yes"])
    assert result.returncode == 0
    # Check for the log confirmation instead of a specific echo
    assert f"Delete operation response: operation_id=" in result.stderr
    assert "status=<UpdateStatus.COMPLETED: 'completed'>" in result.stderr

    # Add a small delay in case of eventual consistency
    logger.info("Waiting 1 second after filter deletion...")
    time.sleep(1)

    # 10. Count Documents (should be 1)
    logger.info("--- Step 10: Count Documents (After Filter Remove) ---")
    result = run_cli_command(["count"])
    assert result.returncode == 0
    assert f"Collection '{COLLECTION_NAME}' contains 1 documents." in result.stderr

    # 11. Delete Collection
    logger.info("--- Step 11: Delete Collection ---")
    result = run_cli_command(["delete", "--yes"])
    assert result.returncode == 0
    # Check stderr for the log message
    assert f"Successfully deleted collection '{COLLECTION_NAME}'." in result.stderr

    # 12. Verify Collection Deletion
    logger.info("--- Step 12: Verify Collection Deletion ---")
    result = run_cli_command(["list"])
    assert result.returncode == 0
    collections = json.loads(result.stdout)
    assert COLLECTION_NAME not in [c['name'] for c in collections]
