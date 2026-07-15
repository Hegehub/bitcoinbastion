from __future__ import annotations

import reflex as rx

from bastion_ui.config import get_config
from bastion_ui.i18n.locales import SUPPORTED_LANGUAGES, normalize_language
from bastion_ui.i18n.translations import translate


class LanguageState(rx.State):
    language: str = normalize_language(get_config().default_language)
    supported_languages: tuple[str, ...] = SUPPORTED_LANGUAGES

    def set_language(self, language: str) -> None:
        self.language = normalize_language(language)

    def t(self, key: str) -> str:
        return translate(key, self.language)
