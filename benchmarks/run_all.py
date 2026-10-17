"""Entry point: ``python -m benchmarks.run_all``.

Thin wrapper around :mod:`algopt.bench` so the numbers in the README are one
command away from anyone who clones the repo.
"""

from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from algopt.bench import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
