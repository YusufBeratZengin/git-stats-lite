"""Output formatters for git-stats-lite."""

from .html import format_html_report
from .json_fmt import format_json_report
from .markdown import format_markdown_report
from .terminal import format_terminal_report

__all__ = [
    "format_terminal_report",
    "format_json_report",
    "format_markdown_report",
    "format_html_report",
]
