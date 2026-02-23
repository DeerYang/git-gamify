"""Shared project utilities and filesystem paths."""

from pathlib import Path

from rich.console import Console

# Shared Rich console used by CLI and runtime messages.
console = Console()

# Package-relative paths for static assets bundled with the project.
_CODE_DIR = Path(__file__).parent
DEFINITIONS_DIR = _CODE_DIR / "definitions"
LOCALES_DIR = _CODE_DIR / "locales"

# Persistent user data directory under the current OS user home.
DATA_DIR = Path.home() / ".git-gamify"
DATA_DIR.mkdir(exist_ok=True)
