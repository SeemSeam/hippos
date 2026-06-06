"""Tests for snapshot archival — save, list, load, resolve."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from hippos.constants import INDEX_FILE, SNAPSHOTS_DIR
from hippos.tools.snapshot import (
    list_snapshots,
    load_snapshot,
    resolve_snapshot,
    save_snapshot,
)


@pytest.fixture
def hippos_dir(tmp_path):
    """Create a minimal .hippos/ with a fake index."""
    out = tmp_path / ".hippos"
    out.mkdir()
    index = {
        "version": 2,
        "schema": "hippos-index/v2",
        "generated_at": "2026-01-01T00:00:00+00:00",
        "project": {"overview": "Test project"},
        "modules": [{"id": "mod-a", "desc": "Module A", "file_count": 1}],
        "files": {
            "src/a.py": {
                "id": "file:src/a.py",
                "type": "file",
                "name": "a.py",
                "lang": "python",
                "desc": "File A",
                "tags": ["python"],
                "module": "mod-a",
                "signatures": [],
            },
        },
        "stats": {
            "total_files": 1,
            "total_modules": 1,
            "total_signatures": 0,
        },
    }
    index_path = out / INDEX_FILE
    index_path.write_text(json.dumps(index), encoding="utf-8")
    return out


class TestSaveSnapshot:
    def test_creates_file_with_snapshot_id(self, hippos_dir):
        result = save_snapshot(hippos_dir)
        snap_id = result["snapshot_id"]
        snap_path = hippos_dir / SNAPSHOTS_DIR / f"{snap_id}.json"
        assert snap_path.exists()

    def test_snapshot_id_contains_microseconds(self, hippos_dir):
        result = save_snapshot(hippos_dir)
        sid = result["snapshot_id"]
        # Format: YYYYMMDDTHHmmSS_ffffffZ
        assert len(sid) == len("20260210T143000_123456Z")
        assert "T" in sid
        assert sid.endswith("Z")

    def test_snapshot_metadata_injected(self, hippos_dir):
        result = save_snapshot(hippos_dir, message="test msg")
        data = json.loads(
            (hippos_dir / SNAPSHOTS_DIR / f"{result['snapshot_id']}.json").read_text()
        )
        meta = data["_snapshot"]
        assert meta["snapshot_id"] == result["snapshot_id"]
        assert "snapshot_created_at" in meta
        assert meta["message"] == "test msg"

    def test_stats_returned(self, hippos_dir):
        result = save_snapshot(hippos_dir)
        assert result["stats"]["total_files"] == 1

    def test_consecutive_saves_no_collision(self, hippos_dir):
        r1 = save_snapshot(hippos_dir)
        r2 = save_snapshot(hippos_dir)
        assert r1["snapshot_id"] != r2["snapshot_id"]

    def test_missing_index_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            save_snapshot(tmp_path / "nonexistent")


class TestListSnapshots:
    def test_empty_dir_returns_empty(self, hippos_dir):
        assert list_snapshots(hippos_dir) == []

    def test_reverse_chronological_order(self, hippos_dir):
        save_snapshot(hippos_dir)
        save_snapshot(hippos_dir)
        snaps = list_snapshots(hippos_dir)
        assert len(snaps) == 2
        assert snaps[0]["snapshot_id"] > snaps[1]["snapshot_id"]

    def test_entry_fields(self, hippos_dir):
        save_snapshot(hippos_dir, message="hello")
        snaps = list_snapshots(hippos_dir)
        entry = snaps[0]
        assert "snapshot_id" in entry
        assert "generated_at" in entry
        assert entry["message"] == "hello"
        assert "total_files" in entry["stats"]


class TestLoadSnapshot:
    def test_load_existing(self, hippos_dir):
        result = save_snapshot(hippos_dir)
        data = load_snapshot(hippos_dir, result["snapshot_id"])
        assert data["version"] == 2
        assert "_snapshot" in data

    def test_load_nonexistent_raises(self, hippos_dir):
        with pytest.raises(FileNotFoundError):
            load_snapshot(hippos_dir, "99990101T000000_000000Z")


class TestResolveSnapshot:
    def test_current(self, hippos_dir):
        data = resolve_snapshot(hippos_dir, "current")
        assert data["version"] == 2

    def test_latest(self, hippos_dir):
        save_snapshot(hippos_dir, message="first")
        save_snapshot(hippos_dir, message="second")
        data = resolve_snapshot(hippos_dir, "latest")
        assert data["_snapshot"]["message"] == "second"

    def test_latest_tilde_1(self, hippos_dir):
        save_snapshot(hippos_dir, message="first")
        save_snapshot(hippos_dir, message="second")
        data = resolve_snapshot(hippos_dir, "latest~1")
        assert data["_snapshot"]["message"] == "first"

    def test_latest_tilde_2(self, hippos_dir):
        save_snapshot(hippos_dir, message="a")
        save_snapshot(hippos_dir, message="b")
        save_snapshot(hippos_dir, message="c")
        data = resolve_snapshot(hippos_dir, "latest~2")
        assert data["_snapshot"]["message"] == "a"

    def test_exact_id(self, hippos_dir):
        result = save_snapshot(hippos_dir)
        data = resolve_snapshot(hippos_dir, result["snapshot_id"])
        assert data["_snapshot"]["snapshot_id"] == result["snapshot_id"]

    def test_invalid_ref_raises(self, hippos_dir):
        save_snapshot(hippos_dir)
        with pytest.raises(ValueError):
            resolve_snapshot(hippos_dir, "latest~abc")

    def test_out_of_range_raises(self, hippos_dir):
        save_snapshot(hippos_dir)
        with pytest.raises(FileNotFoundError):
            resolve_snapshot(hippos_dir, "latest~5")

    def test_no_snapshots_raises(self, hippos_dir):
        with pytest.raises(FileNotFoundError):
            resolve_snapshot(hippos_dir, "latest")


class TestCorruptedSnapshot:
    def test_list_skips_corrupted_json(self, hippos_dir):
        """Corrupted snapshot files should be skipped, not crash list."""
        save_snapshot(hippos_dir, message="good")
        snap_dir = hippos_dir / SNAPSHOTS_DIR
        bad = snap_dir / "99990101T000000_000000Z.json"
        bad.write_text("{invalid json", encoding="utf-8")
        snaps = list_snapshots(hippos_dir)
        assert len(snaps) == 1
        assert snaps[0]["message"] == "good"
