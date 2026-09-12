import html
import logging
from typing import Any, Dict, Optional
import httpx
from app.config import settings
from app.services.openai_service import ScamAnalysisResult

logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

    def _get_api_url(self, method: str) -> str:
        return f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        reply_to_message_id: Optional[int] = None,
        parse_mode: str = "HTML",
    ) -> Optional[Dict[str, Any]]:
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN not configured. Skipping sending message.")
            return None

        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(self._get_api_url("sendMessage"), json=payload)
                res_data = response.json()
                if not res_data.get("ok"):
                    logger.error(f"Telegram API sendMessage error: {res_data}")
                return res_data
            except Exception as e:
                logger.error(f"Failed to send Telegram message: {e}")
                return None

    async def delete_message(self, chat_id: int | str, message_id: int) -> bool:
        """Deletes a message from a group (requires bot admin delete privileges)."""
        if not settings.TELEGRAM_BOT_TOKEN:
            return False
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.post(
                    self._get_api_url("deleteMessage"),
                    json={"chat_id": chat_id, "message_id": message_id}
                )
                data = res.json()
                if data.get("ok"):
                    logger.info(f"🗑️ Successfully deleted scam message #{message_id} in chat {chat_id}")
                    return True
                else:
                    logger.warning(f"Failed to delete message: {data.get('description')}")
                    return False
            except Exception as e:
                logger.error(f"Error deleting message: {e}")
                return False

    async def ban_chat_member(
        self,
        chat_id: int | str,
        user_id: int | str,
        revoke_messages: bool = True
    ) -> bool:
        """Bans a member from the group (requires bot admin restrict/ban privileges)."""
        if not settings.TELEGRAM_BOT_TOKEN or not user_id:
            return False
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                payload = {
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "revoke_messages": revoke_messages,
                }
                res = await client.post(self._get_api_url("banChatMember"), json=payload)
                data = res.json()
                if data.get("ok"):
                    logger.warning(f"🚫 Successfully banned scam user ID {user_id} from chat {chat_id}")
                    return True
                else:
                    logger.warning(
                        f"Could not ban user {user_id}: {data.get('description')} "
                        "(Ensure bot is Admin with 'Ban Users' permission)"
                    )
                    return False
            except Exception as e:
                logger.error(f"Error banning chat member: {e}")
                return False

    async def send_scam_warning(
        self,
        chat_id: int | str,
        reply_to_message_id: Optional[int],
        result: ScamAnalysisResult,
        user_name: Optional[str] = None,
        was_banned: bool = False,
        was_deleted: bool = False,
    ) -> Optional[Dict[str, Any]]:
        badge_map = {
            "CRITICAL": "🚨 <b>CRITICAL THREAT REMOVED</b> 🚨" if was_banned else "🚨 <b>CRITICAL RISK DETECTED</b> 🚨",
            "HIGH": "⚠️ <b>SCAM / PHISHING DETECTED</b> ⚠️",
            "MEDIUM": "⚠️ <b>SUSPICIOUS CONTENT DETECTED</b>",
            "LOW": "ℹ️ <b>LOW RISK NOTICE</b>",
            "SAFE": "✅ <b>CONTENT VERIFIED</b>",
        }
        header = badge_map.get(result.risk_level, "⚠️ <b>SECURITY ALERT</b>")

        escaped_type = html.escape(result.scam_type)
        escaped_summary = html.escape(result.short_summary)
        escaped_advice = html.escape(result.warning_advice)
        confidence_percent = int(result.confidence * 100)

        action_notes = []
        if was_deleted:
            action_notes.append("🗑️ <i>Malicious message deleted</i>")
        if was_banned:
            target = f"@{user_name}" if user_name else "Offending user"
            action_notes.append(f"🚫 <b>{html.escape(target)} has been removed and banned from this group.</b>")

        actions_section = ("\n" + "\n".join(action_notes) + "\n") if action_notes else ""

        message_html = (
            f"{header}\n{actions_section}\n"
            f"🎯 <b>Threat Type:</b> {escaped_type}\n"
            f"📊 <b>Confidence Score:</b> {confidence_percent}% | <b>Risk:</b> {result.risk_level}\n\n"
            f"🔍 <b>Why this was flagged:</b>\n"
            f"{escaped_summary}\n\n"
            f"🛡️ <b>Safety Advice:</b>\n"
            f"{escaped_advice}\n\n"
            f"<i>🔒 Stay vigilant. Never connect wallets to unverified links or share seed phrases.</i>"
        )

        return await self.send_message(
            chat_id=chat_id,
            text=message_html,
            reply_to_message_id=reply_to_message_id if not was_deleted else None,
            parse_mode="HTML",
        )

    async def set_webhook(self, webhook_url: str, secret_token: Optional[str] = None) -> Dict[str, Any]:
        url = self._get_api_url("setWebhook")
        payload: Dict[str, Any] = {
            "url": webhook_url,
            "allowed_updates": ["message", "edited_message", "channel_post"],
        }
        if secret_token:
            payload["secret_token"] = secret_token

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, data=payload)
            return response.json()

    async def get_webhook_info(self) -> Dict[str, Any]:
        url = self._get_api_url("getWebhookInfo")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            return response.json()

    async def delete_webhook(self) -> Dict[str, Any]:
        url = self._get_api_url("deleteWebhook")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url)
            return response.json()


telegram_service = TelegramService()
