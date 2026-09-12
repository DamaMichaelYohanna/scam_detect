import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class StrikeService:
    def __init__(self):
        # Key: (chat_id, user_id) -> strike_count
        self._strikes: Dict[Tuple[int | str, int | str], int] = {}

    def record_strike(self, chat_id: int | str, user_id: int | str) -> int:
        """Records a new strike for a user in a specific chat and returns current strike count."""
        key = (str(chat_id), str(user_id))
        self._strikes[key] = self._strikes.get(key, 0) + 1
        current_count = self._strikes[key]
        logger.info(f"⚡ Strike recorded for user {user_id} in chat {chat_id}. Total strikes: {current_count}")
        return current_count

    def get_strikes(self, chat_id: int | str, user_id: int | str) -> int:
        """Returns the current strike count for a user in a specific chat."""
        key = (str(chat_id), str(user_id))
        return self._strikes.get(key, 0)

    def reset_strikes(self, chat_id: int | str, user_id: int | str):
        """Resets strikes for a user in a specific chat."""
        key = (str(chat_id), str(user_id))
        if key in self._strikes:
            del self._strikes[key]


strike_service = StrikeService()
