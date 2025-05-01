"""Integration tests for the Qdrant CLI commands."""

import subprocess
import json
import pytest
import sys
from pathlib import Path
import uuid
import yaml # Import YAML library

# Determine the project root based on the test file location
# Assuming tests are in tests/integration/
TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent.parent

# Get the full path to the executable relative to the current python interpreter
EXECUTABLE_PATH = Path(sys.executable).parent / "docstore-manager"
if not EXECUTABLE_PATH.exists(): # Add a check in case it's not found
    pytest.fail(f"Executable not found at expected path: {EXECUTABLE_PATH}\n" +
                "Ensure the package is installed in editable mode (pip install -e .) in the correct venv.")

# Define constants for paths and parameters
CONFIG_PATH = TEST_DIR / "config.yaml"
PROFILE = "default"
DOCS_PATH = PROJECT_ROOT / "tests" / "fixtures" / "test_qdrant_docs.jsonl"
IDS_PATH = PROJECT_ROOT / "tests" / "fixtures" / "test_qdrant_docs_ids.txt" # Keep track but might not use
COLLECTION_NAME = "test_qdrant_integration" # Use a dedicated name for tests
TEST_UUID = "40000000-0000-0000-0000-000000000000" # From the updated fixtures
DOC_ID_INT_1 = 1
DOC_ID_INT_2 = 2
DOC_ID_INT_3 = 3
VECTOR_DIM = 256 # Assuming from previous context

# Use the script name directly (assuming it's installed/discoverable via venv)
# And ensure global options come first
BASE_CMD_PREFIX = [
    str(EXECUTABLE_PATH), # Use full path
    "--config", str(CONFIG_PATH), 
    "--profile", PROFILE
]

def run_cli_command(cmd_list: list[str]) -> tuple[int, str, str]:
    """Runs a CLI command using subprocess and returns exit code, stdout, stderr."""
    # Combine prefix, qdrant subgroup, and specific command
    full_cmd = BASE_CMD_PREFIX + ["qdrant"] + cmd_list 
    print(f"\nRunning command: {' '.join(full_cmd)}") # Print command for debugging
    # Use shell=True cautiously if needed, or ensure docstore-manager is in PATH
    # For venv, it should be if venv is active or pytest is run from venv
    result = subprocess.run(full_cmd, capture_output=True, text=True, check=False, cwd=PROJECT_ROOT)
    print(f"Exit Code: {result.returncode}")
    if result.stdout:
        print(f"Stdout:\n{result.stdout.strip()}")
    if result.stderr:
        print(f"Stderr:\n{result.stderr.strip()}")
    return result.returncode, result.stdout, result.stderr

def generate_vector_json(val: float, dim: int) -> str:
    """Generates a JSON string for a vector."""
    vector = [val] * dim
    return json.dumps(vector)

# --- Fixture to ensure config uses the test-specific collection name ---
@pytest.fixture(scope="module", autouse=True)
def patch_config_collection_name():
    """Patches the config file to use a test-specific collection name."""
    original_content = None
    if CONFIG_PATH.exists():
        original_content = CONFIG_PATH.read_text()
        try:
            # Use yaml.safe_load for YAML parsing
            config_data = yaml.safe_load(original_content)
            if not isinstance(config_data, dict): # Basic check
                 pytest.fail(f"Config file {CONFIG_PATH} did not parse as a dictionary.")
                 
            # Access profile directly at the top level
            if PROFILE in config_data and \
               'qdrant' in config_data[PROFILE] and \
               'connection' in config_data[PROFILE]['qdrant']:
                config_data[PROFILE]['qdrant']['connection']['collection'] = COLLECTION_NAME
                # Use yaml.dump to write back
                with open(CONFIG_PATH, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            else:
                 pytest.fail(f"Config file {CONFIG_PATH} is missing profile '{PROFILE}' or expected qdrant/connection keys.")
        except yaml.YAMLError as e:
             pytest.fail(f"Failed to parse YAML config {CONFIG_PATH}: {e}")
        except Exception as e:
             pytest.fail(f"An unexpected error occurred patching config: {e}")

    yield # Run tests

    # Restore original config content
    if original_content is not None:
        CONFIG_PATH.write_text(original_content)
    elif CONFIG_PATH.exists(): # Cleanup if created during test
         try:
             CONFIG_PATH.unlink()
         except OSError as e:
              print(f"Warning: Failed to clean up {CONFIG_PATH}: {e}")


# --- Test Function ---

def test_qdrant_e2e_lifecycle():
    """Runs the full end-to-end test sequence for Qdrant commands."""

    # 1. Create Collection (or ensure it's clean)
    print("\n--- Step 1: Create Collection (Overwrite) ---")
    exit_code, stdout, stderr = run_cli_command(["create", "--overwrite"])
    assert exit_code == 0
    assert f"Successfully recreated collection '{COLLECTION_NAME}'" in stdout or \
           f"Successfully created collection '{COLLECTION_NAME}'" in stdout # Handle both messages

    # 2. Add Documents
    print("\n--- Step 2: Add Documents ---")
    exit_code, stdout, stderr = run_cli_command(["add-documents", "--file", str(DOCS_PATH)])
    assert exit_code == 0
    assert f"Successfully added/updated 4 documents in collection '{COLLECTION_NAME}'." in stdout

    # 3. Count Documents (should be 4)
    print("\n--- Step 3: Count Documents (Initial) ---")
    exit_code, stdout, stderr = run_cli_command(["count"])
    assert exit_code == 0
    try:
        count_result = json.loads(stdout)
        assert count_result.get("collection") == COLLECTION_NAME
        assert count_result.get("count") == 4
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from count: {stdout}")

    # 4a. Get Document (UUID)
    print(f"\n--- Step 4a: Get Document (UUID: {TEST_UUID}) ---")
    exit_code, stdout, stderr = run_cli_command(["get", "--ids", TEST_UUID])
    assert exit_code == 0
    try:
        get_result_uuid = json.loads(stdout)
        assert isinstance(get_result_uuid, list)
        assert len(get_result_uuid) == 1
        assert get_result_uuid[0].get("id") == TEST_UUID
        assert "payload" in get_result_uuid[0]
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from get (UUID): {stdout}")

    # 4b. Get Document (Integer)
    print(f"\n--- Step 4b: Get Document (Int: {DOC_ID_INT_1}) ---")
    exit_code, stdout, stderr = run_cli_command(["get", "--ids", str(DOC_ID_INT_1)])
    assert exit_code == 0
    try:
        get_result_int = json.loads(stdout)
        assert isinstance(get_result_int, list)
        assert len(get_result_int) == 1
        assert get_result_int[0].get("id") == DOC_ID_INT_1 # JSON numbers are ints
        assert "payload" in get_result_int[0]
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from get (Int): {stdout}")

    # 5. Scroll Documents (Page 1)
    print("\n--- Step 5: Scroll Documents (Page 1, Limit 2) ---")
    exit_code, stdout, stderr = run_cli_command(["scroll", "--limit", "2"])
    assert exit_code == 0
    assert "# Next page offset:" in stderr # Check hint in stderr
    try:
        scroll_result_1 = json.loads(stdout)
        assert isinstance(scroll_result_1, list)
        assert len(scroll_result_1) == 2
        # Note: Scroll order isn't strictly guaranteed, but usually follows insertion/ID
        # assert scroll_result_1[0].get("id") == DOC_ID_INT_1
        # assert scroll_result_1[1].get("id") == DOC_ID_INT_2
        found_ids_1 = {item.get("id") for item in scroll_result_1}
        assert DOC_ID_INT_1 in found_ids_1
        assert DOC_ID_INT_2 in found_ids_1
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from scroll (Page 1): {stdout}")

    # Extract offset from stderr for next scroll
    offset_line = next((line for line in stderr.splitlines() if line.startswith("# Next page offset:")), None)
    assert offset_line is not None, "Could not find offset hint in scroll stderr"
    scroll_offset = offset_line.split(":")[-1].strip()
    assert scroll_offset, "Could not extract offset value from hint"
    print(f"Extracted scroll offset: {scroll_offset}")


    # 6. Scroll Documents (Page 2)
    print("\n--- Step 6: Scroll Documents (Page 2, Offset) ---")
    exit_code, stdout, stderr = run_cli_command(["scroll", "--limit", "2", "--offset", scroll_offset])
    assert exit_code == 0
    assert "# Next page offset:" not in stderr # Should be no more offset
    try:
        scroll_result_2 = json.loads(stdout)
        assert isinstance(scroll_result_2, list)
        assert len(scroll_result_2) == 2
        found_ids_2 = {item.get("id") for item in scroll_result_2}
        assert DOC_ID_INT_3 in found_ids_2
        assert TEST_UUID in found_ids_2
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from scroll (Page 2): {stdout}")


    # 7. Search Documents
    print("\n--- Step 7: Search Documents ---")
    query_vector_json = generate_vector_json(0.1, VECTOR_DIM)
    exit_code, stdout, stderr = run_cli_command([
        "search", "--query-vector", query_vector_json, "--limit", "1"
    ])
    assert exit_code == 0
    try:
        search_result = json.loads(stdout)
        assert isinstance(search_result, list)
        assert len(search_result) >= 1 # Should find at least one
        # Check top result - accept any of the tied IDs (2, 3, or UUID)
        top_id = search_result[0].get("id")
        valid_top_ids = {DOC_ID_INT_2, DOC_ID_INT_3, TEST_UUID} 
        assert top_id in valid_top_ids, \
               f"Expected top search result ID to be one of {valid_top_ids}, but got {top_id}"
        assert "score" in search_result[0]
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from search: {stdout}")

    # 8. Collection Info
    print("\n--- Step 8: Collection Info ---")
    exit_code, stdout, stderr = run_cli_command(["info"])
    assert exit_code == 0
    try:
        info_result = json.loads(stdout)
        assert info_result.get("name") == COLLECTION_NAME
        assert info_result.get("points_count") == 4
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from info: {stdout}")

    # 9a. Remove Document (Integer ID 2)
    print(f"\n--- Step 9a: Remove Document (Int: {DOC_ID_INT_2}) ---")
    exit_code, stdout, stderr = run_cli_command(["remove-documents", "--ids", str(DOC_ID_INT_2)])
    assert exit_code == 0
    assert f"Remove operation by IDs for collection '{COLLECTION_NAME}' finished. Status: completed." in stdout

    # 9b. Remove Document (UUID ID)
    print(f"\n--- Step 9b: Remove Document (UUID: {TEST_UUID}) ---")
    exit_code, stdout, stderr = run_cli_command(["remove-documents", "--ids", TEST_UUID])
    assert exit_code == 0
    assert f"Remove operation by IDs for collection '{COLLECTION_NAME}' finished. Status: completed." in stdout

    # 10. Count Documents (should be 2)
    print("\n--- Step 10: Count Documents (After Remove) ---")
    exit_code, stdout, stderr = run_cli_command(["count"])
    assert exit_code == 0
    try:
        count_result_2 = json.loads(stdout)
        assert count_result_2.get("collection") == COLLECTION_NAME
        assert count_result_2.get("count") == 2
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from count (After Remove): {stdout}")

    # 11. Remove Documents (remaining integers 1,3)
    print(f"\n--- Step 11: Remove Documents (Ints: {DOC_ID_INT_1},{DOC_ID_INT_3}) ---")
    ids_to_remove = f"{DOC_ID_INT_1},{DOC_ID_INT_3}"
    exit_code, stdout, stderr = run_cli_command(["remove-documents", "--ids", ids_to_remove])
    assert exit_code == 0
    assert f"Remove operation by IDs for collection '{COLLECTION_NAME}' finished. Status: completed." in stdout

    # 12. Count Documents (should be 0)
    print("\n--- Step 12: Count Documents (Final) ---")
    exit_code, stdout, stderr = run_cli_command(["count"])
    assert exit_code == 0
    try:
        count_result_3 = json.loads(stdout)
        assert count_result_3.get("collection") == COLLECTION_NAME
        assert count_result_3.get("count") == 0
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from count (Final): {stdout}")

    # 13. Delete Collection
    print("\n--- Step 13: Delete Collection ---")
    exit_code, stdout, stderr = run_cli_command(["delete", "-y"])
    assert exit_code == 0
    assert f"Successfully deleted collection '{COLLECTION_NAME}'." in stdout

    # 14. (Optional) List Collections (Verify Deletion)
    print("\n--- Step 14: List Collections (Verify Deletion) ---")
    exit_code, stdout, stderr = run_cli_command(["list"])
    assert exit_code == 0
    try:
        list_result = json.loads(stdout)
        assert isinstance(list_result, list)
        assert not any(col.get("name") == COLLECTION_NAME for col in list_result)
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from list: {stdout}")
