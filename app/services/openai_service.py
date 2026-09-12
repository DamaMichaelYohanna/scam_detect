import logging
from typing import Optional
from openai import AsyncOpenAI
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

Provide a structured, accurate analysis.
"""


class OpenAIService:
    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None

    def _get_client(self) -> Optional[AsyncOpenAI]:
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured. Skipping OpenAI analysis.")
            return None
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def analyze_message(
        self,
        message_text: str,
        urls: list[str],
        crypto_addresses: list[str],
        exa_context: str
    ) -> Optional[ScamAnalysisResult]:
        client = self._get_client()
        if not client:
            return None

        user_content = f"""### Telegram Message:
"{message_text}"

### Detected Entities:
- URLs: {urls if urls else 'None'}
- Crypto Addresses: {crypto_addresses if crypto_addresses else 'None'}

### Real-Time Live Web Intelligence (Exa.ai):
{exa_context}

Analyze if this message or its destination constitutes a scam, phishing attempt, or security threat.
"""

        try:
            response = await client.beta.chat.completions.parse(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                response_format=ScamAnalysisResult,
                temperature=0.1,
            )
            return response.choices[0].message.parsed
        except Exception as e:
            logger.error(f"Error during OpenAI scam analysis: {e}")
            return None


openai_service = OpenAIService()
