#!/usr/bin/env python3
"""Entrypoint for The Globe Courier (make.fun news-image-20261123).

Builds entry.png with build_courier.py (same directory) and copies it into
$MAKEFUN_OUTPUT_DIR as entry.png. With no MAKEFUN_OUTPUT_DIR set, the copy
goes to the current directory.

Usage: python3 main.py
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    target = HERE / "entry.png"
    subprocess.run(
        [sys.executable, str(HERE / "build_courier.py"), str(target)],
        check=True,
    )
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", ".")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(target, out_dir / "entry.png")
    print(f"wrote {out_dir / 'entry.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
