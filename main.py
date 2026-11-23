"""The Globe Courier — news-image-20261123 entry shipper.

Python 3.13, standard library only. Copies the composed entry.png
beside this file to the grader's output directory. Deterministic:
the same repository always writes the same bytes.
"""

import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent

out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
out_dir.mkdir(parents=True, exist_ok=True)
shutil.copyfile(HERE / "entry.png", out_dir / "entry.png")
