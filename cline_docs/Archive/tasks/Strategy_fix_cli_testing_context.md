# Task: Fix CLI Testing Context
**Parent:** `implementation_plan_test_fixes.md`
**Children:** None

## Objective
Resolve the RuntimeError in CLI tests by using Click's CliRunner for all CLI tests instead of directly calling callback functions.

## Context
The test_cli_client_load_failure test in tests/qdrant/test_qdrant_cli.py is failing with a RuntimeError: "There is no active click context." This error occurs because the test is directly calling the callback function of the CLI command without properly setting up a Click context.

Click commands require a proper context to be set up before they can be executed. When testing Click commands, it's recommended to use the CliRunner class from Click's testing utilities, which properly sets up the Click context.

The failing test is:
- tests/qdrant/test_qdrant_cli.py::test_cli_client_load_failure

## Steps
1. [DONE] Analyze the failing test in tests/qdrant/test_qdrant_cli.py
   - [DONE] Understand how the test is currently calling the CLI command
   - [DONE] Identify why the test is failing with a RuntimeError

2. [DONE] Refactor the test to use Click's CliRunner
   - [DONE] Import the CliRunner class if not already imported
   - [DONE] Create a CliRunner instance
   - [DONE] Use the invoke method to run the CLI command
   - [DONE] Pass the appropriate arguments and context to the invoke method

3. [DONE] Update the test assertions
   - [DONE] Check the exit code of the result
   - [DONE] Check the output of the result for the expected error message
   - [DONE] Ensure the mock functions are called or not called as expected

4. [DONE] Run the failing test to verify the fix
   - [DONE] Run tests/qdrant/test_qdrant_cli.py::test_cli_client_load_failure

5. [DONE] Check for other tests that might have similar issues
   - [DONE] Look for other tests that directly call callback functions
   - [DONE] Refactor them to use CliRunner if necessary

## Dependencies
- Requires: None
- Blocks: None

## Expected Output
1. The test_cli_client_load_failure test should be updated to use Click's CliRunner.
2. The test should pass without the RuntimeError.
3. The test should still verify that the client loading failure is handled correctly.
4. Any other tests that directly call callback functions should be updated to use CliRunner.
