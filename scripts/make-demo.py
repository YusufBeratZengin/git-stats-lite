#!/usr/bin/env python3
"""Generate docs/demo.svg from real CLI output."""

from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_real_output() -> list[str]:
    """Run CLI against repository and capture real output lines."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "src" / "git_stats_lite" / "cli.py"),
        ".",
        "--top",
        "4",
    ]
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    raw_lines = res.stdout.splitlines()

    # Sanitize any absolute local paths to relative repo name
    clean_lines: list[str] = []
    repo_path_pattern = re.compile(r"^(Repository Path\s*:\s*).*$", re.MULTILINE)

    for line in raw_lines:
        m = repo_path_pattern.match(line)
        if m:
            clean_lines.append(f"{m.group(1)}git-stats-lite")
        else:
            clean_lines.append(line)

    # Build clean output: Command, Overview card, Bus factor contributor, and Languages breakdown
    selected_lines: list[str] = ["$ git-stats . --top 4"]

    # Gather overview lines up to before '--- Top Authors'
    in_overview = True
    languages_lines: list[str] = []
    in_languages = False

    for line in clean_lines:
        if line.startswith("--- Top Authors"):
            in_overview = False
            continue
        if in_overview:
            selected_lines.append(line)
        elif line.startswith("--- Languages by Extension"):
            in_languages = True
            languages_lines.append(line)
        elif in_languages:
            if line.startswith("--- Churn"):
                break
            languages_lines.append(line)

    # Clean empty lines between overview and languages
    while selected_lines and not selected_lines[-1].strip():
        selected_lines.pop()

    selected_lines.append("")
    selected_lines.extend(languages_lines)

    while selected_lines and not selected_lines[-1].strip():
        selected_lines.pop()

    return selected_lines


def render_svg(lines: list[str]) -> str:
    """Render terminal lines into a polished dark-mode SVG terminal window."""
    line_height = 22
    padding_x = 24
    padding_top = 54
    padding_bottom = 20

    total_height = padding_top + (len(lines) * line_height) + padding_bottom
    width = 720

    svg_lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {total_height}" width="{width}" height="{total_height}">',
        "  <defs>",
        '    <linearGradient id="terminal-header" x1="0%" y1="0%" x2="0%" y2="100%">',
        '      <stop offset="0%" stop-color="#21262d" />',
        '      <stop offset="100%" stop-color="#161b22" />',
        "    </linearGradient>",
        '    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">',
        '      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#010409" flood-opacity="0.6" />',
        "    </filter>",
        "  </defs>",
        "  <style>",
        "    .term-window { fill: #0d1117; stroke: #30363d; stroke-width: 1px; }",
        "    .term-header { fill: url(#terminal-header); stroke: #30363d; stroke-width: 1px; }",
        '    .term-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 12px; fill: #8b949e; text-anchor: middle; font-weight: 500; }',
        '    .term-text { font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace; font-size: 13px; line-height: 22px; }',
        "  </style>",
        f'  <rect x="1" y="1" width="{width - 2}" height="{total_height - 2}" rx="8" class="term-window" filter="url(#shadow)" />',
        f'  <path d="M 1 9 A 8 8 0 0 1 9 1 L {width - 9} 1 A 8 8 0 0 1 {width - 1} 9 L {width - 1} 36 L 1 36 Z" class="term-header" />',
        '  <circle cx="20" cy="19" r="6" fill="#ff5f56" />',
        '  <circle cx="40" cy="19" r="6" fill="#ffbd2e" />',
        '  <circle cx="60" cy="19" r="6" fill="#27c93f" />',
        f'  <text x="{width // 2}" y="23" class="term-title">git-stats-lite — terminal demo</text>',
        '  <g class="term-text">',
    ]

    for idx, line in enumerate(lines):
        y_pos = padding_top + (idx * line_height)
        escaped = html.escape(line)

        # Syntax colorization based on content
        if line.startswith("$"):
            colored = f'<tspan fill="#7ee787">$</tspan> <tspan fill="#f0f6fc" font-weight="bold">{html.escape(line[2:])}</tspan>'
        elif line.startswith("==="):
            colored = f'<tspan fill="#30363d">{escaped}</tspan>'
        elif "GIT STATS LITE:" in line:
            colored = f'<tspan fill="#58a6ff" font-weight="bold">{escaped}</tspan>'
        elif line.startswith("--- Languages"):
            colored = f'<tspan fill="#79c0ff" font-weight="bold">{escaped}</tspan>'
        elif line.startswith("Language") and "|" in line:
            colored = f'<tspan fill="#f0f6fc" font-weight="bold">{escaped}</tspan>'
        elif line.startswith("---") and "+" in line:
            colored = f'<tspan fill="#30363d">{escaped}</tspan>'
        elif ":" in line and not line.startswith(" "):
            parts = line.split(":", 1)
            key_part = html.escape(parts[0] + ":")
            val_part = parts[1]

            if "+" in val_part and "-" in val_part and "Lines Changed" in parts[0]:
                val_colored = re.sub(r"(\+[\d,]+)", r'<tspan fill="#3fb950">\1</tspan>', html.escape(val_part))
                val_colored = re.sub(r"(-[\d,]+)", r'<tspan fill="#f85149">\1</tspan>', val_colored)
                val_part_html = val_colored
            elif "Bus Factor" in parts[0]:
                val_part_html = re.sub(r"(\d+\s+author\(s\))", r'<tspan fill="#d2a8ff" font-weight="bold">\1</tspan>', html.escape(val_part))
            else:
                val_part_html = f'<tspan fill="#c9d1d9">{html.escape(val_part)}</tspan>'

            colored = f'<tspan fill="#8b949e">{key_part}</tspan>{val_part_html}'
        elif line.startswith("Primary contributors"):
            colored = f'<tspan fill="#79c0ff">{escaped}</tspan>'
        elif "|" in line:
            parts = [html.escape(p) for p in line.split("|")]
            if len(parts) >= 6:
                parts[0] = f'<tspan fill="#f0f6fc">{parts[0]}</tspan>'
                parts[3] = f'<tspan fill="#3fb950">{parts[3]}</tspan>'
                parts[4] = f'<tspan fill="#f85149">{parts[4]}</tspan>'
                parts[5] = f'<tspan fill="#79c0ff">{parts[5]}</tspan>'
                colored = '<tspan fill="#30363d">|</tspan>'.join(parts)
            else:
                colored = f'<tspan fill="#c9d1d9">{escaped}</tspan>'
        else:
            colored = f'<tspan fill="#c9d1d9">{escaped}</tspan>'

        svg_lines.append(f'    <text x="{padding_x}" y="{y_pos}">{colored}</text>')

    svg_lines.append("  </g>")
    svg_lines.append("</svg>")
    svg_lines.append("")

    return "\n".join(svg_lines)


def main() -> None:
    lines = get_real_output()
    svg_content = render_svg(lines)

    docs_dir = REPO_ROOT / "docs"
    docs_dir.mkdir(exist_ok=True)
    svg_path = docs_dir / "demo.svg"

    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"Generated {svg_path} ({len(lines)} lines of output)")


if __name__ == "__main__":
    main()
