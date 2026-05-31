from pydantic import BaseModel


class FactorContributionResponse(BaseModel):
    factor: str
    weight: float
    explanation: str
