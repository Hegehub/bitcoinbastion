from __future__ import annotations

from bastion_ui.i18n.keys import TRANSLATION_KEYS
from bastion_ui.i18n.locales import SUPPORTED_LANGUAGES, normalize_language
from bastion_ui.i18n.translations import TRANSLATIONS, translate
from bastion_ui.state.language_state import LanguageState


def test_english_and_russian_translations_exist() -> None:
    assert "en" in SUPPORTED_LANGUAGES
    assert "ru" in SUPPORTED_LANGUAGES
    for language in ("en", "ru"):
        for key in TRANSLATION_KEYS:
            assert key in TRANSLATIONS[language]


def test_missing_key_falls_back_safely() -> None:
    assert translate("missing.key", "ru") == "missing.key"
    assert normalize_language("de") == "en"


def test_safety_keys_exist_in_both_languages() -> None:
    for language in ("en", "ru"):
        assert translate("safety.no_custody", language)
        assert translate("safety.never_enter_sensitive_material", language)


def test_language_state_can_switch_language() -> None:
    state = LanguageState()
    state.set_language("ru")
    assert state.language == "ru"
    assert state.t("nav.console") == "Консоль"
    state.set_language("unsupported")
    assert state.language == "en"
