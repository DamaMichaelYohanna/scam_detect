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
        primary_provider = (provider_override or settings.AI_PROVIDER).lower().strip()

        # If primary provider is OpenAI (or default)
        if primary_provider != "gemini":
            if settings.OPENAI_API_KEY:
                logger.info(f"🧠 [1/2] Analyzing threat using Primary Provider: OPENAI ({settings.OPENAI_MODEL})")
                result = await openai_service.analyze_message(
                    message_text=message_text,
                    urls=urls,
                    crypto_addresses=crypto_addresses,
                    exa_context=exa_context,
                )
                if result:
                    return result
                logger.warning("⚠️ OpenAI analysis failed or returned no result. Triggering Gemini fallback...")
            else:
                logger.info("ℹ️ OPENAI_API_KEY not configured. Falling back to Google Gemini...")

            # Fallback to Google Gemini
            if settings.GEMINI_API_KEY:
                logger.info(f"✨ [2/2] Running Fallback Analysis with GEMINI ({settings.GEMINI_MODEL})")
                return await gemini_service.analyze_message(
                    message_text=message_text,
                    urls=urls,
                    crypto_addresses=crypto_addresses,
                    exa_context=exa_context,
                )

        # If user explicitly requested Gemini as primary
        else:
            if settings.GEMINI_API_KEY:
                logger.info(f"✨ [1/2] Analyzing threat using Primary Provider: GEMINI ({settings.GEMINI_MODEL})")
                result = await gemini_service.analyze_message(
                    message_text=message_text,
                    urls=urls,
                    crypto_addresses=crypto_addresses,
                    exa_context=exa_context,
                )
                if result:
                    return result
                logger.warning("⚠️ Gemini analysis failed. Triggering OpenAI fallback...")

            if settings.OPENAI_API_KEY:
                logger.info(f"🧠 [2/2] Running Fallback Analysis with OPENAI ({settings.OPENAI_MODEL})")
                return await openai_service.analyze_message(
                    message_text=message_text,
                    urls=urls,
                    crypto_addresses=crypto_addresses,
                    exa_context=exa_context,
                )

        logger.error("❌ Both AI providers failed or have no valid API keys configured.")
        return None


analyzer_service = AnalyzerService()
