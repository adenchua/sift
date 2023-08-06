from typing import List

from telegram_helper.telegram_client import telegram_client
from services.channel_service import ChannelService
from services.message_service import MessageService


async def extract_and_ingest_messages(
    channel_id: str, offset_id: int, themes: List[str]
):
    channel_service = ChannelService()
    message_service = MessageService()

    max_message_id = -1
    messages = await telegram_client.get_telegram_channel_messages(
        channel_id=channel_id, offset_id=offset_id
    )

    for message in messages:
        # unique to a particular channel. Need to combine with channel_id
        message_id = int(message.id)
        # the latest message id will be the largest
        max_message_id = max(message_id, max_message_id)
        document = {
            "text": message.text,
            "themes": themes,
            "timestamp": message.date,
            "channel_id": channel_id,
        }
        document_id = ("-").join([channel_id, str(message_id)])
        message_service.ingest_message(message=document, message_id=document_id)

    # for future crawl to use this offset_id for messages after this
    if max_message_id != -1:
        channel_service.update_channel_offset(
            channel_id=channel_id, new_offset_id=max_message_id
        )
