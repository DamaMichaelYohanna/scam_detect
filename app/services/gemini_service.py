import json
import logging
from typing import Optional
from google import genai
from google.genai import types
from app.config import settings
from app.models.scam_models import ScamAnalysisResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an elite cybersecurity and Web3 anti-scam intelligence officer analyzing Telegram messages and live web data.

Your goal is to protect Telegram community members from:
1. Phishing links, fake domains (typosquatting like Uniswapp, Raydiurn, OpenSea fake clones).
2. Crypto wallet drainers (Permit2 approvals, malicious signature requests, fake airdrop claim buttons).
3. Fake admin / Telegram support impersonation ("DM me to fix your wallet", "Verify on support portal").
4. High-yield investment scams, crypto doublers, guaranteed return schemes.
5. Malicious files, fake Telegram Premium gifts, Discord nitro scams.

You will be given:
- The raw message text sent in a Telegram group
- Any extracted URLs or crypto addresses
- Live web content fetched via Exa.ai (page title, text, domain reputation intelligence)

Carefully evaluate the authenticity:
- If the live page text asks users to connect wallets for unverified airdrops, uses urgent/FOMO language, has broken grammar, or mimics known brands -> High / Critical Scam.
- If it is legitimate conversation, news, genuine project documentation -> SAFE / LOW.
- If uncertain, set risk_level to MEDIUM or LOW, and is_scam=False unless strong fraud indicators are present.

Provide a structured, accurate analysis according to the schema.
"""


class GeminiService:
    def __init__(self):
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> Optional[genai.Client]:
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not configured. Skipping Gemini analysis.")
            return None
        if self._client is None:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    async def analyze_message(
        self,
        message_text: str,
        urls: list[str],
        crypto_addresses: list[str],
        exa_context: str,
    ) -> Optional[ScamAnalysisResult]:
        client = self._get_client()
        if not client:
            return None

        prompt = f"""### Telegram Message:
"{message_text}"

### Detected Entities:
- URLs: {urls if urls else 'None'}
- Crypto Addresses: {crypto_addresses if crypto_addresses else 'None'}

### Real-Time Live Web Intelligence (Exa.ai):
{exa_context}

Analyze if this message or its destination constitutes a scam, phishing attempt, or security threat.
"""

        try:
            # Call Google GenAI with structured JSON output
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=ScamAnalysisResult,
                    temperature=0.1,
                ),
            )

            if hasattr(response, "parsed") and response.parsed:
                if isinstance(response.parsed, ScamAnalysisResult):
                    return response.parsed
                if isinstance(response.parsed, dict):
                    return ScamAnalysisResult(**response.parsed)

            if response.text:
                data = json.loads(response.text)
                return ScamAnalysisResult(**data)

            return None
        except Exception as e:
            logger.error(f"Error during Gemini scam analysis: {e}", exc_info=True)
            return None


gemini_service = GeminiService()
