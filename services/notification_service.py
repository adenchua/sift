import os

import dotenv
import telegram

dotenv.load_dotenv()
env_tg_bot_token = os.getenv("ENV_TG_BOT_TOKEN") or ""


class NotificationService:
    def __init__(self, bot_boken=None):
        self.bot_token = bot_boken if bot_boken is not None else env_tg_bot_token
        self.bot = telegram.Bot(token=self.bot_token)

    async def send_message(self, message: str, receiver_chat_id: str):
        """
        sends a message to the client through the Telegram bot
        """
        await self.bot.send_message(chat_id=receiver_chat_id, text=message)
