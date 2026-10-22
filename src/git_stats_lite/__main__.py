"""Entry point for python -m git_stats_lite."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
