import os

import dotenv
import telethon

dotenv.load_dotenv()
env_api_id = os.getenv("ENV_TG_API_ID") or ""
env_api_hash = os.getenv("ENV_TG_API_HASH") or ""


class TelegramClient:
    def __init__(self, api_id=None, api_hash=None):
        self.api_id = api_id if api_id is not None else env_api_id
        self.api_hash = api_hash if api_hash is not None else env_api_hash

        self.client = telethon.TelegramClient(
            "anon", api_id=self.api_id, api_hash=self.api_hash
        )
        self.client.start()

    async def get_channel_messages(self, channel_id: str, offset_id: int = -1):
        channel = await self.client.get_entity(channel_id)

        if offset_id == -1:
            # sending back only latest 100 messages for new channels.
            # Do not want to slow down the api call
            return await self.client.get_messages(
                channel,
                limit=100,
            )

        return await self.client.get_messages(
            channel, limit=None, offset_id=offset_id, reverse=True
        )

    async def send_message(self, message: str, target_id: str):
        await self.client.send_message(target_id, message)


telegram_client = TelegramClient()
