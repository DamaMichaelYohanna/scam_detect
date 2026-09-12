import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from app.config import settings
from app.services.analyzer_service import analyzer_service
from app.services.detector_service import detector_service
from app.services.exa_service import exa_service
from app.services.strike_service import strike_service
from app.services.telegram_service import telegram_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["Telegram Webhook"])


async def process_scam_detection(
    chat_id: int | str,
    message_id: int,
    user_id: Optional[int | str],
    user_name: Optional[str],
    text: str,
    urls: list[str],
    crypto_addresses: list[str],
    matched_keywords: list[str],
):
    logger.info(
        f"Starting deep scam analysis for chat_id={chat_id}, message_id={message_id}, "
        f"sender=@{user_name or 'N/A'} (ID: {user_id})"
    )
    try:
        # 1. Fetch live page contents and search intelligence using Exa.ai
        exa_result = await exa_service.extract_context(
            urls=urls,
            message_text=text,
            matched_keywords=matched_keywords,
        )
        exa_context = exa_result.to_combined_context()

        # 2. Analyze with configured AI Provider (OpenAI or Gemini)
        scam_result = await analyzer_service.analyze_message(
            message_text=text,
            urls=urls,
            crypto_addresses=crypto_addresses,
            exa_context=exa_context,
        )

        if not scam_result:
            logger.warning("AI scam analysis returned no result.")
            return

        logger.info(
            f"Analysis complete: is_scam={scam_result.is_scam}, "
            f"risk_level={scam_result.risk_level}, confidence={scam_result.confidence:.2f}"
        )

        # 3. If classified as scam and confidence meets threshold:
        if scam_result.is_scam and scam_result.confidence >= settings.RISK_THRESHOLD:
            # Record strike for user in this chat
            strike_count = strike_service.record_strike(chat_id, user_id) if user_id else 1
            max_strikes = settings.MAX_STRIKES_BAN
            warn_threshold = settings.WARN_STRIKES

            was_deleted = False
            was_banned = False

            # Always delete scam messages immediately
            if settings.AUTO_DELETE_SCAM_MESSAGE:
                was_deleted = await telegram_service.delete_message(chat_id, message_id)

            # Check if user reached ban strike threshold (>= 5 strikes)
            if strike_count >= max_strikes and settings.AUTO_BAN and user_id:
                was_banned = await telegram_service.ban_chat_member(chat_id, user_id)
                logger.warning(
                    f"🚫 User {user_id} reached {strike_count}/{max_strikes} strikes! Banned from chat {chat_id}."
                )

            # Send public warning / notice if enabled (always at strikes >= 3 or if banned, or configurable)
            if settings.AUTO_WARN:
                logger.warning(
                    f"⚠️ SCAM ACTION in chat {chat_id}: {scam_result.scam_type} "
                    f"(User: @{user_name}, Strikes: {strike_count}/{max_strikes}, "
                    f"Banned: {was_banned}, Deleted: {was_deleted}). Sending announcement."
                )
                await telegram_service.send_scam_warning(
                    chat_id=chat_id,
                    reply_to_message_id=message_id,
                    result=scam_result,
                    user_name=user_name,
                    strike_count=strike_count,
                    max_strikes=max_strikes,
                    was_banned=was_banned,
                    was_deleted=was_deleted,
                )
    except Exception as e:
        logger.error(f"Error in process_scam_detection: {e}", exc_info=True)


@router.post("/telegram")
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None),
):
    # Verify Secret Token if present
    if settings.TELEGRAM_WEBHOOK_SECRET and x_telegram_bot_api_secret_token:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.warning("⛔ Unauthorized webhook call: Invalid secret token header.")
            raise HTTPException(status_code=403, detail="Invalid secret token")

    data: Dict[str, Any] = await request.json()
    update_id = data.get("update_id", "N/A")

    # Extract message / channel_post / edited_message
    message = data.get("message") or data.get("edited_message") or data.get("channel_post")
    if not message:
        logger.info(f"📩 Telegram Update #{update_id} received (Non-message update: {list(data.keys())})")
        return {"ok": True, "status": "no_message_found"}

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    chat_title = chat.get("title") or chat.get("username") or "Direct Chat"
    chat_type = chat.get("type", "unknown")
    sender = message.get("from", {})
    user_id = sender.get("id")
    sender_name = sender.get("username") or sender.get("first_name") or f"User_{user_id}"
    message_id = message.get("message_id")
    text = message.get("text") or message.get("caption") or ""

    text_preview = (text[:80] + "...") if len(text) > 80 else (text or "<Empty / Media only>")

    logger.info(
        f"📩 [INCOMING TELEGRAM MESSAGE] | Update #{update_id} | "
        f"Chat: '{chat_title}' (ID: {chat_id}, Type: {chat_type}) | "
        f"From: @{sender_name} | Message ID: {message_id} | Text: \"{text_preview}\""
    )

    if not chat_id or not message_id or not text.strip():
        logger.info(f"ℹ️ Message #{message_id} in chat {chat_id} has no text content to scan. Skipping.")
        return {"ok": True, "status": "empty_content_ignored"}

    # 1. Quick Heuristic / Regex Pre-filter
    inspection = detector_service.inspect_message(text)

    if not inspection.should_deep_scan:
        logger.info(f"✅ Message #{message_id} in '{chat_title}' evaluated as SAFE by heuristic filter (No triggers/URLs).")
        return {"ok": True, "status": "skipped_safe"}

    logger.warning(
        f"🔍 Message #{message_id} flagged for deep scan! Reason: {inspection.quick_reason} | "
        f"Extracted URLs: {inspection.urls} | Crypto: {inspection.crypto_addresses}"
    )

    # 2. Dispatch background task for Exa + AI scan
    background_tasks.add_task(
        process_scam_detection,
        chat_id=chat_id,
        message_id=message_id,
        user_id=user_id,
        user_name=sender_name,
        text=text,
        urls=inspection.urls,
        crypto_addresses=inspection.crypto_addresses,
        matched_keywords=inspection.matched_keywords,
    )

    return {"ok": True, "status": "queued_for_analysis"}


@router.get("/info")
async def get_webhook_status():
    """Retrieve current Telegram webhook registration status."""
    info = await telegram_service.get_webhook_info()
    return {"telegram_webhook_info": info}


@router.post("/setup")
async def setup_webhook(webhook_url: Optional[str] = None):
    """Register or update webhook with Telegram."""
    target_url = webhook_url or settings.WEBHOOK_URL
    if not target_url:
        raise HTTPException(
            status_code=400,
            detail="No webhook URL provided in request or WEBHOOK_URL environment variable."
        )

    # Ensure full webhook endpoint path
    if not target_url.endswith("/webhook/telegram"):
        target_url = f"{target_url.rstrip('/')}/webhook/telegram"

    res = await telegram_service.set_webhook(
        webhook_url=target_url,
        secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
    )
    return {"status": "webhook_registration_attempted", "telegram_response": res, "url": target_url}


@router.post("/delete")
async def delete_webhook():
    """Remove webhook from Telegram (useful when switching to polling)."""
    res = await telegram_service.delete_webhook()
    return {"status": "webhook_deleted", "telegram_response": res}
