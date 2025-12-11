#!/usr/bin/env python3
"""Generate a beautiful dashboard from REMARKS.md files showing dev metrics per day."""

import re
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def parse_remarks_file(filepath: Path) -> dict | None:
    """Parse a REMARKS.md file and extract metrics from frontmatter."""
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

            if not value:
                continue

            try:
                if key == "dev_time":
                    # Handle "45m" or just "45"
                    clean_val = value.lower().replace("m", "").strip()
                    if clean_val:
                        data["dev_time"] = int(clean_val)
                elif key == "loc":
                    data["loc"] = int(value)
                elif key == "runtime":
                    data["runtime"] = float(value)
                elif key == "cpu":
                    # Handle "99%" -> 99
                    data["cpu"] = int(value.replace("%", ""))
                elif key == "peak_memory":
                    data["peak_memory"] = int(value)
            except ValueError:
                continue

    required_keys = {"dev_time", "loc", "runtime", "cpu", "peak_memory"}
    if not required_keys.issubset(data.keys()):
        # Try to support legacy format if just time/loc are present?
        # The user requested specific new format support, but let's be safe.
        if "dev_time" in data and "loc" in data:
            # Backfill others with 0 if missing, to allow plotting what we have
            for k in required_keys:
                if k not in data:
                    data[k] = 0
            return data
        return None

    return data


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
    """Generate a beautiful 3-row dashboard image using Plotly."""
    if not data:
        print("No data found to plot!")
        return

    days = [d[0] for d in data]
    # Calculate total time in minutes first
    raw_dev_times = [d[1]["dev_time"] for d in data]
    total_minutes = sum(raw_dev_times)

    dev_times = [t / 60 for t in raw_dev_times]  # Convert to hours for plotting
    locs = [d[1]["loc"] for d in data]
    runtimes = [d[1]["runtime"] for d in data]
    cpus = [d[1]["cpu"] for d in data]
    # Convert KB to MB for cleaner graph
    mems = [d[1]["peak_memory"] / 1024 for d in data]

    # Format total time
    if total_minutes >= 60:
        hours, mins = divmod(total_minutes, 60)
        total_time_str = f"{int(hours)}h {int(mins)}m" if mins else f"{int(hours)}h"
    else:
        total_time_str = f"{total_minutes}m"

    # Create subplot with 3 rows
    # Row 1: Dev Time & LOC (Double Axis)
    # Row 2: Runtime (Single Axis)
    # Row 3: Memory & CPU (Double Axis)
    fig = make_subplots(
        rows=3,
        cols=2,
        shared_xaxes=True,
        vertical_spacing=0.08,
        horizontal_spacing=0.03,
        specs=[
            [{"colspan": 2, "secondary_y": True}, None],
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"colspan": 2, "secondary_y": True}, None],
        ],
        subplot_titles=(
            "<b>Time Spent Solving & Lines of Code</b>",
            " ",
            " ",
            "<b>Memory & CPU Usage</b>",
        ),
    )

    fig.add_annotation(
        text="<b>Runtime Duration (MacBook Air M2)</b>",
        x=0.5,
        y=0.64,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 18, "color": "#e2e8f0"},
        xanchor="center",
        yanchor="bottom",
    )

    # --- ROW 1: Development Effort ---

    # Trace 1: Dev Time (Green) - Primary Y
    fig.add_trace(
        go.Scatter(
            x=days,
            y=dev_times,
            name="Dev Time",
            mode="lines+markers",
            line={"color": "#34d399", "width": 3, "shape": "spline"},
            marker={"size": 10, "color": "#111b2d", "line": {"color": "#34d399", "width": 2}},
            fill="tozeroy",
            fillcolor="rgba(52, 211, 153, 0.1)",
            hovertemplate="Dev Time: %{y:.1f} hrs",
        ),
        row=1,
        col=1,
        secondary_y=False,
    )

    # Trace 2: LOC (Amber) - Secondary Y
    fig.add_trace(
        go.Scatter(
            x=days,
            y=locs,
            name="Lines of Code",
            mode="lines+markers",
            line={"color": "#fbbf24", "width": 3, "shape": "spline", "dash": "dot"},
            marker={
                "size": 10,
                "symbol": "diamond",
                "color": "#111b2d",
                "line": {"color": "#fbbf24", "width": 2},
            },
            hovertemplate="LoC: %{y}",
        ),
        row=1,
        col=1,
        secondary_y=True,
    )

    # --- ROW 2: Execution Speed ---

    # Trace 3: Runtime (Cyan) - Linear
    fig.add_trace(
        go.Scatter(
            x=days,
            y=runtimes,
            name="Runtime (Linear)",
            mode="lines+markers",
            line={"color": "#22d3ee", "width": 3, "shape": "spline"},
            marker={"size": 10, "color": "#111b2d", "line": {"color": "#22d3ee", "width": 2}},
            fill="tozeroy",
            fillcolor="rgba(34, 211, 238, 0.1)",
            hovertemplate="Runtime: %{y:.3f}s",
            showlegend=True,
        ),
        row=2,
        col=1,
    )

    # Trace 3b: Runtime (Cyan) - Log
    fig.add_trace(
        go.Scatter(
            x=days,
            y=runtimes,
            name="Runtime (Log)",
            mode="lines+markers",
            line={"color": "#22d3ee", "width": 3, "shape": "spline"},
            marker={"size": 10, "color": "#111b2d", "line": {"color": "#22d3ee", "width": 2}},
            fill="tozeroy",
            fillcolor="rgba(34, 211, 238, 0.1)",
            hovertemplate="Runtime: %{y:.3f}s",
            showlegend=False,
        ),
        row=2,
        col=2,
    )

    # --- ROW 3: System Efficiency ---

    # Trace 4: Memory (Purple) - Primary Y
    fig.add_trace(
        go.Scatter(
            x=days,
            y=mems,
            name="Memory (MB)",
            mode="lines+markers",
            line={"color": "#c084fc", "width": 3, "shape": "spline"},
            marker={"size": 10, "color": "#111b2d", "line": {"color": "#c084fc", "width": 2}},
            fill="tozeroy",
            fillcolor="rgba(192, 132, 252, 0.1)",
            hovertemplate="Mem: %{y:.1f} MB",
        ),
        row=3,
        col=1,
        secondary_y=False,
    )

    # Trace 5: CPU (Red/Rose) - Secondary Y
    fig.add_trace(
        go.Scatter(
            x=days,
            y=cpus,
            name="CPU Usage",
            mode="lines+markers",
            line={"color": "#f43f5e", "width": 3, "shape": "spline", "dash": "dot"},
            marker={
                "size": 10,
                "symbol": "square",
                "color": "#111b2d",
                "line": {"color": "#f43f5e", "width": 2},
            },
            hovertemplate="CPU: %{y}%",
        ),
        row=3,
        col=1,
        secondary_y=True,
    )

    # --- Styling & Layout ---

    fig.update_layout(
        title={
            "text": f"<b>Advent of Code 2025</b><br><span style='font-size: 20px; color: #94a3b8;'>Total Time Spent Solving: {total_time_str}</span>",
            "font": {"size": 36, "color": "#f8fafc", "family": "system-ui, sans-serif"},
            "y": 0.97,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        annotations=[],
        font={"family": "system-ui, sans-serif", "color": "#e2e8f0", "size": 14},
        paper_bgcolor="#0b1120",
        plot_bgcolor="#111b2d",
        hovermode="x unified",
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.06,
            "xanchor": "center",
            "x": 0.5,
            "bgcolor": "rgba(15, 23, 42, 0.8)",
            "bordercolor": "#334155",
            "borderwidth": 1,
            "font": {"size": 14},
        },
        margin={"l": 100, "r": 40, "t": 140, "b": 120},
        width=1080,
        height=1620,
    )

    # Update Axes Style
    # Common X-Axis settings
    fig.update_xaxes(
        gridcolor="#1e293b",
        zeroline=False,
        showline=False,
        tickfont={"size": 14, "color": "#94a3b8"},
        tickmode="linear",
        tick0=1,
        dtick=1,
    )

    # Row 1 Axes
    fig.update_yaxes(
        title_text="Time Spent Solving (Hours)",
        title_font={"color": "#34d399"},
        tickfont={"color": "#34d399"},
        gridcolor="#1e293b",
        rangemode="tozero",
        row=1,
        col=1,
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="LoC",
        title_font={"color": "#fbbf24"},
        tickfont={"color": "#fbbf24"},
        showgrid=False,
        rangemode="tozero",
        row=1,
        col=1,
        secondary_y=True,
    )

    # Row 2 Axes
    fig.update_yaxes(
        title_text="Seconds",
        title_font={"color": "#22d3ee"},
        tickfont={"color": "#22d3ee"},
        gridcolor="#1e293b",
        rangemode="tozero",
        row=2,
        col=1,
    )
    fig.update_yaxes(
        title_text="Seconds (Log)",
        title_font={"color": "#22d3ee"},
        tickfont={"color": "#22d3ee"},
        gridcolor="#1e293b",
        type="log",
        side="right",
        row=2,
        col=2,
    )

    # Row 3 Axes
    fig.update_yaxes(
        title_text="Peak Memory (MB)",
        title_font={"color": "#c084fc"},
        tickfont={"color": "#c084fc"},
        gridcolor="#1e293b",
        rangemode="tozero",
        row=3,
        col=1,
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="CPU Utilization",
        title_font={"color": "#f43f5e"},
        tickfont={"color": "#f43f5e"},
        showgrid=False,
        rangemode="tozero",
        row=3,
        col=1,
        secondary_y=True,
    )

    # Customizing Subplot Titles
    fig.update_annotations(font={"size": 18, "color": "#e2e8f0"})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(str(output_path), width=1080, height=1620, scale=2)
    print(f"Graph saved to: {output_path}")


def main():
    base_path = Path(__file__).parent
    output_path = base_path / "progress.png"

    print("Scanning for REMARKS.md files...")
    data = find_remarks_files(base_path)

    if not data:
        print("No REMARKS.md files with valid data found!")
        return

    print(f"Found {len(data)} day(s) with data.")
    print("\nGenerating dashboard...")
    generate_graph(data, output_path)


if __name__ == "__main__":
    main()
