"""JSON report serializer for git-stats-lite."""

from __future__ import annotations

import json

from ..models import RepoReport


def format_json_report(report: RepoReport, indent: int = 2) -> str:
    """Format repository report as formatted JSON string."""
    return json.dumps(report.to_dict(), indent=indent, ensure_ascii=False)
