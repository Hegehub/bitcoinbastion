from enum import StrEnum


class MarketPattern(StrEnum):
    ETF_INFLOW_SHOCK = "ETF_INFLOW_SHOCK"
    ETF_OUTFLOW_SHOCK = "ETF_OUTFLOW_SHOCK"
    SEC_ENFORCEMENT = "SEC_ENFORCEMENT"
    REGULATORY_APPROVAL = "REGULATORY_APPROVAL"
    SEC_APPROVAL = "SEC_APPROVAL"
    REGULATORY_DELAY = "REGULATORY_DELAY"
    ETF_APPROVAL = "ETF_APPROVAL"
    ETF_DELAY = "ETF_DELAY"
    FED_LIQUIDITY_EASING = "FED_LIQUIDITY_EASING"
    FED_TIGHTENING = "FED_TIGHTENING"
    RATE_CUT_SIGNAL = "RATE_CUT_SIGNAL"
    RATE_HIKE_SIGNAL = "RATE_HIKE_SIGNAL"
    FED_LIQUIDITY_SHOCK = "FED_LIQUIDITY_SHOCK"
    INTEREST_RATE_SHOCK = "FED_TIGHTENING"
    INFLATION_SHOCK = "MACRO_RISK_OFF"
    MINER_CAPITULATION = "MINER_CAPITULATION"
    MINING_DIFFICULTY_SHOCK = "MINING_DIFFICULTY_SHOCK"
    HALVING_NARRATIVE = "HALVING_NARRATIVE"
    MINER_ACCUMULATION = "MINER_ACCUMULATION"
    BITCOIN_CORE_RELEASE = "BITCOIN_CORE_RELEASE"
    LIGHTNING_ADOPTION = "LIGHTNING_ADOPTION"
    INSTITUTIONAL_ACCUMULATION = "INSTITUTIONAL_ACCUMULATION"
    TREASURY_ADOPTION = "TREASURY_ADOPTION"
    EXCHANGE_HACK = "EXCHANGE_HACK"
    SECURITY_EXPLOIT = "SECURITY_EXPLOIT"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"
    BANKING_STRESS = "BANKING_STRESS"
    CUSTODY_FAILURE = "CUSTODY_FAILURE"
    PRIVATE_KEY_LEAK = "PRIVATE_KEY_LEAK"
    LARGE_LIQUIDATION = "LARGE_LIQUIDATION_CASCADE"
    LARGE_LIQUIDATION_CASCADE = "LARGE_LIQUIDATION_CASCADE"
    LIQUIDATION_CASCADE = "LIQUIDATION_CASCADE"
    SHORT_SQUEEZE = "VOLATILITY_EXPANSION"
    LONG_SQUEEZE = "VOLATILITY_EXPANSION"
    MARKET_PANIC = "MACRO_RISK_OFF"
    MARKET_RECOVERY = "MACRO_RISK_ON"
    MACRO_RISK_ON = "MACRO_RISK_ON"
    MACRO_RISK_OFF = "MACRO_RISK_OFF"
    VOLATILITY_EXPANSION = "VOLATILITY_EXPANSION"
    UNKNOWN = "UNKNOWN"


def seed_pattern_definitions() -> list[dict[str, object]]:
    return [
        _pattern(
            "ETF_INFLOW_SHOCK",
            "ETF inflow shock",
            "Spot Bitcoin ETF inflow surprise or acceleration.",
            "POSITIVE",
            ["15m", "1h", "4h"],
            "Strong",
        ),
        _pattern(
            "ETF_OUTFLOW_SHOCK",
            "ETF outflow shock",
            "Spot Bitcoin ETF outflow surprise or acceleration.",
            "NEGATIVE",
            ["15m", "1h", "4h"],
            "Strong",
        ),
        _pattern(
            "SEC_ENFORCEMENT",
            "SEC enforcement",
            "SEC enforcement action or legal pressure touching Bitcoin market structure.",
            "NEGATIVE",
            ["1h", "4h", "24h"],
            "Moderate",
        ),
        _pattern(
            "REGULATORY_APPROVAL",
            "Regulatory approval",
            "Approval or constructive regulatory development.",
            "POSITIVE",
            ["1h", "4h", "24h"],
            "Moderate",
        ),
        _pattern(
            "SEC_APPROVAL",
            "SEC approval",
            "SEC approval or constructive regulatory decision.",
            "POSITIVE",
            ["1h", "4h", "24h"],
            "Moderate",
        ),
        _pattern(
            "REGULATORY_DELAY",
            "Regulatory delay",
            "Delayed approval or unresolved regulatory process.",
            "NEGATIVE",
            ["1h", "4h", "24h"],
            "Moderate",
        ),
        _pattern(
            "ETF_APPROVAL",
            "ETF approval",
            "Spot Bitcoin ETF approval or listing authorization.",
            "POSITIVE",
            ["15m", "1h", "4h"],
            "Strong",
            "elevated",
            1.08,
        ),
        _pattern(
            "ETF_DELAY",
            "ETF delay",
            "Spot Bitcoin ETF delay, deferral, or adverse review timeline.",
            "NEGATIVE",
            ["1h", "4h", "24h"],
            "Moderate",
            "elevated",
            0.94,
        ),
        _pattern(
            "FED_LIQUIDITY_SHOCK",
            "Fed liquidity shock",
            "Unexpected liquidity, balance-sheet, or funding-market shock.",
            "NEUTRAL",
            ["1h", "4h", "24h"],
            "Moderate",
            "elevated",
            0.98,
        ),
        _pattern(
            "FED_LIQUIDITY_EASING",
            "Fed liquidity easing",
            "Liquidity easing or dovish macro signal.",
            "POSITIVE",
            ["1h", "4h", "24h"],
            "Moderate",
        ),
        _pattern(
            "FED_TIGHTENING",
            "Fed tightening",
            "Tightening or hawkish macro signal.",
            "NEGATIVE",
            ["1h", "4h", "24h"],
            "Moderate",
        ),
        _pattern(
            "RATE_CUT_SIGNAL",
            "Rate cut signal",
            "Rate-cut or dovish policy signal.",
            "POSITIVE",
            ["1h", "4h", "24h"],
            "Moderate",
        ),
        _pattern(
            "RATE_HIKE_SIGNAL",
            "Rate hike signal",
            "Rate-hike or hawkish policy signal.",
            "NEGATIVE",
            ["1h", "4h", "24h"],
            "Moderate",
        ),
        _pattern(
            "EXCHANGE_HACK",
            "Exchange hack",
            "Exchange compromise or platform-security shock.",
            "NEGATIVE",
            ["15m", "1h", "4h"],
            "Strong",
        ),
        _pattern(
            "CUSTODY_FAILURE",
            "Custody failure",
            "Custodian failure, insolvency, or custody confidence shock.",
            "NEGATIVE",
            ["1h", "4h", "24h"],
            "Strong",
        ),
        _pattern(
            "PRIVATE_KEY_LEAK",
            "Private key leak",
            "Private-key leak, signer compromise, or key-material exposure.",
            "NEGATIVE",
            ["15m", "1h", "4h"],
            "Strong",
            "elevated",
            1.05,
        ),
        _pattern(
            "MINER_CAPITULATION",
            "Miner capitulation",
            "Miner distress, forced selling, or capitulation narrative.",
            "NEGATIVE",
            ["4h", "24h"],
            "Moderate",
        ),
        _pattern(
            "MINING_DIFFICULTY_SHOCK",
            "Mining difficulty shock",
            "Mining difficulty or hash-rate adjustment shock affecting miner economics.",
            "NEUTRAL",
            ["4h", "24h"],
            "Moderate",
            "elevated",
            0.96,
        ),
        _pattern(
            "HALVING_NARRATIVE",
            "Halving narrative",
            "Halving-cycle narrative, supply issuance, or post-halving miner pressure.",
            "POSITIVE",
            ["4h", "24h"],
            "Moderate",
            "normal",
            1.0,
        ),
        _pattern(
            "MINER_ACCUMULATION",
            "Miner accumulation",
            "Miner accumulation or reduced miner selling pressure.",
            "POSITIVE",
            ["4h", "24h"],
            "Moderate",
        ),
        _pattern(
            "LARGE_LIQUIDATION_CASCADE",
            "Large liquidation cascade",
            "High-leverage liquidation cascade or derivatives stress.",
            "NEGATIVE",
            ["15m", "1h"],
            "Strong",
        ),
        _pattern(
            "LIQUIDATION_CASCADE",
            "Liquidation cascade",
            "Forced-liquidation cascade or derivatives stress.",
            "NEGATIVE",
            ["15m", "1h"],
            "Strong",
        ),
        _pattern(
            "BITCOIN_CORE_RELEASE",
            "Bitcoin Core release",
            "Bitcoin Core software release or protocol maintenance event.",
            "NEUTRAL",
            ["4h", "24h"],
            "Weak",
        ),
        _pattern(
            "LIGHTNING_ADOPTION",
            "Lightning adoption",
            "Lightning Network adoption or infrastructure news.",
            "POSITIVE",
            ["4h", "24h"],
            "Moderate",
        ),
        _pattern(
            "TREASURY_ADOPTION",
            "Treasury adoption",
            "Corporate or sovereign Bitcoin treasury adoption.",
            "POSITIVE",
            ["1h", "4h", "24h"],
            "Strong",
        ),
        _pattern(
            "INSTITUTIONAL_ACCUMULATION",
            "Institutional accumulation",
            "Institutional Bitcoin accumulation, custody, or allocation narrative.",
            "POSITIVE",
            ["1h", "4h", "24h"],
            "Strong",
        ),
        _pattern(
            "MACRO_RISK_ON",
            "Macro risk-on",
            "Broad risk-on macro conditions supportive for BTC.",
            "POSITIVE",
            ["1h", "4h", "24h"],
            "Moderate",
        ),
        _pattern(
            "MACRO_RISK_OFF",
            "Macro risk-off",
            "Broad risk-off macro conditions pressuring BTC.",
            "NEGATIVE",
            ["1h", "4h", "24h"],
            "Moderate",
        ),
        _pattern(
            "BANKING_STRESS",
            "Banking stress",
            "Banking-system stress or fiat-liquidity confidence shock.",
            "POSITIVE",
            ["1h", "4h", "24h"],
            "Moderate",
        ),
        _pattern(
            "SECURITY_EXPLOIT",
            "Security exploit",
            "Exploit, protocol issue, or ecosystem-security disclosure.",
            "NEGATIVE",
            ["15m", "1h", "4h"],
            "Strong",
            "elevated",
            1.05,
        ),
        _pattern(
            "SECURITY_INCIDENT",
            "Security incident",
            "Security incident, exploit, malware, or ecosystem risk disclosure.",
            "NEGATIVE",
            ["15m", "1h", "4h"],
            "Strong",
        ),
        _pattern(
            "VOLATILITY_EXPANSION",
            "Volatility expansion",
            "Volatility breakout or market-structure expansion narrative.",
            "NEUTRAL",
            ["15m", "1h", "4h"],
            "Moderate",
        ),
    ]


def infer_pattern_type(title: str, event_type: str = "", category: str = "") -> MarketPattern:
    text = f"{title} {event_type} {category}".lower()
    if "etf" in text and ("inflow" in text or "accumulation" in text):
        return MarketPattern.ETF_INFLOW_SHOCK
    if "etf" in text and "outflow" in text:
        return MarketPattern.ETF_OUTFLOW_SHOCK
    if "sec" in text and ("enforcement" in text or "lawsuit" in text or "charges" in text):
        return MarketPattern.SEC_ENFORCEMENT
    if "etf" in text and ("approval" in text or "approved" in text):
        return MarketPattern.ETF_APPROVAL
    if "etf" in text and ("delay" in text or "delayed" in text or "defer" in text):
        return MarketPattern.ETF_DELAY
    if "delay" in text and ("sec" in text or "regulatory" in text or "approval" in text):
        return MarketPattern.REGULATORY_DELAY
    if "approval" in text or "approved" in text:
        return MarketPattern.REGULATORY_APPROVAL
    if "fed" in text and ("shock" in text or "liquidity" in text):
        return MarketPattern.FED_LIQUIDITY_SHOCK
    if "rate cut" in text or "cut rates" in text:
        return MarketPattern.RATE_CUT_SIGNAL
    if "rate hike" in text or "hike rates" in text:
        return MarketPattern.RATE_HIKE_SIGNAL
    if "easing" in text or "dovish" in text:
        return MarketPattern.FED_LIQUIDITY_EASING
    if (
        "tightening" in text
        or "hawkish" in text
        or "interest" in text
        or "inflation" in text
        or "cpi" in text
    ):
        return MarketPattern.FED_TIGHTENING
    if "miner" in text and "capitulation" in text:
        return MarketPattern.MINER_CAPITULATION
    if "difficulty" in text or "hash rate" in text or "hashrate" in text:
        return MarketPattern.MINING_DIFFICULTY_SHOCK
    if "halving" in text:
        return MarketPattern.HALVING_NARRATIVE
    if "miner" in text and "accumulation" in text:
        return MarketPattern.MINER_ACCUMULATION
    if "bitcoin core" in text or "core release" in text:
        return MarketPattern.BITCOIN_CORE_RELEASE
    if "lightning" in text:
        return MarketPattern.LIGHTNING_ADOPTION
    if "treasury" in text:
        return MarketPattern.TREASURY_ADOPTION
    if "institutional" in text or "blackrock" in text or "fidelity" in text:
        return MarketPattern.INSTITUTIONAL_ACCUMULATION
    if "exchange" in text and "hack" in text:
        return MarketPattern.EXCHANGE_HACK
    if "exploit" in text or "malware" in text:
        return MarketPattern.SECURITY_EXPLOIT
    if "security incident" in text:
        return MarketPattern.SECURITY_INCIDENT
    if "private key" in text or "key leak" in text or "signer compromise" in text:
        return MarketPattern.PRIVATE_KEY_LEAK
    if "custody" in text or "custodian" in text:
        return MarketPattern.CUSTODY_FAILURE
    if "liquidation" in text or "cascade" in text:
        return MarketPattern.LIQUIDATION_CASCADE
    if "banking stress" in text or "bank failure" in text or "bank run" in text:
        return MarketPattern.BANKING_STRESS
    if "risk-on" in text or "recovery" in text:
        return MarketPattern.MACRO_RISK_ON
    if "risk-off" in text or "panic" in text:
        return MarketPattern.MACRO_RISK_OFF
    if "volatility" in text or "short squeeze" in text or "long squeeze" in text:
        return MarketPattern.VOLATILITY_EXPANSION
    return MarketPattern.UNKNOWN


def _pattern(
    pattern_code: str,
    display_name: str,
    description: str,
    expected_sentiment: str,
    expected_time_windows: list[str],
    default_confidence_band: str,
    expected_volatility: str = "normal",
    confidence_modifier: float = 1.0,
) -> dict[str, object]:
    return {
        "pattern_code": pattern_code,
        "display_name": display_name,
        "description": description,
        "expected_sentiment": expected_sentiment,
        "expected_time_windows": expected_time_windows,
        "default_confidence_band": default_confidence_band,
        "default_sentiment": expected_sentiment,
        "expected_reaction_window": (
            expected_time_windows[0] if expected_time_windows else "unknown"
        ),
        "expected_volatility": expected_volatility,
        "confidence_modifier": confidence_modifier,
    }


PatternType = MarketPattern
Pattern = MarketPattern
