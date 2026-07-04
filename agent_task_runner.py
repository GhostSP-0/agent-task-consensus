#!/usr/bin/env python3
"""
agent_task_runner.py — Runner untuk agent_task yang jalan di background.

Usage:
    python3 agent_task_runner.py "<task>" [--model1 ...] [--model2 ...] [--model3 ...] [--output ...]

Output disimpan ke file (default: /tmp/agent_task_output_<timestamp>.md)
Script ini mencatat progress ke stderr dan hasil akhir ke stdout + file.
"""

import sys
import os
import time
import json
import argparse
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_task.core import agent_task


def main():
    parser = argparse.ArgumentParser(description="Agent Task Runner (background mode)")
    parser.add_argument("task", type=str, help="Task/prompt untuk para agen")
    parser.add_argument("--model1", type=str, default=None, help="Model Agent 1 (default: gemini-3-flash)")
    parser.add_argument("--model2", type=str, default=None, help="Model Agent 2 (default: claude-opus)")
    parser.add_argument("--model3", type=str, default=None, help="Model Agent 3 (default: claude-sonnet)")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    args = parser.parse_args()

    # Generate output file path
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = args.output or f"/tmp/agent_task_output_{ts}.md"

    # Log start to stderr
    print(f"[{datetime.now().isoformat()}] START agent_task", file=sys.stderr)
    print(f"[Task] {args.task[:100]}...", file=sys.stderr)
    m1 = args.model1 or "ag/gemini-3-flash-agent"
    m2 = args.model2 or "ag/claude-opus-4-6-thinking"
    m3 = args.model3 or "ag/claude-sonnet-4-6"
    print(f"[Models] {m1} | {m2} | {m3}", file=sys.stderr)
    print(f"[Output] {output_file}", file=sys.stderr)

    t0 = time.time()

    try:
        # Run the consensus pipeline
        result = agent_task(
            task=args.task,
            model1=args.model1,
            model2=args.model2,
            model3=args.model3,
            output_file=output_file,
        )

        elapsed = time.time() - t0
        print(f"[{datetime.now().isoformat()}] DONE in {elapsed:.1f}s", file=sys.stderr)

        # Print result to stdout (for notify_on_complete)
        print(result)

        # Also save metadata
        meta_file = output_file.replace(".md", "_meta.json")
        with open(meta_file, "w") as f:
            json.dump({
                "task": args.task,
                "model1": m1,
                "model2": m2,
                "model3": m3,
                "elapsed_seconds": elapsed,
                "output_file": output_file,
                "timestamp": datetime.now().isoformat(),
            }, f, indent=2)

    except Exception as e:
        elapsed = time.time() - t0
        error_msg = f"ERROR after {elapsed:.1f}s: {e}"
        print(f"[{datetime.now().isoformat()}] {error_msg}", file=sys.stderr)
        print(error_msg)
        sys.exit(1)


if __name__ == "__main__":
    main()
