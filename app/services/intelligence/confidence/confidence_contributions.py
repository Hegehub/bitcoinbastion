def build_contributions(values: dict[str, tuple[float, float]]) -> list[dict[str, float | str]]:
    out: list[dict[str, float | str]] = []
    for factor, (value, weight) in values.items():
        out.append(
            {"factor": factor, "value": value, "weight": weight, "contribution": value * weight}
        )
    return out
