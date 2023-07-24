from typing import List

from telegram_helper.telegram_client import telegram_client
from database_connector.database_client import database_client

async def extract_and_ingest_messages(channel_id: str, offset_id: int, themes: List[str]):
    max_message_id = -1
    messages = await telegram_client.get_channel_messages(channel_id, offset_id)

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
        database_client.ingest_message(document, document_id)

    # for future crawl to use this offset_id for messages after this
    if max_message_id != -1:
        database_client.update_channel(
            channel_id, updated_fields={"offset_id": max_message_id}
        )