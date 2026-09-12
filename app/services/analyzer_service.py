import logging
from typing import Optional
from app.config import settings
from app.models.scam_models import ScamAnalysisResult
from app.services.gemini_service import gemini_service
from app.services.openai_service import openai_service

logger = logging.getLogger(__name__)


class AnalyzerService:
    async def analyze_message(
        self,
        message_text: str,
        urls: list[str],
        crypto_addresses: list[str],
        exa_context: str,
        provider_override: Optional[str] = None,
    ) -> Optional[ScamAnalysisResult]:
        provider = (provider_override or settings.AI_PROVIDER).lower().strip()
        logger.info(f"🧠 Running scam threat evaluation using AI Provider: [{provider.upper()}]")

        if provider == "gemini":
            result = await gemini_service.analyze_message(
                message_text=message_text,
                urls=urls,
                crypto_addresses=crypto_addresses,
                exa_context=exa_context,
            )
            if result:
                return result
            # Optional fallback to OpenAI if Gemini fails or is unconfigured
            if settings.OPENAI_API_KEY:
                logger.info("Gemini analysis yielded no result; falling back to OpenAI...")
                return await openai_service.analyze_message(
                    message_text=message_text,
                    urls=urls,
                    crypto_addresses=crypto_addresses,
                    exa_context=exa_context,
                )

        else:  # Default: openai
            result = await openai_service.analyze_message(
                message_text=message_text,
                urls=urls,
                crypto_addresses=crypto_addresses,
                exa_context=exa_context,
            )
            if result:
                return result
            # Optional fallback to Gemini if OpenAI fails or is unconfigured
            if settings.GEMINI_API_KEY:
                logger.info("OpenAI analysis yielded no result; falling back to Gemini...")
                return await gemini_service.analyze_message(
                    message_text=message_text,
                    urls=urls,
                    crypto_addresses=crypto_addresses,
                    exa_context=exa_context,
                )

        return None


analyzer_service = AnalyzerService()
