"""Terminal table formatter for git-stats-lite."""

from __future__ import annotations

from typing import List

from ..models import ActivityHeatmap, RepoReport


def _format_num(n: int | float) -> str:
    """Format number with thousands comma separator."""
    if isinstance(n, float):
        return f"{n:,.1f}"
    return f"{n:,}"


def _format_table(headers: List[str], rows: List[List[str]], alignments: List[str]) -> str:
    """Render a clean text table with headers, borders, and column alignments."""
    if not headers:
        return ""

    num_cols = len(headers)
    col_widths = [len(h) for h in headers]

    for row in rows:
        for i in range(min(num_cols, len(row))):
            col_widths[i] = max(col_widths[i], len(row[i]))

    # Formatting borders
    header_cells = []
    separator_cells = []
    for i, h in enumerate(headers):
        align = alignments[i] if i < len(alignments) else "left"
        width = col_widths[i]
        if align == "right":
            header_cells.append(h.rjust(width))
        else:
            header_cells.append(h.ljust(width))
        separator_cells.append("-" * width)

    header_line = " | ".join(header_cells)
    sep_line = "-+-".join(separator_cells)

    data_lines = []
    for row in rows:
        cells = []
        for i in range(num_cols):
            val = row[i] if i < len(row) else ""
            align = alignments[i] if i < len(alignments) else "left"
            width = col_widths[i]
            if align == "right":
                cells.append(val.rjust(width))
            else:
                cells.append(val.ljust(width))
        data_lines.append(" | ".join(cells))

    return "\n".join([header_line, sep_line] + data_lines)


def _render_ascii_heatmap(heatmap: ActivityHeatmap) -> str:
    """Render a compact 7x24 weekday-hour ASCII heatmap."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    shades = [" ", ".", ":", "*", "#"]
    max_val = heatmap.max_val or 1

    lines = []
    # Header for hours (0, 3, 6, 9, 12, 15, 18, 21)
    lines.append("      00 02 04 06 08 10 12 14 16 18 20 22")
    lines.append("     +------------------------------------------------")

    for day_idx, day_name in enumerate(days):
        row_chars = []
        for hour in range(24):
            val = heatmap.grid[day_idx][hour]
            if val == 0:
                char = "·"
            else:
                ratio = val / max_val
                shade_idx = min(len(shades) - 1, int(ratio * (len(shades) - 1)) + 1)
                char = shades[shade_idx]
            row_chars.append(f"{char} ")
        lines.append(f"{day_name}  | " + "".join(row_chars))

    lines.append(f"     +------------------------------------------------ (max cell: {max_val} commits)")
    return "\n".join(lines)


def format_terminal_report(report: RepoReport, top_n: int = 10, timezone_mode: str = "local") -> str:
    """Format full repository report for terminal display."""
    output_parts: List[str] = []

    # Title & Overview Card
    title = f"GIT STATS LITE: {report.repo_name}"
    line_border = "=" * max(60, len(title) + 8)
    output_parts.append(line_border)
    output_parts.append(f" {title} ")
    output_parts.append(line_border)

    anon_status = " [ANONYMIZED]" if report.is_anonymized else ""
    date_range = f"{report.first_commit_date[:10] if report.first_commit_date else 'N/A'} to {report.last_commit_date[:10] if report.last_commit_date else 'N/A'}"

    overview_rows = [
        f"Repository Path   : {report.repo_path}",
        f"Branch            : {report.branch}{anon_status}",
        f"History Range     : {date_range}",
        f"Total Commits     : {_format_num(report.total_commits)} (over {report.active_days_count} active days)",
        f"Total Authors     : {_format_num(report.total_authors)}",
        f"Files Touched     : {_format_num(report.total_files_touched)}",
        f"Lines Changed     : +{_format_num(report.total_lines_added)} / -{_format_num(report.total_lines_deleted)} (net: {_format_num(report.total_lines_added - report.total_lines_deleted)})",
        f"Bus Factor (50%)  : {report.bus_factor.bus_factor_50} author(s) (window: {report.bus_factor.window_months}m)",
        f"Bus Factor (80%)  : {report.bus_factor.bus_factor_80} author(s) (window: {report.bus_factor.window_months}m)",
    ]
    output_parts.extend(overview_rows)
    output_parts.append("")

    # Bus factor breakdown
    if report.bus_factor.authors_50:
        names_50 = ", ".join(f"{a.name} ({a.percentage:.1f}%)" for a in report.bus_factor.authors_50[:5])
        output_parts.append(f"Primary contributors covering 50% churn: {names_50}")
        output_parts.append("")

    # Top Authors Table
    output_parts.append(f"--- Top Authors (Top {min(top_n, len(report.authors))}) ---")
    author_headers = ["Author", "Email", "Commits", "% Commits", "Added", "Deleted", "Days"]
    author_aligns = ["left", "left", "right", "right", "right", "right", "right"]
    author_rows = []
    for a in report.authors[:top_n]:
        author_rows.append([
            a.name,
            a.email,
            _format_num(a.commits_count),
            f"{a.percentage_commits:.1f}%",
            f"+{_format_num(a.lines_added)}",
            f"-{_format_num(a.lines_deleted)}",
            str(a.active_days),
        ])
    if author_rows:
        output_parts.append(_format_table(author_headers, author_rows, author_aligns))
    else:
        output_parts.append("No authors found.")
    output_parts.append("")

    # Language Breakdown Table
    output_parts.append(f"--- Languages by Extension (Top {min(top_n, len(report.languages))}) ---")
    lang_headers = ["Language", "Files", "Commits", "Lines Added", "Lines Deleted", "% Lines"]
    lang_aligns = ["left", "right", "right", "right", "right", "right"]
    lang_rows = []
    for l in report.languages[:top_n]:
        lang_rows.append([
            l.language,
            _format_num(l.files_count),
            _format_num(l.commits_count),
            f"+{_format_num(l.lines_added)}",
            f"-{_format_num(l.lines_deleted)}",
            f"{l.percentage_lines:.1f}%",
        ])
    if lang_rows:
        output_parts.append(_format_table(lang_headers, lang_rows, lang_aligns))
    else:
        output_parts.append("No file diffs detected.")
    output_parts.append("")

    # File Churn and Hotspots Table
    output_parts.append(f"--- Churn & Hotspots (Top {min(top_n, len(report.files))}) ---")
    file_headers = ["File Path", "Commits", "Changes (+/-)", "Hotspot Score"]
    file_aligns = ["left", "right", "right", "right"]
    file_rows = []
    for f in report.files[:top_n]:
        file_rows.append([
            f.path,
            _format_num(f.commits_count),
            _format_num(f.lines_changed),
            _format_num(f.hotspot_score),
        ])
    if file_rows:
        output_parts.append(_format_table(file_headers, file_rows, file_aligns))
    else:
        output_parts.append("No modified files recorded.")
    output_parts.append("")

    # Activity Heatmap
    active_heatmap = report.heatmap_local if timezone_mode == "local" else report.heatmap_utc
    output_parts.append(f"--- Activity Heatmap ({timezone_mode.upper()} Time) ---")
    output_parts.append(_render_ascii_heatmap(active_heatmap))
    output_parts.append("")

    return "\n".join(output_parts)
