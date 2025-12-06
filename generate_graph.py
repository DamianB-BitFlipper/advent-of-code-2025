#!/usr/bin/env python3
"""Generate a beautiful line graph from REMARKS.md files showing time and LOC per day."""

import re
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def parse_remarks_file(filepath: Path) -> dict | None:
    """Parse a REMARKS.md file and extract time and loc from frontmatter."""
    content = filepath.read_text()

    # Match YAML frontmatter between --- delimiters
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    frontmatter = match.group(1)
    data = {}

    for line in frontmatter.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key in ("time", "loc"):
                data[key] = int(value)

    return data if "time" in data and "loc" in data else None


def find_remarks_files(base_path: Path) -> list[tuple[int, dict]]:
    """Find all REMARKS.md files in day* directories and return sorted data."""
    results = []

    for day_dir in base_path.glob("day*"):
        if not day_dir.is_dir():
            continue

        remarks_file = day_dir / "REMARKS.md"
        if not remarks_file.exists():
            continue

        # Extract day number from directory name
        day_match = re.search(r"day(\d+)", day_dir.name)
        if not day_match:
            continue

        day_num = int(day_match.group(1))
        data = parse_remarks_file(remarks_file)

        if data:
            results.append((day_num, data))

    return sorted(results, key=lambda x: x[0])


def generate_graph(data: list[tuple[int, dict]], output_path: Path) -> None:
    """Generate a beautiful dual-axis line graph using Plotly."""
    if not data:
        print("No data found to plot!")
        return

    days = [d[0] for d in data]
    times = [d[1]["time"] for d in data]
    locs = [d[1]["loc"] for d in data]
    total_time = sum(times)

    # Format total time as hours + minutes if >= 60 minutes
    if total_time >= 60:
        hours, mins = divmod(total_time, 60)
        total_time_str = f"{hours}h {mins}m" if mins else f"{hours}h"
    else:
        total_time_str = f"{total_time}m"

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # LOC trace (secondary y-axis) - added first so Time marker renders on top
    fig.add_trace(
        go.Scatter(
            x=days,
            y=locs,
            name="Lines of Code",
            mode="lines+markers+text",
            text=[f"{loc} LOC" for loc in locs],
            textposition="bottom center",
            textfont=dict(size=14, color="#fbbf24", family="JetBrains Mono, monospace"),
            line=dict(
                color="#f59e0b",
                width=4,
                shape="spline",
                smoothing=0.3,
            ),
            marker=dict(
                size=20,
                color="#f59e0b",
                line=dict(color="#78350f", width=3),
                symbol="diamond",
            ),
            hovertemplate="<b>Day %{x}</b><br>LOC: %{y}<extra></extra>",
            legendrank=2,
            cliponaxis=False,
        ),
        secondary_y=True,
    )

    # Time trace (primary y-axis) - added second so it renders on top
    fig.add_trace(
        go.Scatter(
            x=days,
            y=times,
            name="Time (min)",
            mode="lines+markers+text",
            text=[f"{t} min" for t in times],
            textposition="top center",
            textfont=dict(size=14, color="#34d399", family="JetBrains Mono, monospace"),
            line=dict(
                color="#10b981",
                width=4,
                shape="spline",
                smoothing=0.3,
            ),
            marker=dict(
                size=18,
                color="#10b981",
                line=dict(color="#064e3b", width=3),
                symbol="circle",
            ),
            hovertemplate="<b>Day %{x}</b><br>Time: %{y} min<extra></extra>",
            legendrank=1,
            cliponaxis=False,
        ),
        secondary_y=False,
    )

    # Update layout for mobile/Twitter optimized dark theme
    fig.update_layout(
        title=dict(
            text=f"<b>Advent of Code 2025</b><br><sup>Total Time Spent: {total_time_str}</sup>",
            font=dict(size=40, color="#f8fafc", family="system-ui, sans-serif"),
            x=0.5,
            xanchor="center",
            yanchor="top",
            y=0.925,
        ),
        font=dict(family="system-ui, sans-serif", color="#e2e8f0", size=18),
        paper_bgcolor="#0b1120",
        plot_bgcolor="#111b2d",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.17,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(15, 23, 42, 0.9)",
            bordercolor="#1f2937",
            borderwidth=1,
            font=dict(size=22),
            itemwidth=90,
        ),
        margin=dict(l=140, r=140, t=220, b=210),
        hoverlabel=dict(
            bgcolor="#1f2937",
            font_size=16,
            font_family="JetBrains Mono, monospace",
            bordercolor="#334155",
        ),
        width=1080,
        height=1350,
        autosize=False,
    )

    # Update axes
    # Calculate sensible x-axis range
    if len(days) == 1:
        x_min, x_max = days[0] - 1, days[0] + 1
    else:
        x_padding = max(0.5, (max(days) - min(days)) * 0.1)
        x_min, x_max = min(days) - x_padding, max(days) + x_padding

    fig.update_xaxes(
        title_text="<b>Day</b>",
        title_font=dict(size=22, color="#94a3b8"),
        tickfont=dict(size=20, color="#cbd5e1"),
        tickmode="array",
        tickvals=days,
        ticktext=[f"{d}" for d in days],
        gridcolor="#1f2937",
        gridwidth=1,
        zeroline=False,
        showline=True,
        linewidth=2,
        linecolor="#475569",
        range=[x_min, x_max],
        ticklen=10,
        tickcolor="#475569",
        ticklabelstandoff=12,
    )

    # Calculate sensible y-axis ranges with nice round numbers
    import math

    def nice_range(values, padding=0.2):
        """Calculate a nice axis range with round tick values."""
        v_min, v_max = min(values), max(values)
        v_range = v_max - v_min if v_max != v_min else v_max * 0.5
        padded_min = v_min - v_range * padding
        padded_max = v_max + v_range * padding
        # Round to nice values
        magnitude = 10 ** math.floor(math.log10(max(abs(padded_max), 1)))
        nice_min = math.floor(padded_min / magnitude) * magnitude
        nice_max = math.ceil(padded_max / magnitude) * magnitude
        if nice_max == nice_min:
            nice_max = nice_min + magnitude
        return max(0, nice_min), nice_max

    time_min, time_max = nice_range(times)
    loc_min, loc_max = nice_range(locs)

    # Primary y-axis (Time)
    fig.update_yaxes(
        title_text="<b>Time (minutes)</b>",
        title_font=dict(size=22, color="#10b981"),
        tickfont=dict(size=20, color="#10b981"),
        gridcolor="#1f2937",
        gridwidth=1,
        zeroline=False,
        showline=True,
        linewidth=2,
        linecolor="#10b981",
        secondary_y=False,
        range=[time_min, time_max],
        ticklen=8,
    )

    # Secondary y-axis (LOC)
    fig.update_yaxes(
        title_text="<b>Lines of Code</b>",
        title_font=dict(size=22, color="#f59e0b"),
        tickfont=dict(size=20, color="#f59e0b"),
        gridcolor="rgba(51, 65, 85, 0.25)",
        gridwidth=1,
        zeroline=False,
        showline=True,
        linewidth=2,
        linecolor="#f59e0b",
        secondary_y=True,
        range=[loc_min, loc_max],
        overlaying="y",
        side="right",
        ticklen=8,
    )

    # Add subtle gradient effect with shapes
    fig.add_shape(
        type="rect",
        xref="paper",
        yref="paper",
        x0=0,
        y0=0,
        x1=1,
        y1=1,
        fillcolor="rgba(15, 23, 42, 0)",
        line=dict(width=0),
        layer="below",
    )

    # Save as PNG - 4:5 aspect ratio plays well on Twitter mobile
    fig.write_image(str(output_path), width=1080, height=1350, scale=2)
    print(f"Graph saved to: {output_path}")


def main():
    base_path = Path(__file__).parent
    output_path = base_path / "progress.png"

    print("Scanning for REMARKS.md files...")
    data = find_remarks_files(base_path)

    if not data:
        print("No REMARKS.md files with valid frontmatter found!")
        return

    print(f"Found {len(data)} day(s) with data:")
    for day, info in data:
        print(f"  Day {day}: {info['time']} min, {info['loc']} LOC")

    print("\nGenerating graph...")
    generate_graph(data, output_path)


if __name__ == "__main__":
    main()
