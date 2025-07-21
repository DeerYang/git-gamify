# src/gg_cli/translator.py
"""Provides internationalization (i18n) support through a Translator class."""

import json
from gg_cli.utils import LOCALES_DIR, console


class Translator:
    """Manages loading and retrieving translated strings from JSON locale files."""

    def __init__(self, lang_code: str = "en"):
        """
        Initializes the Translator for a specific language.

        Args:
            lang_code: The language code (e.g., "en", "zh") to use for translations.
        """
        self.strings = {}
        # Always load English first as a reliable fallback.
        self._load_language("en")
        # If the requested language is not English, try to load it.
        # It will override the English strings if successful.
        if lang_code.lower() != "en":
            self.load_strings(lang_code)

    def _load_language(self, lang_code: str) -> bool:
        """
        Internal helper to load a single language file with robust error handling.
        Returns True on success, False on failure.
        """
        lang_file = LOCALES_DIR / f"{lang_code.lower()}.json"
        try:
            with open(lang_file, 'r', encoding='utf-8-sig') as f:
                self.strings.update(json.load(f))
            return True
        except FileNotFoundError:
            console.print(f"[yellow]Warning: Language file for '{lang_code}' not found.[/yellow]")
        except json.JSONDecodeError:
            console.print(
                f"[bold red]Error: Failed to decode language file for '{lang_code}'. The file might be corrupted.[/bold red]")
        except Exception as e:
            console.print(
                f"[bold red]An unexpected error occurred while loading language '{lang_code}': {e}[/bold red]")

        return False

    def load_strings(self, lang_code: str):
        """
        Loads the translation strings for the given language, with English as a fallback.
        """
        if not self._load_language(lang_code):
            console.print("[yellow]Falling back to English.[/yellow]")
            # No need to load English again, it's already there as the base.
            pass

    def t(self, key: str, **kwargs) -> str:
        """
        Retrieves a translated string by its key and formats it with given arguments.
        """
        template = self.strings.get(key, key)
        return template.format(**kwargs)