"""Shared policy for progressively disclosed long lists.

The data source remains responsible for ordering the complete result before it
applies a limit.  This module only defines how many already ordered items the
UI asks for and how the explicit, accessible ``loadMore`` row is presented.
"""

from __future__ import annotations

from .list_model import Row


PAGE_SIZE = 150


def requested_count(
    previous_count: int,
    *,
    load_more: bool,
    page_size: int = PAGE_SIZE,
) -> int:
    """Return the cumulative visible item count for one paging request."""

    safe_page_size = max(1, int(page_size))
    safe_previous = max(0, int(previous_count))
    if load_more:
        return max(safe_page_size, safe_previous + safe_page_size)
    return max(safe_page_size, safe_previous)


def load_more_row(
    scope: str,
    loaded_count: int,
    *,
    page_size: int = PAGE_SIZE,
) -> Row:
    """Build a deliberate user-facing row without exposing its model key."""

    safe_page_size = max(1, int(page_size))
    return Row(
        item_id=f"load-more:{scope}:{max(0, int(loaded_count))}",
        title="Załaduj więcej",
        kind="loadMore",
        detail=f"następne {safe_page_size} elementów",
        show_kind=False,
    )
