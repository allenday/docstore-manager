"""Tests for base formatting functionality."""

import pytest
import json
import yaml
from typing import Dict, Any, List
from io import StringIO

from docstore_manager.core.format.base import DocumentStoreFormatter

# This class is intended as a test implementation for testing the base class,
# not as a test class to be collected by pytest itself.
# Rename it to avoid the `Test` prefix and the warning.
class _TestFormatterImpl(DocumentStoreFormatter):
    """Test implementation of DocumentStoreFormatter."""
    
    def format_collection_list(self, collections: List[Dict[str, Any]]) -> str:
        """Format a list of collections."""
        return self._format_output(collections)
    
    def format_collection_info(self, info: Dict[str, Any]) -> str:
        """Format collection information."""
        return self._format_output(info)
    
    def format_documents(self, documents: List[Dict[str, Any]], with_vectors: bool = False) -> str:
        """Format multiple documents."""
        if not with_vectors:
            documents = [self._filter_vectors(doc) for doc in documents]
        return self._format_output(documents)

class TestDocumentStoreFormatter:
    """Tests for DocumentStoreFormatter."""

    @pytest.fixture
    def formatter(self):
        """Create a test formatter instance."""
        return _TestFormatterImpl()

    def test_init_valid_format(self):
        """Test initialization with valid format."""
        formatter = _TestFormatterImpl("json")
        assert formatter.output_format == "json"
        formatter = _TestFormatterImpl("yaml")
        assert formatter.output_format == "yaml"

    def test_init_invalid_format(self):
        """Test initialization with invalid format."""
        with pytest.raises(ValueError) as exc:
            _TestFormatterImpl("invalid")
        assert "Unsupported output format" in str(exc.value)

    def test_format_collection_list_json(self):
        """Test formatting collection list as JSON."""
        formatter = _TestFormatterImpl("json")
        collections = [
            {"name": "test1", "count": 100},
            {"name": "test2", "count": 200}
        ]
        result = formatter.format_collection_list(collections)
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["name"] == "test1"
        assert parsed[1]["count"] == 200

    def test_format_collection_list_yaml(self):
        """Test formatting collection list as YAML."""
        formatter = _TestFormatterImpl("yaml")
        collections = [
            {"name": "test1", "count": 100},
            {"name": "test2", "count": 200}
        ]
        result = formatter.format_collection_list(collections)
        parsed = yaml.safe_load(result)
        assert len(parsed) == 2
        assert parsed[0]["name"] == "test1"
        assert parsed[1]["count"] == 200

    def test_format_collection_info_json(self):
        """Test formatting collection info as JSON."""
        formatter = _TestFormatterImpl("json")
        info = {
            "name": "test",
            "size": 100,
            "metadata": {"created": "2024-01-01"}
        }
        result = formatter.format_collection_info(info)
        parsed = json.loads(result)
        assert parsed["name"] == "test"
        assert parsed["size"] == 100
        assert parsed["metadata"]["created"] == "2024-01-01"

    def test_format_collection_info_yaml(self):
        """Test formatting collection info as YAML."""
        formatter = _TestFormatterImpl("yaml")
        info = {
            "name": "test",
            "size": 100,
            "metadata": {"created": "2024-01-01"}
        }
        result = formatter.format_collection_info(info)
        parsed = yaml.safe_load(result)
        assert parsed["name"] == "test"
        assert parsed["size"] == 100
        assert parsed["metadata"]["created"] == "2024-01-01"

    def test_format_documents_with_vectors_json(self):
        """Test formatting documents with vectors as JSON."""
        formatter = _TestFormatterImpl("json")
        docs = [
            {"id": 1, "text": "test1", "vector": [1.0, 2.0, 3.0]},
            {"id": 2, "text": "test2", "vector": [4.0, 5.0, 6.0]}
        ]
        result = formatter.format_documents(docs, with_vectors=True)
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert "vector" in parsed[0]
        assert parsed[0]["vector"] == [1.0, 2.0, 3.0]
        assert parsed[1]["vector"] == [4.0, 5.0, 6.0]

    def test_format_documents_without_vectors_json(self):
        """Test formatting documents without vectors as JSON."""
        formatter = _TestFormatterImpl("json")
        docs = [
            {"id": 1, "text": "test1", "vector": [1.0, 2.0, 3.0]},
            {"id": 2, "text": "test2", "vector": [4.0, 5.0, 6.0]}
        ]
        result = formatter.format_documents(docs, with_vectors=False)
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert "vector" not in parsed[0]
        assert "vector" not in parsed[1]
        assert parsed[0]["text"] == "test1"
        assert parsed[1]["text"] == "test2"

    def test_format_documents_with_vectors_yaml(self):
        """Test formatting documents with vectors as YAML."""
        formatter = _TestFormatterImpl("yaml")
        docs = [
            {"id": 1, "text": "test1", "vector": [1.0, 2.0, 3.0]},
            {"id": 2, "text": "test2", "vector": [4.0, 5.0, 6.0]}
        ]
        result = formatter.format_documents(docs, with_vectors=True)
        parsed = yaml.safe_load(result)
        assert len(parsed) == 2
        assert "vector" in parsed[0]
        assert parsed[0]["vector"] == [1.0, 2.0, 3.0]
        assert parsed[1]["vector"] == [4.0, 5.0, 6.0]

    def test_format_documents_without_vectors_yaml(self):
        """Test formatting documents without vectors as YAML."""
        formatter = _TestFormatterImpl("yaml")
        docs = [
            {"id": 1, "text": "test1", "vector": [1.0, 2.0, 3.0]},
            {"id": 2, "text": "test2", "vector": [4.0, 5.0, 6.0]}
        ]
        result = formatter.format_documents(docs, with_vectors=False)
        parsed = yaml.safe_load(result)
        assert len(parsed) == 2
        assert "vector" not in parsed[0]
        assert "vector" not in parsed[1]
        assert parsed[0]["text"] == "test1"
        assert parsed[1]["text"] == "test2"

    def test_format_empty_list_json(self):
        """Test formatting empty list as JSON."""
        formatter = _TestFormatterImpl("json")
        assert formatter.format_collection_list([]) == "[]"
        assert formatter.format_documents([]) == "[]"

    def test_format_empty_list_yaml(self):
        """Test formatting empty list as YAML."""
        formatter = _TestFormatterImpl("yaml")
        assert formatter.format_collection_list([]) == "[]\n"
        assert formatter.format_documents([]) == "[]\n"

    def test_filter_vectors_empty_doc(self):
        """Test filtering vectors from empty document."""
        formatter = _TestFormatterImpl()
        doc = {}
        filtered = formatter._filter_vectors(doc)
        assert filtered == {}

    def test_filter_vectors_no_vector(self):
        """Test filtering vectors from document without vector."""
        formatter = _TestFormatterImpl()
        doc = {"id": 1, "text": "test"}
        filtered = formatter._filter_vectors(doc)
        assert filtered == doc

    def test_filter_vectors_with_vector(self):
        """Test filtering vectors from document with vector."""
        formatter = _TestFormatterImpl()
        doc = {"id": 1, "text": "test", "vector": [1.0, 2.0, 3.0]}
        filtered = formatter._filter_vectors(doc)
        assert filtered == {"id": 1, "text": "test"}

    def test_filter_vectors_with_nested_vector(self):
        """Test filtering vectors from document with nested vector."""
        formatter = _TestFormatterImpl()
        doc = {
            "id": 1,
            "text": "test",
            "metadata": {
                "vector": [1.0, 2.0, 3.0],
                "other": "value"
            }
        }
        filtered = formatter._filter_vectors(doc)
        assert filtered == {
            "id": 1,
            "text": "test",
            "metadata": {
                "other": "value"
            }
        }

    def test_format_complex_nested_structure_json(self):
        """Test formatting complex nested structure as JSON."""
        formatter = _TestFormatterImpl("json")
        data = {
            "name": "test",
            "metadata": {
                "created": "2024-01-01",
                "stats": {
                    "count": 100,
                    "distribution": [1, 2, 3]
                }
            },
            "tags": ["tag1", "tag2"]
        }
        result = formatter.format_collection_info(data)
        parsed = json.loads(result)
        assert parsed["metadata"]["stats"]["count"] == 100
        assert parsed["tags"] == ["tag1", "tag2"]

    def test_format_complex_nested_structure_yaml(self):
        """Test formatting complex nested structure as YAML."""
        formatter = _TestFormatterImpl("yaml")
        data = {
            "name": "test",
            "metadata": {
                "created": "2024-01-01",
                "stats": {
                    "count": 100,
                    "distribution": [1, 2, 3]
                }
            },
            "tags": ["tag1", "tag2"]
        }
        result = formatter.format_collection_info(data)
        parsed = yaml.safe_load(result)
        assert parsed["metadata"]["stats"]["count"] == 100
        assert parsed["tags"] == ["tag1", "tag2"] 