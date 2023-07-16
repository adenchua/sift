import asyncio

from typing import List
from telegram_helper.telegram_client import telegram_client
from opensearch_helper.opensearch_client import opensearch_client


async def download_messages(channel_id: str, offset_id: int, themes: List[str]):
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

        opensearch_client.ingest_message(document, document_id)

    # for future crawl to use this offset_id for messages after this
    if max_message_id != -1:
        opensearch_client.update_channel(
            channel_id, updated_fields={"offset_id": max_message_id}
        )


async def main():
    channels = opensearch_client.get_channels()
    for channel in channels:
        channel_id = channel["id"]
        offset_id = channel["offset_id"]
        channel_themes = channel["themes"]
        await download_messages(
            channel_id,
            offset_id=offset_id if offset_id is not None else -1,
            themes=channel_themes,
        )


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
