"""Tests for Solr Formatter."""

import json
from io import StringIO

import pytest

from docstore_manager.solr.format import SolrFormatter


# Rename to avoid pytest collection warning
class _TestableSolrFormatterImpl(SolrFormatter):
    """Test implementation of SolrFormatter for accessing protected methods."""

    def format_public(self, data, method_name, **kwargs):
        # Simplified formatting for testing - just use JSON
        # In a real scenario, this would call the specific protected format method
        return json.dumps(data, indent=2)


class TestSolrFormatter:
    @pytest.fixture
    def formatter(self):
        """Create a JSON formatter instance."""
        return _TestableSolrFormatterImpl("json")

    @pytest.fixture
    def yaml_formatter(self):
        """Create a YAML formatter instance."""
        return _TestableSolrFormatterImpl("yaml")

    def test_init_valid_format(self):
        formatter = _TestableSolrFormatterImpl("json")
        assert formatter.output_format == "json"
        formatter_yaml = _TestableSolrFormatterImpl("yaml")
        assert formatter_yaml.output_format == "yaml"

    def test_init_invalid_format(self):
        with pytest.raises(ValueError):
            _TestableSolrFormatterImpl("invalid_format")

    # --- format_collection_list Tests ---

    # Note: Tests using the fixture need `self` as the first argument now
    def test_format_collection_list_basic(self, formatter):
        collections = [
            {
                "name": "coll1",
                "configName": "conf1",
                "shards": {"s1": {}},
                "replicas": {"r1": {}},
                "health": "green",
            },
            {"name": "coll2", "configName": "conf2"},  # Missing optional keys
        ]
        expected = [
            {
                "name": "coll1",
                "config": "conf1",
                "shards": {"s1": {}},
                "replicas": {"r1": {}},
                "status": "green",
            },
            {
                "name": "coll2",
                "config": "conf2",
                "shards": {},
                "replicas": {},
                "status": "unknown",
            },
        ]
        result = formatter.format_collection_list(collections)
        assert json.loads(result) == expected

    def test_format_collection_list_empty(self, formatter):
        result = formatter.format_collection_list([])
        assert json.loads(result) == []

    # --- format_collection_info Tests ---

    def test_format_collection_info_basic(self, formatter):
        collection_name = "info_coll"
        info = {
            "numShards": 2,
            "replicationFactor": 2,
            "configName": "_default",
            "router": {"name": "compositeId", "field": "id"},
            "shards": {"shard1": {}},
            "aliases": ["alias1"],
            "properties": {"prop1": "val1"},
        }
        expected = {
            "name": "info_coll",
            "num_shards": 2,
            "replication_factor": 2,
            "config": "_default",
            "router": {"name": "compositeId", "field": "id"},
            "shards": {"shard1": {}},
            "aliases": ["alias1"],
            "properties": {"prop1": "val1"},
        }
        result = formatter.format_collection_info(collection_name, info)
        assert json.loads(result) == expected

    def test_format_collection_info_missing_optional(self, formatter):
        collection_name = "minimal_coll"
        info = {}
        expected = {
            "name": "minimal_coll",
            "num_shards": 0,
            "replication_factor": 0,
            "config": "unknown",
            "router": {"name": "unknown", "field": None},
            "shards": {},
            "aliases": [],
            "properties": {},
        }
        result = formatter.format_collection_info(collection_name, info)
        assert json.loads(result) == expected

    # --- format_documents Tests ---

    def test_format_documents_basic(self, formatter):
        docs = [
            {
                "id": "doc1",
                "field": "val1",
                "_version_": 123,
                "_score_": 1.5,
                "_vector_": [0.1, 0.2],
            },
            {"id": "doc2", "field": "val2", "_version_": 456},  # No score or vector
        ]
        # Default: with_vectors=False
        expected = [
            {"id": "doc1", "field": "val1", "score": 1.5},
            {"id": "doc2", "field": "val2"},
        ]
        result = formatter.format_documents(docs)
        assert json.loads(result) == expected

    def test_format_documents_with_vectors(self, formatter):
        docs = [
            {
                "id": "doc1",
                "field": "val1",
                "_version_": 123,
                "_score_": 1.5,
                "_vector_": [0.1, 0.2],
            },
        ]
        expected = [
            {"id": "doc1", "field": "val1", "score": 1.5, "_vector_": [0.1, 0.2]},
        ]
        result = formatter.format_documents(docs, with_vectors=True)
        assert json.loads(result) == expected

    def test_format_documents_empty(self, formatter):
        result = formatter.format_documents([])
        assert json.loads(result) == []
