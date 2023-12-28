import os
from typing import Optional

import dotenv
import telethon
from telethon.sessions import StringSession

from services.channel_service import Channel, ChannelService
from services.logging_service import LoggingService
from services.message_service import Message, MessageService

dotenv.load_dotenv()
env_api_id = os.getenv("ENV_TG_API_ID") or ""
env_api_hash = os.getenv("ENV_TG_API_HASH") or ""
env_string_session = os.getenv("ENV_TG_STRING_SESSION") or ""
LOGGING_MODULE = "DOWNLOAD-SERVICE"


class DownloadService:
    def __init__(self, api_id=None, api_hash=None):
        self.logging_service = LoggingService()
        self.api_id = api_id if api_id is not None else env_api_id
        self.api_hash = api_hash if api_hash is not None else env_api_hash
        # using string session to authenticate instead of anon, skip the login process
        self.client = telethon.TelegramClient(
            StringSession(env_string_session), api_id=self.api_id, api_hash=self.api_hash
        ).start()

    async def __fetch_messages_from_channel(self, channel_id: str, offset_id: Optional[int] = None):
        """Retrieves messages from a telegram channel later than an offset id.

        If the offset id is not provided, it will retrieve the latest 100 messages from the channel

        Returns a list of messages
        """
        try:
            MESSAGE_SIZE_FOR_NEW_CHANNELS = 100
            channel = await self.client.get_entity(channel_id)

            if offset_id is None:
                # retrieving back latest 100 messages for new channels.
                return await self.client.get_messages(
                    channel,
                    limit=MESSAGE_SIZE_FOR_NEW_CHANNELS,
                )

            # retrieve messages later than a given offset_id
            return await self.client.get_messages(channel, limit=None, offset_id=offset_id, reverse=True)
        except Exception as error:
            error_content = {"channel_id": channel_id, "offset_id": offset_id, "error": error}
            self.logging_service.log_error(
                message=f"Failed to fetch message from channel: {error_content}", module=LOGGING_MODULE
            )

    async def download_messages_from_channel(self, channel: Channel):
        """Downloads messages from a telegram channel and ingests to the database

        If the offset id is not provided, it will download the latest 100 messages from the channel
        """
        channel_service = ChannelService()
        message_service = MessageService()
        channel_id = channel["id"]
        offset_id = channel["offset_id"]
        themes = channel["themes"]

        max_message_id = -1  # to set as the new offset id
        messages = await self.__fetch_messages_from_channel(channel_id=channel_id, offset_id=offset_id)

        for message in messages:
            # message id is unique to their own channels only. Need to combine with channel_id to create a unique ID
            message_id = int(message.id)
            max_message_id = max(message_id, max_message_id)  # the latest message id in the channel will be the largest
            document_id = ("-").join([channel_id, str(message_id)])
            document = Message(
                text=message.text,
                themes=themes,
                timestamp=message.date,
                channel_id=channel_id,
                message_id=document_id,
            )

            message_service.create_message(
                message=document,
            )

        # for future crawl to use this offset_id for messages after this
        if max_message_id != -1:
            channel_service.update_channel_offset(channel_id=channel_id, new_offset_id=max_message_id)


download_service = DownloadService()
