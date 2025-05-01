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
VENV_BIN_PATH = BASE_DIR / "venv" / "bin"
EXECUTABLE_PATH = VENV_BIN_PATH / "docstore-manager"

assert EXECUTABLE_PATH.exists(), (
    f"Executable not found at expected path: {EXECUTABLE_PATH}\n"
    f"Ensure the virtual environment exists at {BASE_DIR / 'venv'} "
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
    assert f"Successfully added/updated 4 documents in collection '{COLLECTION_NAME}'." in result.stdout

    # 3. Count Documents (should be 4)
    logger.info("--- Step 3: Count Documents (Initial) ---")
    result = run_cli_command(["count"])
    assert result.returncode == 0
    try:
        count_result = json.loads(result.stdout)
        assert count_result.get("collection") == COLLECTION_NAME
        assert count_result.get("count") == 4
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from count: {result.stdout}")

    # 4a. Get Document (UUID)
    logger.info(f"--- Step 4a: Get Document (UUID: {TEST_UUID}) ---")
    result = run_cli_command(["get", "--ids", TEST_UUID])
    assert result.returncode == 0
    try:
        get_result_uuid = json.loads(result.stdout)
        assert isinstance(get_result_uuid, list)
        assert len(get_result_uuid) == 1
        assert get_result_uuid[0].get("id") == TEST_UUID
        assert "payload" in get_result_uuid[0]
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from get (UUID): {result.stdout}")

    # 4b. Get Document (Integer)
    logger.info(f"--- Step 4b: Get Document (Int: {DOC_ID_INT_1}) ---")
    result = run_cli_command(["get", "--ids", str(DOC_ID_INT_1)])
    assert result.returncode == 0
    try:
        get_result_int = json.loads(result.stdout)
        assert isinstance(get_result_int, list)
        assert len(get_result_int) == 1
        assert get_result_int[0].get("id") == DOC_ID_INT_1 # JSON numbers are ints
        assert "payload" in get_result_int[0]
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from get (Int): {result.stdout}")

    # 5. Scroll Documents (Page 1)
    logger.info("--- Step 5: Scroll Documents (Page 1, Limit 2) ---")
    result = run_cli_command(["scroll", "--limit", "2"])
    assert result.returncode == 0
    assert "# Next page offset:" in result.stderr # Check hint in stderr
    try:
        scroll_result_1 = json.loads(result.stdout)
        assert isinstance(scroll_result_1, list)
        assert len(scroll_result_1) == 2
        found_ids_1 = {item.get("id") for item in scroll_result_1}
        assert DOC_ID_INT_1 in found_ids_1
        assert DOC_ID_INT_2 in found_ids_1
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from scroll (Page 1): {result.stdout}")

    # Extract offset from stderr for next scroll
    offset_line = next((line for line in result.stderr.splitlines() if line.startswith("# Next page offset:")), None)
    assert offset_line is not None, "Could not find offset hint in scroll stderr"
    scroll_offset = offset_line.split(":")[-1].strip()
    assert scroll_offset, "Could not extract offset value from hint"
    logger.info(f"Extracted scroll offset: {scroll_offset}")


    # 6. Scroll Documents (Page 2)
    logger.info("--- Step 6: Scroll Documents (Page 2, Offset) ---")
    result = run_cli_command(["scroll", "--limit", "2", "--offset", scroll_offset])
    assert result.returncode == 0
    assert "# Next page offset:" not in result.stderr # Should be no more offset
    try:
        scroll_result_2 = json.loads(result.stdout)
        assert isinstance(scroll_result_2, list)
        assert len(scroll_result_2) == 2
        found_ids_2 = {item.get("id") for item in scroll_result_2}
        assert DOC_ID_INT_3 in found_ids_2
        assert TEST_UUID in found_ids_2
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from scroll (Page 2): {result.stdout}")


    # 7. Search Documents
    logger.info("--- Step 7: Search Documents ---")
    query_vector_json = generate_vector_json(0.1, VECTOR_DIM)
    result = run_cli_command([
        "search", "--query-vector", query_vector_json, "--limit", "1"
    ])
    assert result.returncode == 0
    try:
        search_result = json.loads(result.stdout)
        assert isinstance(search_result, list)
        assert len(search_result) >= 1 # Should find at least one
        top_id = search_result[0].get("id")
        valid_top_ids = {DOC_ID_INT_2, DOC_ID_INT_3, TEST_UUID} 
        assert top_id in valid_top_ids, \
               f"Expected top search result ID to be one of {valid_top_ids}, but got {top_id}"
        assert "score" in search_result[0]
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from search: {result.stdout}")

    # 8. Collection Info
    logger.info("--- Step 8: Collection Info ---")
    result = run_cli_command(["info"])
    assert result.returncode == 0
    try:
        info_result = json.loads(result.stdout)
        assert info_result.get("name") == COLLECTION_NAME
        assert info_result.get("points_count") == 4
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from info: {result.stdout}")

    # 9a. Remove Document (Integer ID 2)
    logger.info(f"--- Step 9a: Remove Document (Int: {DOC_ID_INT_2}) ---")
    result = run_cli_command(["remove-documents", "--ids", str(DOC_ID_INT_2)])
    assert result.returncode == 0
    assert f"Remove operation by IDs for collection '{COLLECTION_NAME}' finished. Status: completed." in result.stdout

    # 9b. Remove Document (UUID ID)
    logger.info(f"--- Step 9b: Remove Document (UUID: {TEST_UUID}) ---")
    result = run_cli_command(["remove-documents", "--ids", TEST_UUID])
    assert result.returncode == 0
    assert f"Remove operation by IDs for collection '{COLLECTION_NAME}' finished. Status: completed." in result.stdout

    # 10. Count Documents (should be 2)
    logger.info("--- Step 10: Count Documents (After Remove) ---")
    result = run_cli_command(["count"])
    assert result.returncode == 0
    try:
        count_result_2 = json.loads(result.stdout)
        assert count_result_2.get("collection") == COLLECTION_NAME
        assert count_result_2.get("count") == 2
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from count (After Remove): {result.stdout}")

    # 11. Remove Documents (remaining integers 1,3)
    logger.info(f"--- Step 11: Remove Documents (Ints: {DOC_ID_INT_1},{DOC_ID_INT_3}) ---")
    ids_to_remove = f"{DOC_ID_INT_1},{DOC_ID_INT_3}"
    result = run_cli_command(["remove-documents", "--ids", ids_to_remove])
    assert result.returncode == 0
    assert f"Remove operation by IDs for collection '{COLLECTION_NAME}' finished. Status: completed." in result.stdout

    # 12. Count Documents (should be 0)
    logger.info("--- Step 12: Count Documents (Final) ---")
    result = run_cli_command(["count"])
    assert result.returncode == 0
    try:
        count_result_3 = json.loads(result.stdout)
        assert count_result_3.get("collection") == COLLECTION_NAME
        assert count_result_3.get("count") == 0
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from count (Final): {result.stdout}")

    # 13. Delete Collection
    logger.info("--- Step 13: Delete Collection ---")
    result = run_cli_command(["delete", "-y"])
    assert result.returncode == 0
    assert f"Successfully deleted collection '{COLLECTION_NAME}'." in result.stdout

    # 14. (Optional) List Collections (Verify Deletion)
    logger.info("--- Step 14: List Collections (Verify Deletion) ---")
    result = run_cli_command(["list"])
    assert result.returncode == 0
    try:
        list_result = json.loads(result.stdout)
        assert isinstance(list_result, list)
        assert not any(col.get("name") == COLLECTION_NAME for col in list_result)
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from list: {result.stdout}")
