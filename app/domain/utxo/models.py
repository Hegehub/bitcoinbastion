from dataclasses import dataclass


@dataclass(slots=True)
class UTXOEntry:
    value_sats: int


@dataclass(slots=True)
class FeeScenario:
    fee_rate_sat_vb: float
    label: str
