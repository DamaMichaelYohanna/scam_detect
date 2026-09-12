from typing import Literal
from pydantic import BaseModel, Field


class ScamAnalysisResult(BaseModel):
    is_scam: bool = Field(
        description="True if the message or linked website is deemed a scam, phishing, fraud, or high-risk threat."
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0 that this is fraudulent/scam."
    )
    risk_level: Literal["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        description="Risk level evaluation."
    )
    scam_type: str = Field(
        description="Type of scam identified (e.g. 'Wallet Drainer / Phishing', 'Fake Airdrop', 'Fake Support / Impersonation', 'High-Yield Investment / Ponzi', 'Malicious Link', 'None')."
    )
    short_summary: str = Field(
        description="A concise 1-2 sentence explanation of why this was flagged or deemed safe."
    )
    warning_advice: str = Field(
        description="Actionable advice for the user (e.g. 'Never connect your wallet or share your seed phrase. This domain mimics official site.')."
    )
