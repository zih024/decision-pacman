#!/usr/bin/env python3
"""Append headless run summaries to repro/results/runs.csv.

Usage:
  python3 repro/scripts/collect.py RUN_DIR [RUN_DIR ...] [--max-seconds 300] [--load 1.8] [--notes "..."]

RUN_DIR is a directory with summary.json (written by `npm run headless`),
or a parent directory whose subdirectories contain one (e.g. runs/det_greedy_a).
Runs already in the CSV are skipped. Run this right after the runs, so the
recorded commit matches the code that produced them.
"""
import argparse
import csv
import json
import re
import subprocess
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[1] / "results" / "runs.csv"
FIELDS = [
    "run_id", "date", "commit", "machine", "ollama_ver", "policy", "clock",
    "seed_start", "games", "max_seconds", "mean_pellets", "per_game_pellets",
    "p50_ms", "stale_rate", "load_avg", "notes",
]


def sh(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def find_summaries(path):
    path = Path(path)
    if (path / "summary.json").exists():
        return [path / "summary.json"]
    return sorted(path.glob("*/summary.json"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--max-seconds", default="300")
    ap.add_argument("--load", default="", help="load average during the run (from uptime)")
    ap.add_argument("--notes", default="")
    args = ap.parse_args()

    existing = set()
    if CSV_PATH.exists():
        with CSV_PATH.open() as f:
            existing = {row["run_id"] for row in csv.DictReader(f)}

    commit = sh(["git", "rev-parse", "--short", "HEAD"])
    machine = sh(["sysctl", "-n", "hw.model"])
    m = re.search(r"\d+\.\d+\.\d+", sh(["ollama", "--version"]))
    ollama_ver = m.group(0) if m else ""

    added = 0
    with CSV_PATH.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        for run in args.runs:
            for summary_path in find_summaries(run):
                run_id = summary_path.parent.name
                if run_id in existing:
                    print(f"skip (already in CSV): {run_id}")
                    continue
                data = json.loads(summary_path.read_text())
                o = data["overall"]
                date = re.match(r"(\d{4}-\d{2}-\d{2})", run_id)
                writer.writerow({
                    "run_id": run_id,
                    "date": date.group(1) if date else "",
                    "commit": commit,
                    "machine": machine,
                    "ollama_ver": ollama_ver,
                    "policy": o["policy"],
                    "clock": o["clock"],
                    "seed_start": o["seed0"],
                    "games": o["games"],
                    "max_seconds": args.max_seconds,
                    "mean_pellets": o["meanPellets"],
                    "per_game_pellets": ";".join(str(g["pellets"]) for g in data["games"]),
                    "p50_ms": o["meanLatencyP50"],
                    "stale_rate": o["staleRate"],
                    "load_avg": args.load,
                    "notes": args.notes,
                })
                existing.add(run_id)
                added += 1
                print(f"added: {run_id}  {o['policy']} {o['clock']} mean_pellets={o['meanPellets']}")
    print(f"{added} row(s) added to {CSV_PATH}")


if __name__ == "__main__":
    main()
