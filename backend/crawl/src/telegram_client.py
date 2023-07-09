import os
import telethon
import dotenv


class TelegramClient:
    _client = None

    def __init__(self):
        dotenv.load_dotenv()
        api_id = os.getenv("ENV_TG_API_ID") or ""
        api_hash = os.getenv("ENV_TG_API_HASH") or ""
        self._client = telethon.TelegramClient("anon", api_id=api_id, api_hash=api_hash)
        self._client.start()

    async def get_channel_messages(self, channel_id: str):
        channel = await self._client.get_entity(channel_id)
        return await self._client.get_messages(channel, limit=10)

    async def send_message(self, message: str, target_id: str):
        # stub
        pass


telegram_client = TelegramClient()
