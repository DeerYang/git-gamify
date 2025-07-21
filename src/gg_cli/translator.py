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
        self.load_strings(lang_code)

    def load_strings(self, lang_code: str):
        """
        Loads the translation strings from a JSON file for the given language code.

        Falls back to English ("en") if the specified language file is not found
        or if the language code is invalid.
        """
        if not lang_code or not isinstance(lang_code, str):
            lang_code = "en"

        lang_file = LOCALES_DIR / f"{lang_code.lower()}.json"

        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.strings = json.load(f)
        except FileNotFoundError:
            # If a language file is missing, default to English.
            if lang_code != "en":
                console.print(f"[yellow]Warning: Language file for '{lang_code}' not found. Falling back to 'en'.[/yellow]")
                with open(LOCALES_DIR / "en.json", 'r', encoding='utf-8') as f:
                    self.strings = json.load(f)

    def t(self, key: str, **kwargs) -> str:
        """
        Retrieves a translated string by its key and formats it with given arguments.

        Args:
            key: The key of the string to translate.
            **kwargs: Keyword arguments to format into the translated string.

        Returns:
            The formatted, translated string. Returns the key if not found.
        """
        template = self.strings.get(key, key)
        return template.format(**kwargs)