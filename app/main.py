import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.routers.webhook import router as webhook_router
from app.services.telegram_service import telegram_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Check configuration
    logger.info("Starting Telegram Anti-Scam Bot FastAPI service...")
    
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN is missing! Set it in your .env file.")
    if not settings.EXA_API_KEY:
        logger.warning("⚠️ EXA_API_KEY is missing! Set it in your .env file.")
    
    if settings.AI_PROVIDER.lower() == "gemini":
        if not settings.GEMINI_API_KEY:
            logger.warning("⚠️ GEMINI_API_KEY is missing! Set it in your .env file for Gemini analysis.")
        else:
            logger.info(f"✨ Active AI Provider: Google Gemini ({settings.GEMINI_MODEL})")
    else:
        if not settings.OPENAI_API_KEY:
            logger.warning("⚠️ OPENAI_API_KEY is missing! Set it in your .env file for OpenAI analysis.")
        else:
            logger.info(f"✨ Active AI Provider: OpenAI ({settings.OPENAI_MODEL})")

    # Start Polling or register Webhook based on mode
    from app.services.poller_service import poller_service

    if settings.POLLING_MODE:
        logger.info("🚀 POLLING_MODE is enabled. Starting long-polling service...")
        await poller_service.start()
    elif settings.WEBHOOK_URL and settings.TELEGRAM_BOT_TOKEN:
        webhook_target = f"{settings.WEBHOOK_URL.rstrip('/')}/webhook/telegram"
        logger.info(f"Automatically registering webhook target: {webhook_target}")
        try:
            res = await telegram_service.set_webhook(
                webhook_url=webhook_target,
                secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
            )
            logger.info(f"Webhook setup result: {res}")
        except Exception as e:
            logger.error(f"Failed to auto-register webhook on startup: {e}")

    yield

    # Shutdown
    if settings.POLLING_MODE:
        await poller_service.stop()
    logger.info("Shutting down Telegram Anti-Scam Bot FastAPI service...")


app = FastAPI(
    title="Telegram Anti-Scam Bot",
    description="Real-time Telegram group scam and phishing detector powered by Exa.ai, OpenAI, and Google Gemini",
    version="1.0.0",
    lifespan=lifespan,
)

# Include Routers
app.include_router(webhook_router)


@app.get("/")
async def root():
    return {
        "service": "Telegram Anti-Scam Bot API",
        "status": "online",
        "docs": "/docs",
        "configured": {
            "ai_provider": settings.AI_PROVIDER,
            "gemini_model": settings.GEMINI_MODEL,
            "gemini_key_set": bool(settings.GEMINI_API_KEY),
            "openai_model": settings.OPENAI_MODEL,
            "openai_key_set": bool(settings.OPENAI_API_KEY),
            "telegram_token_set": bool(settings.TELEGRAM_BOT_TOKEN),
            "exa_api_key_set": bool(settings.EXA_API_KEY),
            "risk_threshold": settings.RISK_THRESHOLD,
            "polling_mode": settings.POLLING_MODE,
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
