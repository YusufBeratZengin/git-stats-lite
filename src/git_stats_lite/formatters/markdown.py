"""Markdown report formatter for git-stats-lite."""

from __future__ import annotations

from ..models import RepoReport


def _num(n: float) -> str:
    if isinstance(n, float):
        return f"{n:,.1f}"
    return f"{n:,}"


def format_markdown_report(report: RepoReport, top_n: int = 15, timezone_mode: str = "local") -> str:
    """Render repository report as GitHub Flavored Markdown."""
    lines: list[str] = []

    anon_badge = " *(anonymized)*" if report.is_anonymized else ""
    lines.append(f"# Git Stats Lite: {report.repo_name}{anon_badge}")
    lines.append("")
    lines.append(f"> Generated on {report.generated_at[:19].replace('T', ' ')} UTC for branch `{report.branch}`.")
    lines.append("")

    # Summary
    lines.append("## Repository Overview")
    lines.append("")
    lines.append(f"- **Path:** `{report.repo_path}`")
    first_d = report.first_commit_date[:10] if report.first_commit_date else "N/A"
    last_d = report.last_commit_date[:10] if report.last_commit_date else "N/A"
    lines.append(f"- **Date Range:** {first_d} to {last_d} ({report.active_days_count} active days)")
    lines.append(f"- **Total Commits:** {_num(report.total_commits)}")
    lines.append(f"- **Total Authors:** {_num(report.total_authors)}")
    lines.append(f"- **Files Touched:** {_num(report.total_files_touched)}")
    lines.append(f"- **Lines Added / Deleted:** +{_num(report.total_lines_added)} / -{_num(report.total_lines_deleted)} (net: {_num(report.total_lines_added - report.total_lines_deleted)})")
    lines.append("")

    # Bus factor
    lines.append("## Bus Factor")
    lines.append("")
    lines.append(f"- **Bus Factor (50% churn threshold):** **{report.bus_factor.bus_factor_50}** author(s)")
    lines.append(f"- **Bus Factor (80% churn threshold):** **{report.bus_factor.bus_factor_80}** author(s)")
    lines.append(f"- **Evaluation Window:** Last {report.bus_factor.window_months} months")
    lines.append("")
    if report.bus_factor.authors_50:
        lines.append("### Key Contributors (50% Lines Changed)")
        lines.append("")
        lines.append("| Author | Lines Changed | Churn Share |")
        lines.append("| :--- | ---: | ---: |")
        for a in report.bus_factor.authors_50:
            lines.append(f"| {a.name} | {_num(a.lines_changed)} | {a.percentage:.1f}% |")
        lines.append("")

    # Top Authors Table
    lines.append(f"## Top Authors (Top {min(top_n, len(report.authors))})")
    lines.append("")
    lines.append("| Author | Commits | % Commits | Added | Deleted | Net | Active Days |")
    lines.append("| :--- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for author in report.authors[:top_n]:
        net = author.lines_added - author.lines_deleted
        lines.append(
            f"| {author.name} | {_num(author.commits_count)} | {author.percentage_commits:.1f}% | "
            f"+{_num(author.lines_added)} | -{_num(author.lines_deleted)} | {_num(net)} | {author.active_days} |"
        )
    lines.append("")

    # Languages Table
    lines.append(f"## Languages by Extension (Top {min(top_n, len(report.languages))})")
    lines.append("")
    lines.append("| Language | Files | Commits | Added | Deleted | % Lines |")
    lines.append("| :--- | ---: | ---: | ---: | ---: | ---: |")
    for l in report.languages[:top_n]:
        lines.append(
            f"| {l.language} | {_num(l.files_count)} | {_num(l.commits_count)} | "
            f"+{_num(l.lines_added)} | -{_num(l.lines_deleted)} | {l.percentage_lines:.1f}% |"
        )
    lines.append("")

    # File Churn Table
    lines.append(f"## Hotspots & Churn (Top {min(top_n, len(report.files))})")
    lines.append("")
    lines.append("| File Path | Commits | Changes (+/-) | Hotspot Score |")
    lines.append("| :--- | ---: | ---: | ---: |")
    for f in report.files[:top_n]:
        lines.append(f"| `{f.path}` | {_num(f.commits_count)} | {_num(f.lines_changed)} | {_num(f.hotspot_score)} |")
    lines.append("")

    # Activity Heatmap Summary
    active_heatmap = report.heatmap_local if timezone_mode == "local" else report.heatmap_utc
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    lines.append(f"## Activity Heatmap ({timezone_mode.upper()} Time)")
    lines.append("")
    lines.append("| Day | " + " | ".join(f"{h:02d}" for h in range(24)) + " | Total |")
    lines.append("| :--- |" + " ---: |" * 24 + " ---: |")
    for day_idx, day_name in enumerate(days):
        row_vals = [str(active_heatmap.grid[day_idx][h]) for h in range(24)]
        day_total = sum(active_heatmap.grid[day_idx])
        lines.append(f"| {day_name} | " + " | ".join(row_vals) + f" | {_num(day_total)} |")
    lines.append("")

    return "\n".join(lines)
