from pydantic import BaseModel


class FactorContribution(BaseModel):
    factor: str
    weight: float
    explanation: str
