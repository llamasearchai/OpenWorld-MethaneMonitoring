"""Tests for indexed JSONL store implementation."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from openworld_methane.models import EmissionRecord
from openworld_methane.persistence.indexed_jsonl import IndexedJsonlStore, IndexEntry


@pytest.fixture
def temp_jsonl_file():
    """Create a temporary JSONL file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()
    index_path = temp_path.with_suffix(f"{temp_path.suffix}.idx")
    if index_path.exists():
        index_path.unlink()


@pytest.fixture
def sample_records():
    """Create sample emission records for testing."""
    records = []
    base_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    for i in range(5):
        records.append(
            EmissionRecord(
                timestamp=base_time.replace(hour=12 + i),
                site_id=f"site-{i % 2 + 1}",
                region_id=f"region-{i % 3 + 1}",
                emission_rate_kg_per_h=5.0 + i,
                source="test"
            )
        )

    return records


class TestIndexedJsonlStore:
    def test_initialization(self, temp_jsonl_file):
        """Test store initialization."""
        store = IndexedJsonlStore(temp_jsonl_file)
        assert store.path == temp_jsonl_file
        assert store.index_path == temp_jsonl_file.with_suffix(f"{temp_jsonl_file.suffix}.idx")
        assert temp_jsonl_file.exists()

    def test_append_records(self, temp_jsonl_file, sample_records):
        """Test appending records and index updates."""
        store = IndexedJsonlStore(temp_jsonl_file)

        count = store.append(sample_records)
        assert count == len(sample_records)

        # Verify file contents
        with temp_jsonl_file.open("r") as f:
            lines = f.readlines()
        assert len(lines) == len(sample_records)

        # Verify each line is valid JSON
        for line in lines:
            data = json.loads(line)
            assert "timestamp" in data
            assert "site_id" in data
            assert "region_id" in data
            assert "emission_rate_kg_per_h" in data

    def test_index_creation(self, temp_jsonl_file, sample_records):
        """Test that index is created and saved."""
        store = IndexedJsonlStore(temp_jsonl_file)
        store.append(sample_records)

        # Index should be saved to disk
        assert store.index_path.exists()

        # Create new store instance to test index loading
        new_store = IndexedJsonlStore(temp_jsonl_file)
        new_store._load_index()

        assert len(new_store._index) == len(sample_records)

        # Verify index entries
        for i, entry in enumerate(new_store._index):
            assert isinstance(entry, IndexEntry)
            assert entry.site_id == f"site-{i % 2 + 1}"
            assert entry.region_id == f"region-{i % 3 + 1}"

    def test_tail_functionality(self, temp_jsonl_file, sample_records):
        """Test tail method using index."""
        store = IndexedJsonlStore(temp_jsonl_file)
        store.append(sample_records)

        # Test getting last 3 records
        tail_records = store.tail(3)
        assert len(tail_records) == 3

        # Should be the last 3 records in order
        expected_rates = [7.0, 8.0, 9.0]  # Last 3 from sample_records
        actual_rates = [r.emission_rate_kg_per_h for r in tail_records]
        assert actual_rates == expected_rates

    def test_tail_more_than_available(self, temp_jsonl_file, sample_records):
        """Test tail when requesting more records than available."""
        store = IndexedJsonlStore(temp_jsonl_file)
        store.append(sample_records)

        tail_records = store.tail(10)  # More than available
        assert len(tail_records) == len(sample_records)

    def test_query_time_range(self, temp_jsonl_file, sample_records):
        """Test time range queries using index."""
        store = IndexedJsonlStore(temp_jsonl_file)
        store.append(sample_records)

        # Query for middle records
        start_time = sample_records[1].timestamp
        end_time = sample_records[3].timestamp

        results = store.query_time_range(start_time, end_time)

        # Should include records at positions 1 and 2 (3 is exclusive)
        assert len(results) == 2
        assert all(start_time <= r.timestamp < end_time for r in results)

    def test_query_by_site(self, temp_jsonl_file, sample_records):
        """Test site-specific queries."""
        store = IndexedJsonlStore(temp_jsonl_file)
        store.append(sample_records)

        site_1_records = store.query_by_site("site-1")

        # From sample_records, site-1 should be at indices 0, 2, 4
        assert len(site_1_records) == 3
        assert all(r.site_id == "site-1" for r in site_1_records)

    def test_query_by_region(self, temp_jsonl_file, sample_records):
        """Test region-specific queries."""
        store = IndexedJsonlStore(temp_jsonl_file)
        store.append(sample_records)

        region_1_records = store.query_by_region("region-1")

        # From sample_records, region-1 should be at indices 0, 3
        assert len(region_1_records) == 2
        assert all(r.region_id == "region-1" for r in region_1_records)

    def test_get_sites_and_regions(self, temp_jsonl_file, sample_records):
        """Test getting unique sites and regions."""
        store = IndexedJsonlStore(temp_jsonl_file)
        store.append(sample_records)

        sites = store.get_sites()
        regions = store.get_regions()

        assert sites == {"site-1", "site-2"}
        assert regions == {"region-1", "region-2", "region-3"}

    def test_summary(self, temp_jsonl_file, sample_records):
        """Test summary statistics."""
        store = IndexedJsonlStore(temp_jsonl_file)
        store.append(sample_records)

        summary = store.summary()

        assert summary["count"] == len(sample_records)
        assert summary["mean"] == 7.0  # (5+6+7+8+9)/5
        assert summary["min"] == 5.0
        assert summary["max"] == 9.0

    def test_empty_store(self, temp_jsonl_file):
        """Test operations on empty store."""
        store = IndexedJsonlStore(temp_jsonl_file)

        assert store.tail(5) == []
        assert store.query_time_range(None, None) == []
        assert store.query_by_site("site-1") == []
        assert store.get_sites() == set()

        summary = store.summary()
        assert summary["count"] == 0
        assert summary["mean"] == 0.0

    def test_index_rebuild(self, temp_jsonl_file, sample_records):
        """Test index rebuilding functionality."""
        store = IndexedJsonlStore(temp_jsonl_file)
        store.append(sample_records)

        # Remove index file to force rebuild
        store.index_path.unlink()

        # Create new store instance
        new_store = IndexedJsonlStore(temp_jsonl_file)

        # Should rebuild index automatically
        tail_records = new_store.tail(2)
        assert len(tail_records) == 2

    def test_corrupted_index_handling(self, temp_jsonl_file, sample_records):
        """Test handling of corrupted index files."""
        store = IndexedJsonlStore(temp_jsonl_file)
        store.append(sample_records)

        # Corrupt the index file
        with store.index_path.open("w") as f:
            f.write("corrupted data")

        # Create new store instance - should rebuild index
        new_store = IndexedJsonlStore(temp_jsonl_file)

        # Should work normally after rebuild
        tail_records = new_store.tail(2)
        assert len(tail_records) == 2

    def test_malformed_jsonl_handling(self, temp_jsonl_file):
        """Test handling of malformed JSONL data."""
        # Write some malformed data
        with temp_jsonl_file.open("w") as f:
            f.write('{"timestamp": "2023-01-01T12:00:00Z", "site_id": "site-1", "region_id": "region-1", "emission_rate_kg_per_h": 5.0}\n')
            f.write('invalid json line\n')  # Malformed
            f.write('{"timestamp": "2023-01-01T13:00:00Z", "site_id": "site-2", "region_id": "region-2", "emission_rate_kg_per_h": 6.0}\n')

        store = IndexedJsonlStore(temp_jsonl_file)
        store._rebuild_index()

        # Should have indexed only the valid lines
        assert len(store._index) == 2

    def test_to_dicts_format(self, temp_jsonl_file, sample_records):
        """Test to_dicts method format."""
        store = IndexedJsonlStore(temp_jsonl_file)
        store.append(sample_records)

        dicts = store.to_dicts()

        assert len(dicts) == len(sample_records)
        for d in dicts:
            assert "timestamp" in d
            assert "site_id" in d
            assert "region_id" in d
            assert "emission_rate_kg_per_h" in d
            assert isinstance(d["timestamp"], str)  # Should be ISO format
