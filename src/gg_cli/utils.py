# src/gg_cli/utils.py
"""Global utilities and path definitions for the Git-Gamify project."""

from pathlib import Path
from rich.console import Console

# Global Rich Console instance for consistent output styling.
console = Console()

# Define key project paths relative to this file's location to ensure they
# work correctly even when packaged.
_CODE_DIR = Path(__file__).parent
DEFINITIONS_DIR = _CODE_DIR / "definitions"
LOCALES_DIR = _CODE_DIR / "locales"

# Define the user data directory in the user's home folder.
DATA_DIR = Path.home() / ".git-gamify"

# Ensure the user data directory exists upon import.
DATA_DIR.mkdir(exist_ok=True)