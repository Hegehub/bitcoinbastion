from __future__ import annotations

from bastion_ui.i18n.keys import TRANSLATION_KEYS
from bastion_ui.i18n.locales import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, normalize_language
from bastion_ui.i18n.translations import TRANSLATIONS, translate

__all__ = [
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "TRANSLATIONS",
    "TRANSLATION_KEYS",
    "normalize_language",
    "translate",
]
