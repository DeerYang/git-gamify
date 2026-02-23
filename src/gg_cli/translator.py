"""Internationalization helper for loading and formatting locale strings."""

from __future__ import annotations

import json

from gg_cli.utils import LOCALES_DIR, console


class Translator:
    """Load locale files and expose a small translation lookup API."""

    def __init__(self, lang_code: str = "en") -> None:
        self.strings: dict[str, str] = {}

        # Always seed translations with English to guarantee fallback keys.
        self._load_language("en")
        if lang_code.lower() != "en":
            self.load_strings(lang_code)

    def _load_language(self, lang_code: str) -> bool:
        """Load one locale file into the translation map."""
        lang_file = LOCALES_DIR / f"{lang_code.lower()}.json"
        try:
            with open(lang_file, "r", encoding="utf-8-sig") as f:
                self.strings.update(json.load(f))
            return True
        except FileNotFoundError:
            console.print(f"[yellow]Warning: Language file for '{lang_code}' not found.[/yellow]")
        except json.JSONDecodeError:
            console.print(
                f"[bold red]Error: Failed to decode language file for '{lang_code}'. The file might be corrupted.[/bold red]"
            )
        except Exception as exc:
            console.print(
                f"[bold red]An unexpected error occurred while loading language '{lang_code}': {exc}[/bold red]"
            )
        return False

    def load_strings(self, lang_code: str) -> None:
        """Load non-English strings while preserving English fallback entries."""
        if not self._load_language(lang_code):
            console.print("[yellow]Falling back to English.[/yellow]")

    def t(self, key: str, **kwargs) -> str:
        """Return translated text for `key`, formatted with `kwargs` if provided."""
        template = self.strings.get(key, key)
        return template.format(**kwargs)
