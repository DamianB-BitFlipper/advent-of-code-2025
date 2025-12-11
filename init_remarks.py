#!/usr/bin/env python3
"""Initialize REMARKS.md for a given day with metrics from cloc and gtime."""

import json
import subprocess
import sys
from pathlib import Path

import fire


def parse_existing_remarks(remarks_path: Path) -> tuple[str, str]:
    """Parse existing REMARKS.md and extract dev_time and body content.

    Args:
        remarks_path: Path to the REMARKS.md file

    Returns:
        Tuple of (dev_time, body) from the existing file, or ("", "") if not found
    """
    if not remarks_path.exists():
        return "", ""

    content = remarks_path.read_text()
    if not content.startswith("---"):
        return "", content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return "", content

    front_matter = parts[1]
    body = parts[2]

    dev_time = ""
    for line in front_matter.strip().split("\n"):
        if line.startswith("dev_time:"):
            dev_time = line.split(":", 1)[1].strip()
            break

    return dev_time, body


def find_python_file(day_dir: Path) -> Path:
    """Find the single Python file in the day directory.

    Args:
        day_dir: Path to the day directory

    Returns:
        Path to the Python file

    Raises:
        SystemExit: If no Python file or multiple Python files found
    """
    python_files = list(day_dir.glob("*.py"))
    if len(python_files) == 0:
        print(f"Error: No Python file found in {day_dir}", file=sys.stderr)
        sys.exit(1)
    if len(python_files) > 1:
        print(f"Error: Multiple Python files found in {day_dir}: {python_files}", file=sys.stderr)
        sys.exit(1)
    return python_files[0]


def get_loc(day_dir: Path) -> str:
    """Get lines of code using cloc.

    Args:
        day_dir: Path to the day directory

    Returns:
        LOC count as string, or empty string on error
    """
    cloc_cmd = ["cloc", str(day_dir), "--exclude-lang=Text,Markdown", "--json"]
    print(f"Running: {' '.join(cloc_cmd)}")
    try:
        cloc_result = subprocess.run(
            cloc_cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        cloc_data = json.loads(cloc_result.stdout)
        return cloc_data.get("Python", {}).get("code", "")
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not get LOC from cloc: {e}", file=sys.stderr)
        return ""


def get_runtime_metrics(day_dir: Path, python_file: Path) -> dict[str, str]:
    """Get runtime metrics using gtime.

    Args:
        day_dir: Path to the day directory (used as cwd)
        python_file: Path to the Python file to run

    Returns:
        Dict with runtime, cpu, and peak_memory keys (empty strings on error)
    """
    gtime_cmd = [
        "gtime",
        "-f",
        '{"runtime_sec": %e, "cpu_percent": "%P", "max_rss_kb": %M}',
        "python",
        python_file.name,
    ]
    print(f"Running (in {day_dir}): {' '.join(gtime_cmd)}")
    try:
        gtime_result = subprocess.run(
            gtime_cmd,
            capture_output=True,
            text=True,
            cwd=day_dir,
        )
        # gtime outputs to stderr (last line), extract it from any other stderr output
        gtime_output = gtime_result.stderr.strip().split("\n")[-1]
        metrics = json.loads(gtime_output)
        return {
            "runtime": metrics.get("runtime_sec", ""),
            "cpu": metrics.get("cpu_percent", ""),
            "peak_memory": metrics.get("max_rss_kb", ""),
        }
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not get metrics from gtime: {e}", file=sys.stderr)
        return {"runtime": "", "cpu": "", "peak_memory": ""}


def init_remarks(day: int) -> None:
    """Initialize REMARKS.md for the given day number.

    Args:
        day: The day number (e.g., 1 for day1/)
    """
    day_dir = Path(f"day{day}")

    if not day_dir.exists():
        print(f"Error: Directory {day_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    remarks_path = day_dir / "REMARKS.md"

    # Parse existing REMARKS.md if present
    existing_dev_time, existing_body = parse_existing_remarks(remarks_path)

    # Find the Python file
    python_file = find_python_file(day_dir)

    # Gather metrics
    loc = get_loc(day_dir)
    metrics = get_runtime_metrics(day_dir, python_file)

    # Create REMARKS.md content
    content = f"""---
dev_time: {existing_dev_time}
loc: {loc}
runtime: {metrics["runtime"]}
cpu: {metrics["cpu"]}
peak_memory: {metrics["peak_memory"]}
---
{existing_body.lstrip()}"""

    remarks_path.write_text(content)
    action = "Updated" if existing_body or existing_dev_time else "Created"
    print(f"{action} {remarks_path}")


if __name__ == "__main__":
    fire.Fire(init_remarks)
