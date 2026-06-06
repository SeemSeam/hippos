from __future__ import annotations

from pathlib import Path

from hippos.nav.navigate_mentions import extract_mentions
from hippos.nav.navigate_paths import validate_repo_paths


def test_extract_mentions_detects_files_and_identifiers() -> None:
    all_files = [
        "src/hippos/tools/ranker/ranker_graph.py",
        "src/hippos/nav/navigate.py",
    ]
    index = {
        "files": {
            "src/hippos/tools/ranker/ranker_graph.py": {
                "signatures": [{"name": "GraphRanker"}, {"name": "rank_files"}]
            }
        }
    }
    query = "Please inspect GraphRanker rank_files in ranker_graph implementation"

    mentioned_files, mentioned_idents = extract_mentions(
        query=query,
        all_files=all_files,
        index=index,
    )

    assert "src/hippos/tools/ranker/ranker_graph.py" in mentioned_files
    assert "GraphRanker" in mentioned_idents
    assert "rank_files" in mentioned_idents


def test_extract_mentions_filters_noise_tokens() -> None:
    all_files = ["src/hippos/nav/navigate.py"]
    index = {"files": {}}
    query = "fix bug add to in on 12 ok"

    _, mentioned_idents = extract_mentions(
        query=query,
        all_files=all_files,
        index=index,
    )

    assert mentioned_idents == set()


def test_validate_repo_paths_filters_invalid_and_normalizes(tmp_path: Path) -> None:
    root = tmp_path
    index_files = {
        "src/hippos/tools/ranker/ranker_graph.py",
        "src/hippos/nav/navigate.py",
    }
    candidates = [
        "src/hippos/tools/ranker/ranker_graph.py",
        "src\\hippos\\nav\\navigate.py",
        "/abs/path.py",
        "../escape.py",
        "unknown.py",
    ]

    validated = validate_repo_paths(
        files=candidates,
        index_files=index_files,
        root=root,
    )

    assert validated == [
        "src/hippos/tools/ranker/ranker_graph.py",
        "src/hippos/nav/navigate.py",
    ]


def test_validate_repo_paths_is_case_insensitive_index(tmp_path: Path) -> None:
    root = tmp_path
    index_files = {"Src/Hippos/Nav/Navigate.Py"}
    validated = validate_repo_paths(
        files=["src/hippos/nav/navigate.py"],
        index_files=index_files,
        root=root,
    )

    assert validated == ["src/hippos/nav/navigate.py"]
