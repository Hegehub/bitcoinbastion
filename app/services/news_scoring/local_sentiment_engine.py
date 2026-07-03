from dataclasses import dataclass


@dataclass
class SentimentResult:
    label: str
    sentiment_score: float
    factors: list[str]


class LocalSentimentEngine:
    positive_keywords = {
        "approval",
        "inflow",
        "adoption",
        "accumulation",
        "partnership",
        "launch",
        "buying",
        "expansion",
    }
    negative_keywords = {
        "ban",
        "lawsuit",
        "hack",
        "exploit",
        "outflow",
        "liquidation",
        "rejection",
        "crackdown",
        "failure",
    }
    institutional_keywords = {
        "etf",
        "blackrock",
        "fidelity",
        "treasury",
        "fund",
        "institutional",
        "issuer",
    }
    macro_keywords = {"fed", "rates", "cpi", "inflation", "dollar", "liquidity", "bond yields"}
    security_keywords = {"exploit", "malware", "private key leak", "hack", "breach", "attack"}
    regulatory_keywords = {
        "sec",
        "cftc",
        "treasury",
        "compliance",
        "regulation",
        "approval",
        "enforcement",
    }
    sovereignty_keywords = {
        "self-custody",
        "bitcoin core",
        "lightning",
        "privacy",
        "sovereign",
        "open-source",
        "node",
    }
    urgency_keywords = {"breaking", "urgent", "immediate", "alert", "emergency"}

    def _count(self, text: str, keywords: set[str]) -> int:
        t = text.lower()
        return sum(1 for k in keywords if k in t)

    def score(self, title: str, summary: str = "", content: str = "") -> SentimentResult:
        text = " ".join([title, summary, content])
        pos = self._count(text, self.positive_keywords)
        neg = self._count(text, self.negative_keywords)
        base = max(1, pos + neg)
        score = max(0.0, min(1.0, (pos - neg + base) / (2 * base)))
        if pos == 0 and neg == 0:
            label = "UNCERTAIN"
        elif pos > neg * 1.5:
            label = "POSITIVE"
        elif neg > pos * 1.5:
            label = "NEGATIVE"
        elif pos == neg:
            label = "NEUTRAL"
        else:
            label = "MIXED"
        factors = [f"positive_hits={pos}", f"negative_hits={neg}"]
        return SentimentResult(label=label, sentiment_score=score, factors=factors)
