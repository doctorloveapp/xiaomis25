"""Application preferences, separate from watchface documents and bundled data."""
import json
from pathlib import Path
from .paths import user_data_root

LANGUAGES = ('it', 'en', 'zh')


def language_code(value):
    code = str(value or 'it').replace('_', '-').split('-')[0].lower()
    return code if code in LANGUAGES else 'it'


class AppSettings:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else user_data_root() / 'settings.json'
        self.values = self.read()

    def read(self):
        try:
            value = json.loads(self.path.read_text(encoding='utf-8-sig'))
            return value if isinstance(value, dict) else {}
        except (OSError, ValueError):
            return {}

    @property
    def language(self):
        return language_code(self.values.get('language'))

    def compiler(self,default):
        value=self.values.get('compiler')
        return Path(value) if isinstance(value,str) and value.strip() else default

    def update(self, **changes):
        # Re-read to preserve preferences written by another application window.
        values = {**self.read(), **changes}
        if 'language' in changes:
            if changes['language'] not in LANGUAGES:
                raise ValueError('Lingua non supportata.')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + '.tmp')
        temporary.write_text(json.dumps(values, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        temporary.replace(self.path)
        self.values = values
