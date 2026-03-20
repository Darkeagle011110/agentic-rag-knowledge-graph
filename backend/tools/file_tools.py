"""
Shared file-access tools used by multiple agents.
Extracted from notebook Lessons 5 & 6.
"""
from __future__ import annotations

import os
from itertools import islice
from pathlib import Path
from typing import Any

from neo4j_client import tool_success, tool_error
from config import get_settings


def _get_data_dir() -> Path:
    return Path(get_settings().data_dir)


# ──────────────────────────────────────────────────────────
# list_available_files
# ──────────────────────────────────────────────────────────
def list_available_files() -> dict[str, Any]:
    """Lists all structured (CSV/JSON) and unstructured (Markdown) files
    available for knowledge graph construction.

    Returns:
        dict: Success dict with key 'all_available_files' listing relative paths,
              or error dict with 'error_message'.
    """
    data_dir = _get_data_dir()
    if not data_dir.exists():
        return tool_error(f"Data directory '{data_dir}' does not exist.")

    file_names = [
        str(x.relative_to(data_dir))
        for x in data_dir.rglob("*")
        if x.is_file()
    ]
    return tool_success("all_available_files", file_names)


# ──────────────────────────────────────────────────────────
# sample_file
# ──────────────────────────────────────────────────────────
def sample_file(file_path: str) -> dict[str, Any]:
    """Samples a file by reading its content as text (up to 100 lines).

    Args:
        file_path: Path relative to the data directory.

    Returns:
        dict: Success dict with 'content', or error dict.
    """
    if Path(file_path).is_absolute():
        return tool_error(
            "File path must be relative to the data directory. "
            "Use paths from list_available_files."
        )

    full_path = _get_data_dir() / file_path
    if not full_path.exists():
        return tool_error(
            f"File does not exist: {file_path}. "
            "Make sure it is from list_available_files."
        )

    try:
        with open(full_path, "r", encoding="utf-8") as fh:
            lines = list(islice(fh, 100))
            content = "".join(lines)
        return tool_success("content", content)
    except Exception as exc:  # pylint: disable=broad-except
        return tool_error(f"Error reading file {file_path}: {exc}")


# ──────────────────────────────────────────────────────────
# search_file  (grep-like)
# ──────────────────────────────────────────────────────────
def search_file(file_path: str, query: str) -> dict[str, Any]:
    """Case-insensitive grep-like search through any text file.

    Args:
        file_path: Path relative to the data directory.
        query: String to search for.

    Returns:
        dict: Success dict with 'search_results' (matching lines + metadata).
    """
    full_path = _get_data_dir() / file_path
    if not full_path.exists():
        return tool_error(f"File does not exist: {file_path}")
    if not full_path.is_file():
        return tool_error(f"Path is not a file: {file_path}")

    if not query:
        return tool_success(
            "search_results",
            {"metadata": {"path": file_path, "query": query, "lines_found": 0},
             "matching_lines": []},
        )

    matching_lines: list[dict] = []
    try:
        with open(full_path, "r", encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                if query.lower() in line.lower():
                    matching_lines.append({"line_number": i, "content": line.strip()})
    except Exception as exc:  # pylint: disable=broad-except
        return tool_error(f"Error searching {file_path}: {exc}")

    return tool_success(
        "search_results",
        {
            "metadata": {
                "path": file_path,
                "query": query,
                "lines_found": len(matching_lines),
            },
            "matching_lines": matching_lines,
        },
    )
