import asyncio
import logging
from typing import Any, Dict, List
import httpx
from app.config import settings
from app.routers.webhook import process_scam_detection
from app.services.detector_service import detector_service
from app.services.telegram_service import telegram_service

logger = logging.getLogger(__name__)


class PollerService:
    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self._offset = 0

    async def start(self):
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN not configured. Cannot start Telegram long-polling.")
            return

        # Ensure no leftover webhook blocks polling
        logger.info("Initializing Telegram Long-Polling (ensuring clean webhook slate)...")
        await telegram_service.delete_webhook()

        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("🤖 Telegram Long-Polling service is ACTIVE! Listening for group messages...")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Telegram Poller stopped.")

    async def _handle_update(self, update: Dict[str, Any]):
        update_id = update.get("update_id", "N/A")
        message = update.get("message") or update.get("edited_message") or update.get("channel_post")
        if not message:
            return

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
            f"From: @{sender_name} (ID: {user_id}) | Message ID: {message_id} | Text: \"{text_preview}\""
        )

        if not chat_id or not message_id or not text.strip():
            return

        # 1. Quick Heuristic Scan
        inspection = detector_service.inspect_message(text)
        if not inspection.should_deep_scan:
            logger.info(f"✅ Message #{message_id} in '{chat_title}' evaluated as SAFE (No triggers/URLs).")
            return

        logger.warning(
            f"🔍 Message #{message_id} flagged for deep scan! Reason: {inspection.quick_reason} | "
            f"Extracted URLs: {inspection.urls} | Crypto: {inspection.crypto_addresses}"
        )

        # 2. Run Exa + AI Scam Detection in background
        asyncio.create_task(
            process_scam_detection(
                chat_id=chat_id,
                message_id=message_id,
                user_id=user_id,
                user_name=sender_name,
                text=text,
                urls=inspection.urls,
                crypto_addresses=inspection.crypto_addresses,
                matched_keywords=inspection.matched_keywords,
            )
        )

    async def _poll_loop(self):
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getUpdates"
        async with httpx.AsyncClient(timeout=35.0) as client:
            while self._running:
                try:
                    params = {
                        "offset": self._offset,
                        "timeout": 20,
                        "allowed_updates": ["message", "edited_message", "channel_post"],
                    }
                    response = await client.get(url, params=params)
                    data = response.json()

                    if not data.get("ok"):
                        logger.error(f"Telegram getUpdates error: {data}")
                        await asyncio.sleep(3)
                        continue

                    updates: List[Dict[str, Any]] = data.get("result", [])
                    for update in updates:
                        self._offset = update["update_id"] + 1
                        await self._handle_update(update)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in Telegram poller loop: {e}")
                    await asyncio.sleep(3)


poller_service = PollerService()
