"""Tests for list collections command."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pytest_mock import MockerFixture

from docstore_manager.common.exceptions import DocumentStoreError
from docstore_manager.qdrant.commands.list import list_collections

@pytest.fixture
def mock_client():
    """Create a mock QdrantClient."""
    return Mock()

@pytest.fixture
def mock_command():
    """Create a mock QdrantCommand."""
    with patch("docstore_manager.qdrant.cli.QdrantCommand") as mock:
        yield mock.return_value

def test_list_collections_success(mock_client, mock_command):
    """Test successful collection listing."""
    # Setup mock response as a dictionary for the command method
    mock_response = {
        'success': True,
        'data': ["collection1", "collection2"],
        'message': "Found 2 collections",
        'error': None
    }
    mock_command.list_collections.return_value = mock_response

    # Pass the QdrantCommand mock to the handler function
    list_collections(mock_command, MagicMock())

    # Verify the command method was called
    mock_command.list_collections.assert_called_once()

def test_list_collections_empty(mock_client, mock_command):
    """Test listing when no collections exist."""
    # Setup mock response as a dictionary for the command method
    mock_response = {
        'success': True,
        'data': [],
        'message': "No collections found",
        'error': None
    }
    mock_command.list_collections.return_value = mock_response

    # Pass the QdrantCommand mock to the handler function
    list_collections(mock_command, MagicMock())

    # Verify the command method was called
    mock_command.list_collections.assert_called_once()

def test_list_collections_failure(mock_client, mock_command):
    """Test handling of failed collection listing."""
    # Setup mock response as a dictionary for the command method
    mock_response = {
        'success': False,
        'error': "Test error"
    }
    mock_command.list_collections.return_value = mock_response

    # Call the function and verify exception
    with pytest.raises(DocumentStoreError) as exc_info:
        # Pass the QdrantCommand mock to the handler function
        list_collections(mock_command, MagicMock())

    assert "Failed to list collections: Test error" in str(exc_info.value)

def test_list_collections_unexpected_error(mock_client, mock_command):
    """Test handling of unexpected errors."""
    # Setup command mock to raise an unexpected error
    mock_command.list_collections.side_effect = ValueError("Unexpected error")

    # Call the function and verify exception
    with pytest.raises(DocumentStoreError) as exc_info:
        # Pass the QdrantCommand mock to the handler function
        list_collections(mock_command, MagicMock())

    # Assert the correct formatted message
    assert "Unexpected error listing collections: Unexpected error" in str(exc_info.value)
    assert exc_info.value.details == {'error_type': 'ValueError'}

# Fixture to create a mock QdrantClient
@pytest.fixture
def mock_qdrant_client(mocker: MockerFixture):
    # Implementation of the fixture
    pass 