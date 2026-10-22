"""Self-contained HTML report generator with inline SVG charts and light/dark theme."""

from __future__ import annotations

import html
from typing import Dict, List

from ..models import ActivityHeatmap, RepoReport


def _esc(val: str | int | float) -> str:
    """HTML escape string."""
    return html.escape(str(val))


def _num(val: int | float) -> str:
    """Format number with thousands separator."""
    if isinstance(val, float):
        return f"{val:,.1f}"
    return f"{val:,}"


def _generate_svg_heatmap(heatmap: ActivityHeatmap) -> str:
    """Generate inline SVG for 7x24 weekday-hour activity matrix."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cell_size = 18
    gap = 3
    margin_left = 40
    margin_top = 25

    width = margin_left + 24 * (cell_size + gap) + 10
    height = margin_top + 7 * (cell_size + gap) + 15
    max_val = heatmap.max_val or 1

    svg_parts = [
        f'<svg viewBox="0 0 {width} {height}" class="chart-svg heatmap-svg" role="img" aria-label="Weekday-Hour Activity Heatmap">',
    ]

    # Hour labels on top
    for h in range(0, 24, 2):
        x = margin_left + h * (cell_size + gap) + (cell_size // 2)
        svg_parts.append(f'<text x="{x}" y="{margin_top - 8}" class="svg-label" text-anchor="middle">{h:02d}</text>')

    # Rows
    for day_idx, day_name in enumerate(days):
        y = margin_top + day_idx * (cell_size + gap)
        # Day label
        svg_parts.append(f'<text x="{margin_left - 8}" y="{y + cell_size - 4}" class="svg-label" text-anchor="end">{day_name}</text>')

        for hour in range(24):
            val = heatmap.grid[day_idx][hour]
            x = margin_left + hour * (cell_size + gap)

            if val == 0:
                level = 0
            else:
                ratio = val / max_val
                if ratio <= 0.25:
                    level = 1
                elif ratio <= 0.50:
                    level = 2
                elif ratio <= 0.75:
                    level = 3
                else:
                    level = 4

            tooltip = f"{day_name} {hour:02d}:00 - {_num(val)} commits"
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="3" class="heat-cell heat-{level}">'
                f'<title>{tooltip}</title>'
                f'</rect>'
            )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def _generate_svg_weekly_timeline(commits_by_week: Dict[str, int]) -> str:
    """Generate inline SVG bar timeline of commits per week."""
    if not commits_by_week:
        return '<p class="empty-state">No timeline activity to display.</p>'

    weeks = list(commits_by_week.keys())
    # Limit to at most the last 52 weeks if history is long
    display_weeks = weeks[-52:]
    counts = [commits_by_week[w] for w in display_weeks]
    max_count = max(counts, default=1) or 1

    chart_w = 780
    chart_h = 160
    margin_l = 40
    margin_b = 30
    margin_t = 15
    plot_w = chart_w - margin_l - 15
    plot_h = chart_h - margin_b - margin_t

    n = len(display_weeks)
    bar_slot = plot_w / max(1, n)
    bar_w = max(2, bar_slot * 0.75)

    svg_parts = [
        f'<svg viewBox="0 0 {chart_w} {chart_h}" class="chart-svg timeline-svg" role="img" aria-label="Weekly Commit Timeline">',
        # Background horizontal grid line
        f'<line x1="{margin_l}" y1="{margin_t}" x2="{chart_w - 15}" y2="{margin_t}" class="grid-line" />',
        f'<line x1="{margin_l}" y1="{margin_t + plot_h / 2}" x2="{chart_w - 15}" y2="{margin_t + plot_h / 2}" class="grid-line" />',
        f'<line x1="{margin_l}" y1="{margin_t + plot_h}" x2="{chart_w - 15}" y2="{margin_t + plot_h}" class="grid-line-base" />',
        # Y axis labels
        f'<text x="{margin_l - 6}" y="{margin_t + 4}" class="svg-label" text-anchor="end">{max_count}</text>',
        f'<text x="{margin_l - 6}" y="{margin_t + plot_h / 2 + 4}" class="svg-label" text-anchor="end">{max_count // 2}</text>',
        f'<text x="{margin_l - 6}" y="{margin_t + plot_h + 4}" class="svg-label" text-anchor="end">0</text>',
    ]

    for idx, (week, count) in enumerate(zip(display_weeks, counts)):
        bx = margin_l + idx * bar_slot + (bar_slot - bar_w) / 2
        bh = (count / max_count) * plot_h
        by = margin_t + plot_h - bh

        svg_parts.append(
            f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="2" class="timeline-bar">'
            f'<title>{_esc(week)}: {_num(count)} commits</title>'
            f'</rect>'
        )

        # Labels for every 6-8 weeks or first/last
        if idx == 0 or idx == n - 1 or idx % 8 == 0:
            label_x = bx + bar_w / 2
            svg_parts.append(f'<text x="{label_x:.1f}" y="{chart_h - 10}" class="svg-label" text-anchor="middle">{_esc(week[-5:])}</text>')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def _generate_svg_top_authors(report: RepoReport, top_n: int = 8) -> str:
    """Generate horizontal bar chart for top authors by commits."""
    authors = report.authors[:top_n]
    if not authors:
        return '<p class="empty-state">No authors found.</p>'

    max_commits = max((a.commits_count for a in authors), default=1) or 1
    chart_w = 580
    row_h = 28
    chart_h = len(authors) * row_h + 20
    label_w = 140
    plot_w = chart_w - label_w - 90

    svg_parts = [
        f'<svg viewBox="0 0 {chart_w} {chart_h}" class="chart-svg author-svg" role="img" aria-label="Top Authors Chart">',
    ]

    for idx, a in enumerate(authors):
        y = idx * row_h + 12
        bar_len = (a.commits_count / max_commits) * plot_w
        short_name = a.name[:18] + ("…" if len(a.name) > 18 else "")

        svg_parts.append(f'<text x="{label_w - 10}" y="{y + 14}" class="svg-label author-name" text-anchor="end">{_esc(short_name)}</text>')
        svg_parts.append(
            f'<rect x="{label_w}" y="{y}" width="{max(2.0, bar_len):.1f}" height="18" rx="3" class="author-bar">'
            f'<title>{_esc(a.name)}: {_num(a.commits_count)} commits ({a.percentage_commits:.1f}%)</title>'
            f'</rect>'
        )
        svg_parts.append(f'<text x="{label_w + bar_len + 8:.1f}" y="{y + 14}" class="svg-label-bold">{_num(a.commits_count)} ({a.percentage_commits:.1f}%)</text>')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def _generate_svg_language_distribution(report: RepoReport, top_n: int = 7) -> str:
    """Generate stacked horizontal distribution bar and legend for languages."""
    languages = report.languages[:top_n]
    if not languages:
        return '<p class="empty-state">No languages detected.</p>'

    palette = [
        "#3b82f6",  # blue
        "#10b981",  # emerald
        "#f59e0b",  # amber
        "#ef4444",  # red
        "#8b5cf6",  # violet
        "#06b6d4",  # cyan
        "#ec4899",  # pink
        "#64748b",  # slate
    ]

    total_pct = sum(l.percentage_lines for l in languages)
    # Remaining percentage for "Other"
    other_pct = max(0.0, 100.0 - total_pct)

    chart_w = 600
    bar_h = 24

    svg_parts = [
        f'<svg viewBox="0 0 {chart_w} {bar_h + 8}" class="chart-svg lang-bar-svg" role="img" aria-label="Languages Distribution Bar">',
    ]

    current_x = 0.0
    for idx, lang in enumerate(languages):
        color = palette[idx % len(palette)]
        segment_w = (lang.percentage_lines / 100.0) * chart_w
        if segment_w > 0.5:
            svg_parts.append(
                f'<rect x="{current_x:.1f}" y="4" width="{segment_w:.1f}" height="{bar_h}" fill="{color}" rx="0">'
                f'<title>{_esc(lang.language)}: {lang.percentage_lines:.1f}%</title>'
                f'</rect>'
            )
            current_x += segment_w

    if other_pct > 0.5:
        segment_w = (other_pct / 100.0) * chart_w
        svg_parts.append(
            f'<rect x="{current_x:.1f}" y="4" width="{segment_w:.1f}" height="{bar_h}" fill="#94a3b8">'
            f'<title>Others: {other_pct:.1f}%</title>'
            f'</rect>'
        )

    svg_parts.append('</svg>')

    # Legend markup
    legend_items = []
    for idx, lang in enumerate(languages):
        color = palette[idx % len(palette)]
        legend_items.append(
            f'<div class="lang-legend-item">'
            f'<span class="legend-color-dot" style="background-color: {color};"></span>'
            f'<span class="legend-name">{_esc(lang.language)}</span>'
            f'<span class="legend-pct">{lang.percentage_lines:.1f}%</span>'
            f'</div>'
        )
    if other_pct > 0.5:
        legend_items.append(
            f'<div class="lang-legend-item">'
            f'<span class="legend-color-dot" style="background-color: #94a3b8;"></span>'
            f'<span class="legend-name">Others</span>'
            f'<span class="legend-pct">{other_pct:.1f}%</span>'
            f'</div>'
        )

    legend_html = f'<div class="lang-legend-grid">{"".join(legend_items)}</div>'
    return "\n".join(svg_parts) + "\n" + legend_html


def format_html_report(report: RepoReport, top_n: int = 15, timezone_mode: str = "local") -> str:
    """Generate completely self-contained single-file HTML report."""
    active_heatmap = report.heatmap_local if timezone_mode == "local" else report.heatmap_utc
    heatmap_svg = _generate_svg_heatmap(active_heatmap)
    timeline_svg = _generate_svg_weekly_timeline(report.commits_by_week)
    authors_svg = _generate_svg_top_authors(report)
    lang_svg = _generate_svg_language_distribution(report)

    net_lines = report.total_lines_added - report.total_lines_deleted
    first_d = report.first_commit_date[:10] if report.first_commit_date else "N/A"
    last_d = report.last_commit_date[:10] if report.last_commit_date else "N/A"

    # Bus factor summary
    bus_authors_50_html = ""
    if report.bus_factor.authors_50:
        pills = [f'<span class="author-pill">{_esc(a.name)} ({a.percentage:.1f}%)</span>' for a in report.bus_factor.authors_50]
        bus_authors_50_html = f'<div class="bus-pills-container"><strong>50% Coverage:</strong> {" ".join(pills)}</div>'

    # Authors Table Rows
    authors_rows = []
    for a in report.authors[:top_n]:
        authors_rows.append(
            f'<tr>'
            f'<td><strong>{_esc(a.name)}</strong><br><small class="text-muted">{_esc(a.email)}</small></td>'
            f'<td class="text-right">{_num(a.commits_count)}</td>'
            f'<td class="text-right">{a.percentage_commits:.1f}%</td>'
            f'<td class="text-right text-success">+{_num(a.lines_added)}</td>'
            f'<td class="text-right text-danger">-{_num(a.lines_deleted)}</td>'
            f'<td class="text-right">{_num(a.lines_added - a.lines_deleted)}</td>'
            f'<td class="text-right">{a.active_days}</td>'
            f'</tr>'
        )

    # Churn Table Rows
    file_rows = []
    for f in report.files[:top_n]:
        file_rows.append(
            f'<tr>'
            f'<td><code class="file-path">{_esc(f.path)}</code></td>'
            f'<td class="text-right">{_num(f.commits_count)}</td>'
            f'<td class="text-right text-success">+{_num(f.lines_added)}</td>'
            f'<td class="text-right text-danger">-{_num(f.lines_deleted)}</td>'
            f'<td class="text-right"><strong>{_num(f.hotspot_score)}</strong></td>'
            f'</tr>'
        )

    # Languages Table Rows
    lang_rows = []
    for l in report.languages[:top_n]:
        lang_rows.append(
            f'<tr>'
            f'<td><strong>{_esc(l.language)}</strong></td>'
            f'<td class="text-right">{_num(l.files_count)}</td>'
            f'<td class="text-right">{_num(l.commits_count)}</td>'
            f'<td class="text-right text-success">+{_num(l.lines_added)}</td>'
            f'<td class="text-right text-danger">-{_num(l.lines_deleted)}</td>'
            f'<td class="text-right"><strong>{l.percentage_lines:.1f}%</strong></td>'
            f'</tr>'
        )

    anon_badge = '<span class="badge badge-warning">ANONYMIZED</span>' if report.is_anonymized else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Git Stats Lite — {_esc(report.repo_name)}</title>
<style>
:root {{
  --bg-primary: #f8fafc;
  --bg-card: #ffffff;
  --text-main: #0f172a;
  --text-muted: #64748b;
  --border: #e2e8f0;
  --border-light: #f1f5f9;
  --accent: #2563eb;
  --accent-light: #dbeafe;
  --success: #16a34a;
  --danger: #dc2626;
  --warning: #d97706;

  /* SVG heatmap levels */
  --heat-0: #e2e8f0;
  --heat-1: #93c5fd;
  --heat-2: #3b82f6;
  --heat-3: #1d4ed8;
  --heat-4: #1e3a8a;

  --timeline-bar: #3b82f6;
  --author-bar: #2563eb;
  --grid-line: #e2e8f0;
  --label-color: #64748b;
}}

@media (prefers-color-scheme: dark) {{
  :root {{
    --bg-primary: #0b0f17;
    --bg-card: #151b26;
    --text-main: #f1f5f9;
    --text-muted: #94a3b8;
    --border: #242f42;
    --border-light: #1b2332;
    --accent: #3b82f6;
    --accent-light: #1e293b;
    --success: #22c55e;
    --danger: #ef4444;
    --warning: #f59e0b;

    /* Dark SVG heatmap levels */
    --heat-0: #1b2332;
    --heat-1: #1e3a5f;
    --heat-2: #2563eb;
    --heat-3: #3b82f6;
    --heat-4: #60a5fa;

    --timeline-bar: #3b82f6;
    --author-bar: #60a5fa;
    --grid-line: #242f42;
    --label-color: #94a3b8;
  }}
}}

* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-main);
  line-height: 1.5;
  padding: 2rem 1rem;
}}

.container {{
  max-width: 1200px;
  margin: 0 auto;
}}

header {{
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
}}

.title-section h1 {{
  font-size: 1.85rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}}

.badge {{
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}}

.badge-warning {{
  background-color: var(--warning);
  color: #ffffff;
}}

.meta-info {{
  color: var(--text-muted);
  font-size: 0.875rem;
}}

/* Cards grid */
.cards-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}}

.card {{
  background-color: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}

.card-title {{
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}}

.card-value {{
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-main);
}}

.card-subtext {{
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}}

/* Bus factor alert box */
.bus-factor-banner {{
  background-color: var(--bg-card);
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
  border-radius: 8px;
  padding: 1.25rem;
  margin-bottom: 2rem;
}}

.bus-factor-banner h3 {{
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}}

.bus-pills-container {{
  margin-top: 0.75rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}}

.author-pill {{
  background-color: var(--accent-light);
  color: var(--accent);
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 600;
}}

/* Two column layout */
.layout-grid {{
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}}

@media (min-width: 900px) {{
  .layout-grid-2 {{
    grid-template-columns: 1fr 1fr;
  }}
}}

.section-box {{
  background-color: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}

.section-title {{
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 1.25rem;
  color: var(--text-main);
}}

/* SVG styles */
.chart-svg {{
  width: 100%;
  height: auto;
  display: block;
}}

.svg-label {{
  font-size: 10px;
  fill: var(--label-color);
  font-family: inherit;
}}

.svg-label-bold {{
  font-size: 11px;
  font-weight: 600;
  fill: var(--text-main);
  font-family: inherit;
}}

.heat-cell {{
  transition: opacity 0.15s ease;
  cursor: pointer;
}}
.heat-cell:hover {{
  opacity: 0.8;
  stroke: var(--text-main);
  stroke-width: 1px;
}}
.heat-0 {{ fill: var(--heat-0); }}
.heat-1 {{ fill: var(--heat-1); }}
.heat-2 {{ fill: var(--heat-2); }}
.heat-3 {{ fill: var(--heat-3); }}
.heat-4 {{ fill: var(--heat-4); }}

.grid-line {{
  stroke: var(--grid-line);
  stroke-width: 1;
  stroke-dasharray: 3 3;
}}
.grid-line-base {{
  stroke: var(--border);
  stroke-width: 1;
}}

.timeline-bar {{
  fill: var(--timeline-bar);
  transition: opacity 0.15s;
  cursor: pointer;
}}
.timeline-bar:hover {{
  opacity: 0.8;
}}

.author-bar {{
  fill: var(--author-bar);
  transition: opacity 0.15s;
}}
.author-bar:hover {{
  opacity: 0.85;
}}

/* Language legend */
.lang-legend-grid {{
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1rem;
}}

.lang-legend-item {{
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
}}

.legend-color-dot {{
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}}

.legend-name {{
  font-weight: 500;
}}

.legend-pct {{
  color: var(--text-muted);
}}

/* Tables */
.table-wrapper {{
  overflow-x: auto;
}}

table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}}

th, td {{
  padding: 0.65rem 0.85rem;
  border-bottom: 1px solid var(--border-light);
  text-align: left;
}}

th {{
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border);
}}

tr:hover td {{
  background-color: var(--border-light);
}}

.text-right {{ text-align: right; }}
.text-success {{ color: var(--success); }}
.text-danger {{ color: var(--danger); }}
.text-muted {{ color: var(--text-muted); }}

code.file-path {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.8rem;
  background-color: var(--bg-primary);
  padding: 0.15rem 0.35rem;
  border-radius: 4px;
}}

footer {{
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
  text-align: center;
  font-size: 0.8rem;
  color: var(--text-muted);
}}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="title-section">
      <h1>git-stats-lite: {_esc(report.repo_name)} {anon_badge}</h1>
    </div>
    <div class="meta-info">
      Branch: <strong>{_esc(report.branch)}</strong> &bull; Generated: {_esc(report.generated_at[:19].replace('T', ' '))} UTC
    </div>
  </header>

  <!-- Metric summary cards -->
  <div class="cards-grid">
    <div class="card">
      <div class="card-title">Total Commits</div>
      <div class="card-value">{_num(report.total_commits)}</div>
      <div class="card-subtext">{_num(report.active_days_count)} active days</div>
    </div>
    <div class="card">
      <div class="card-title">Authors</div>
      <div class="card-value">{_num(report.total_authors)}</div>
      <div class="card-subtext">contributors</div>
    </div>
    <div class="card">
      <div class="card-title">Files Touched</div>
      <div class="card-value">{_num(report.total_files_touched)}</div>
      <div class="card-subtext">tracked paths</div>
    </div>
    <div class="card">
      <div class="card-title">Net Lines</div>
      <div class="card-value">{_num(net_lines)}</div>
      <div class="card-subtext text-success">+{_num(report.total_lines_added)} / <span class="text-danger">-{_num(report.total_lines_deleted)}</span></div>
    </div>
    <div class="card">
      <div class="card-title">Bus Factor (50%)</div>
      <div class="card-value">{report.bus_factor.bus_factor_50}</div>
      <div class="card-subtext">min authors for 50% lines</div>
    </div>
    <div class="card">
      <div class="card-title">Bus Factor (80%)</div>
      <div class="card-value">{report.bus_factor.bus_factor_80}</div>
      <div class="card-subtext">min authors for 80% lines</div>
    </div>
  </div>

  <!-- Bus factor banner -->
  <div class="bus-factor-banner">
    <h3>Bus Factor Risk Assessment (Last {report.bus_factor.window_months} Months)</h3>
    <p class="text-muted">
      A bus factor of <strong>{report.bus_factor.bus_factor_50}</strong> indicates that {report.bus_factor.bus_factor_50} contributor(s) account for more than 50% of recent code modifications, and <strong>{report.bus_factor.bus_factor_80}</strong> contributor(s) account for 80%.
    </p>
    {bus_authors_50_html}
  </div>

  <!-- Charts layout -->
  <div class="layout-grid">
    <div class="section-box">
      <h2 class="section-title">Weekday-Hour Activity Heatmap ({timezone_mode.upper()})</h2>
      {heatmap_svg}
    </div>
  </div>

  <div class="layout-grid layout-grid-2">
    <div class="section-box">
      <h2 class="section-title">Commits by Week (Timeline)</h2>
      {timeline_svg}
    </div>
    <div class="section-box">
      <h2 class="section-title">Top Authors (Commits)</h2>
      {authors_svg}
    </div>
  </div>

  <div class="layout-grid">
    <div class="section-box">
      <h2 class="section-title">Language Distribution (Lines Changed)</h2>
      {lang_svg}
    </div>
  </div>

  <!-- Tables layout -->
  <div class="layout-grid">
    <div class="section-box">
      <h2 class="section-title">Top Authors ({min(top_n, len(report.authors))})</h2>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Author</th>
              <th class="text-right">Commits</th>
              <th class="text-right">% Commits</th>
              <th class="text-right">Added</th>
              <th class="text-right">Deleted</th>
              <th class="text-right">Net</th>
              <th class="text-right">Active Days</th>
            </tr>
          </thead>
          <tbody>
            {"".join(authors_rows) if authors_rows else '<tr><td colspan="7" class="text-muted">No authors found</td></tr>'}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="layout-grid layout-grid-2">
    <div class="section-box">
      <h2 class="section-title">Churn & Hotspots ({min(top_n, len(report.files))})</h2>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>File Path</th>
              <th class="text-right">Commits</th>
              <th class="text-right">Added</th>
              <th class="text-right">Deleted</th>
              <th class="text-right">Hotspot</th>
            </tr>
          </thead>
          <tbody>
            {"".join(file_rows) if file_rows else '<tr><td colspan="5" class="text-muted">No files found</td></tr>'}
          </tbody>
        </table>
      </div>
    </div>

    <div class="section-box">
      <h2 class="section-title">Languages by Extension</h2>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Language</th>
              <th class="text-right">Files</th>
              <th class="text-right">Commits</th>
              <th class="text-right">Added</th>
              <th class="text-right">Deleted</th>
              <th class="text-right">% Lines</th>
            </tr>
          </thead>
          <tbody>
            {"".join(lang_rows) if lang_rows else '<tr><td colspan="6" class="text-muted">No languages found</td></tr>'}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <footer>
    Generated by <strong>git-stats-lite</strong> &bull; Zero external dependencies &bull; Privacy-first local git statistics
  </footer>
</div>
</body>
</html>
"""
