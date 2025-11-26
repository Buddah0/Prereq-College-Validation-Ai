#!/usr/bin/env python3
"""
scripts/ingest.py
Minimal ingestion CLI stub referenced in docs/development.md
Usage:
  python scripts/ingest.py --source samples/sample-catalog.html
"""
import argparse
import json
from pathlib import Path

def ingest(source: str, out: str = "snapshots/latest.json"):
    # Minimal stub: copy source path info into a snapshot JSON
    snapshot = {"source": source, "status": "stub", "courses": []}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
    print(f"Snapshot written to {out}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, help="Path or URL to catalog")
    p.add_argument("--out", default="snapshots/latest.json", help="Output snapshot path")
    args = p.parse_args()
    ingest(args.source, args.out)

if __name__ == "__main__":
    main()
