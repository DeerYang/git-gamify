import json
from gg_cli.utils import LOCALES_DIR


class Translator:
    def __init__(self, lang_code="en"):
        """
        现在，我们在创建它的时候，就必须告诉它使用哪种语言。
        """
        self.strings = {}
        self.load_strings(lang_code)

    def load_strings(self, lang_code):
        """根据传入的语言代码加载对应的翻译文件。"""
        # 如果传入的语言代码无效，则安全地回退到英语
        if not lang_code or not isinstance(lang_code, str):
            lang_code = "en"

        lang_file = LOCALES_DIR / f"{lang_code.lower()}.json"

        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.strings = json.load(f)
        except FileNotFoundError:
            # 如果指定的语言文件不存在，也回退到英语
            if lang_code != "en":
                print(f"Warning: Language file for '{lang_code}' not found. Falling back to 'en'.")
                with open(LOCALES_DIR / "en.json", 'r', encoding='utf-8') as f:
                    self.strings = json.load(f)

    def t(self, key, **kwargs):
        """获取翻译后的字符串，并格式化占位符。"""
        template = self.strings.get(key, key)
        return template.format(**kwargs)