"""Tree-sitter parsing and tag extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .lang_map import detect_file_language
from .query_loader import load_query


def _normalize_query_for_runtime(lang: str, query_scm: str) -> str:
    """Patch known legacy query/node mismatches for current parser backend."""
    # Legacy javascript tags use "(function)" while newer grammar uses
    # "(function_expression)". Keep existing query files usable, including
    # multiline node forms like "(function\n  name: ...)".
    if lang == "javascript":
        query_scm = re.sub(r"\(function(?=[\s)\]])", "(function_expression", query_scm)
    return query_scm


@dataclass
class Tag:
    """A code tag extracted by tree-sitter."""
    rel_fname: str
    fname: str
    name: str
    kind: str  # "def" or "ref"
    line: int
    tag_type: str = ""  # e.g. "class", "function"


def _get_parser_and_language(lang: str):
    """Get tree-sitter parser and language for a given language name."""
    lang_name = lang.replace("-", "_")

    # Use tree-sitter-language-pack (compatible with tree-sitter 0.25.x)
    try:
        from tree_sitter_language_pack import get_language, get_parser
        ts_lang = get_language(lang_name)
        parser = get_parser(lang_name)
        return parser, ts_lang
    except Exception:
        pass

    # Fallback: try tree_sitter_languages (older versions)
    try:
        from tree_sitter_languages import get_language, get_parser
        ts_lang = get_language(lang_name)
        parser = get_parser(lang_name)
        return parser, ts_lang
    except Exception:
        pass

    return None, None


def _parse_source(parser, code: str):
    """Parse source across tree-sitter parser wrappers with different inputs."""
    try:
        return parser.parse(bytes(code, "utf-8"))
    except TypeError:
        return parser.parse(code)


def _node_text(node) -> str:
    text = node.text
    if isinstance(text, bytes):
        return text.decode("utf-8")
    return str(text)


def _root_node(tree):
    root_node = tree.root_node
    if callable(root_node):
        return root_node()
    return root_node


def _query_captures(ts_lang, query_scm: str, root_node):
    import tree_sitter

    query = tree_sitter.Query(ts_lang, query_scm)

    try:
        cursor = tree_sitter.QueryCursor(query)
        matches = cursor.matches(root_node)
        captures = {}
        for pattern_index, match_captures in matches:
            for capture_name, nodes in match_captures.items():
                if capture_name not in captures:
                    captures[capture_name] = []
                captures[capture_name].extend(nodes)
        return captures
    except (AttributeError, TypeError):
        if hasattr(query, "captures"):
            return query.captures(root_node)
        raise


def _extract_with_language_pack_process(
    fname: str,
    rel_fname: str,
    lang: str,
    code: str,
) -> list[Tag]:
    try:
        from tree_sitter_language_pack import ProcessConfig, process
    except Exception:
        return []

    try:
        result = process(
            code,
            ProcessConfig(
                language=lang,
                structure=False,
                imports=False,
                exports=False,
                comments=False,
                docstrings=False,
                symbols=True,
                diagnostics=False,
            ),
        )
    except Exception:
        return []

    tags: list[Tag] = []
    for symbol in getattr(result, "symbols", None) or []:
        name = getattr(symbol, "name", None)
        if not name:
            continue
        kind_name = str(getattr(symbol, "kind", "")).lower()
        span = getattr(symbol, "span", None)
        line = int(getattr(span, "start_line", 0) or 0)
        tags.append(Tag(
            rel_fname=rel_fname,
            fname=fname,
            name=str(name),
            kind="def",
            line=line,
            tag_type=kind_name,
        ))
    return tags


def extract_tags(
    fname: str,
    rel_fname: str,
    queries_dir: Path,
) -> list[Tag]:
    """Extract definition tags from a source file using tree-sitter.

    Returns a list of Tag objects for definitions found in the file.
    """
    lang = detect_file_language(fname)
    if not lang:
        return []

    parser, ts_lang = _get_parser_and_language(lang)
    if parser is None or ts_lang is None:
        return []

    query_scm = load_query(queries_dir, lang)
    if not query_scm:
        return []
    query_scm = _normalize_query_for_runtime(lang, query_scm)

    try:
        code = Path(fname).read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return []

    if not code:
        return []

    tree = _parse_source(parser, code)
    root_node = _root_node(tree)

    try:
        captures = _query_captures(ts_lang, query_scm, root_node)
    except Exception:
        return _extract_with_language_pack_process(fname, rel_fname, lang, code)

    tags = []
    # tree-sitter 0.23+ returns dict[str, list[Node]]
    if isinstance(captures, dict):
        all_nodes = []
        for tag_name, nodes in captures.items():
            all_nodes += [(node, tag_name) for node in nodes]
    else:
        all_nodes = list(captures)

    for node, tag_name in all_nodes:
        if tag_name.startswith("name.definition."):
            kind = "def"
            tag_type = tag_name.replace("name.definition.", "")
        elif tag_name.startswith("name.reference."):
            kind = "ref"
            tag_type = tag_name.replace("name.reference.", "")
        else:
            continue

        tags.append(Tag(
            rel_fname=rel_fname,
            fname=fname,
            name=_node_text(node),
            kind=kind,
            line=node.start_point[0],
            tag_type=tag_type,
        ))

    return tags


def extract_definitions(
    fname: str,
    rel_fname: str,
    queries_dir: Path,
) -> list[Tag]:
    """Extract only definition tags (no references)."""
    return [t for t in extract_tags(fname, rel_fname, queries_dir)
            if t.kind == "def"]
