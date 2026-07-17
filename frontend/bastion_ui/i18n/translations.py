from __future__ import annotations

from bastion_ui.i18n.locales import DEFAULT_LANGUAGE, normalize_language

EN = {
    "nav.platform": "Platform",
    "nav.trace": "Trace",
    "nav.evidence": "Evidence",
    "nav.status": "Status",
    "nav.developers": "Developers",
    "nav.operations": "Operations",
    "nav.docs": "Docs",
    "nav.security": "Security",
    "nav.roadmap": "Roadmap",
    "nav.console": "Console",
    "safety.advisory_only": "Advisory-only.",
    "safety.not_legal_verification": "Not legal verification.",
    "safety.not_consensus_proof": "Not Bitcoin consensus proof.",
    "safety.no_custody": "No custody.",
    "safety.public_addresses_only": "Public Bitcoin addresses only.",
    "safety.never_enter_sensitive_material": (
        "Never enter seed phrases, private keys, wallet files or signing material."
    ),
    "trace.title": "Trace",
    "trace.address_input_label": "Public Bitcoin address",
    "trace.address_input_placeholder": "Enter a public Bitcoin address",
    "trace.submit": "Check address",
    "trace.loading": "Trace request loading.",
    "trace.error_invalid_address": "Enter a public Bitcoin address only.",
    "trace.error_sensitive_material": (
        "This interface accepts public Bitcoin addresses only. Never enter seed phrases, "
        "private keys, wallet files or signing material."
    ),
    "trace.manual_review_recommended": "Manual review recommended.",
    "trace.provider_disagreement": "Provider disagreement.",
    "trace.limited_evidence": "Limited evidence.",
    "evidence.title": "Evidence",
    "evidence.proof_packet": "Proof Packet",
    "evidence.chain": "Evidence chain",
    "evidence.limitations": "Evidence limitations",
    "console.title": "Bastion Console",
    "console.trace": "Trace",
    "console.evidence": "Evidence",
    "console.provider_health": "Provider Health",
    "console.market_intelligence": "Market Intelligence",
    "console.time_machine": "Time Machine",
    "console.policy": "Policy",
    "console.audit": "Audit",
    "degraded.provider_unavailable": "Provider unavailable.",
    "degraded.stale_data": "Stale data visible.",
    "degraded.fallback_mode": "Fallback mode active.",
    "degraded.partial_result": "Partial result shown.",
    "error.backend_unavailable": (
        "The backend is temporarily unavailable. No custody action was performed."
    ),
    "error.timeout": "The request timed out. No custody action was performed.",
    "error.not_found": "The requested report was not found or is no longer available.",
    "error.rate_limited": "Too many requests. Wait and retry.",
    "error.unexpected": "Unexpected error. No custody action was performed.",
}

RU = {
    "nav.platform": "Платформа",
    "nav.trace": "Трассировка",
    "nav.evidence": "Доказательства",
    "nav.status": "Статус",
    "nav.developers": "Разработчикам",
    "nav.operations": "Операции",
    "nav.docs": "Документы",
    "nav.security": "Безопасность",
    "nav.roadmap": "План",
    "nav.console": "Консоль",
    "safety.advisory_only": "Только справочная информация.",
    "safety.not_legal_verification": "Не является юридической проверкой.",
    "safety.not_consensus_proof": "Не является доказательством консенсуса Bitcoin.",
    "safety.no_custody": "Без хранения средств.",
    "safety.public_addresses_only": "Только публичные Bitcoin-адреса.",
    "safety.never_enter_sensitive_material": (
        "Никогда не вводите seed-фразы, приватные ключи, файлы кошельков или материалы для подписи."
    ),
    "trace.title": "Трассировка",
    "trace.address_input_label": "Публичный Bitcoin-адрес",
    "trace.address_input_placeholder": "Введите публичный Bitcoin-адрес",
    "trace.submit": "Проверить адрес",
    "trace.loading": "Запрос трассировки выполняется.",
    "trace.error_invalid_address": "Введите только публичный Bitcoin-адрес.",
    "trace.error_sensitive_material": (
        "Этот интерфейс принимает только публичные Bitcoin-адреса. Никогда не вводите "
        "seed-фразы, приватные ключи, файлы кошельков или материалы для подписи."
    ),
    "trace.manual_review_recommended": "Рекомендуется ручная проверка.",
    "trace.provider_disagreement": "Расхождение между провайдерами.",
    "trace.limited_evidence": "Ограниченные доказательства.",
    "evidence.title": "Доказательства",
    "evidence.proof_packet": "Пакет доказательств",
    "evidence.chain": "Цепочка доказательств",
    "evidence.limitations": "Ограничения доказательств",
    "console.title": "Консоль Bastion",
    "console.trace": "Трассировка",
    "console.evidence": "Доказательства",
    "console.provider_health": "Состояние провайдеров",
    "console.market_intelligence": "Рыночная аналитика",
    "console.time_machine": "Time Machine",
    "console.policy": "Политики",
    "console.audit": "Аудит",
    "degraded.provider_unavailable": "Провайдер недоступен.",
    "degraded.stale_data": "Показаны устаревшие данные.",
    "degraded.fallback_mode": "Активен резервный режим.",
    "degraded.partial_result": "Показан частичный результат.",
    "error.backend_unavailable": (
        "Бэкенд временно недоступен. Действий с хранением средств не выполнялось."
    ),
    "error.timeout": "Время запроса истекло. Действий с хранением средств не выполнялось.",
    "error.not_found": "Запрошенный отчет не найден или больше недоступен.",
    "error.rate_limited": "Слишком много запросов. Подождите и повторите.",
    "error.unexpected": "Неожиданная ошибка. Действий с хранением средств не выполнялось.",
}

TRANSLATIONS = {"en": EN, "ru": RU}


def translate(key: str, language: str | None = None) -> str:
    normalized = normalize_language(language)
    return TRANSLATIONS.get(normalized, EN).get(key, EN.get(key, key))


def default_language() -> str:
    return DEFAULT_LANGUAGE
