import os

import dotenv
import telegram

from services.logging_service import LoggingService

dotenv.load_dotenv()
env_tg_bot_token = os.getenv("ENV_TG_BOT_TOKEN") or ""


class NotificationService:
    def __init__(self, bot_boken=None):
        self.bot_token = bot_boken if bot_boken is not None else env_tg_bot_token
        self.bot = telegram.Bot(token=self.bot_token)
        self.logging_service = LoggingService()

    def __format_telegram_string(self, string: str) -> str:
        """
        Telegram message formatting is different from telegram bot API message syntax
        This function formats telegram format syntax to telegram bot api message syntax, HTML
        """
        string = string.replace("**", "<b>")  # bold word
        string = string.replace("__", "<i>")  # italic
        return string

    async def send_message(self, message: str, receiver_chat_id: str):
        """
        sends a message to the client through the Telegram bot
        """
        try:
            formatted_message = self.__format_telegram_string(message)
            await self.bot.send_message(chat_id=receiver_chat_id, text=formatted_message, parse_mode="HTML")
        except Exception as error:
            self.logging_service.log_error(
                message=f"Failed to send message through telegram bot: {error}", module="NOTIFICATION-SERVICE"
            )
