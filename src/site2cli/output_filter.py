"""Output filtering for run command results."""

from __future__ import annotations

import re
from typing import Any


def filter_result(
    data: dict | list,
    grep: str | None = None,
    limit: int | None = None,
    keys_only: bool = False,
) -> dict | list | Any:
    """Filter and transform command output.

    Args:
        data: Raw result data (dict or list).
        grep: Regex pattern to filter dict keys.
        limit: Maximum number of items for list results.
        keys_only: Return only top-level keys (for dicts).

    Returns:
        Filtered data.
    """
    result = data

    # Apply grep filter on dict keys
    if grep and isinstance(result, dict):
        pattern = re.compile(grep, re.IGNORECASE)
        result = {k: v for k, v in result.items() if pattern.search(str(k))}

    # Keys only
    if keys_only and isinstance(result, dict):
        return list(result.keys())

    # Apply limit on lists
    if limit is not None and isinstance(result, list):
        result = result[:limit]
    elif limit is not None and isinstance(result, dict):
        # For dicts with list values, limit each list
        result = {
            k: v[:limit] if isinstance(v, list) else v
            for k, v in result.items()
        }

    return result
