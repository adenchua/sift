import argparse
import asyncio

from services.channel_service import ChannelService
from services.message_service import MessageService
from services.subscriber_service import SubscriberService
from services.telegram_bot_client import TelegramBotClient
from utils.date_helper import get_latest_iso_datetime
from utils.message_helper import extract_and_ingest_messages


async def send_message_from_bot(message: str, receiver_chat_id: str):
    """send messages from bot. A user must first interact with this bot first"""
    telegram_bot_client = TelegramBotClient()
    await telegram_bot_client.send_message(message, receiver_chat_id)


async def notify_subscribers():
    subscriber_service = SubscriberService()
    message_service = MessageService()

    subscribers = subscriber_service.get_subscribers(True)

    for subscriber in subscribers:
        subscriber_id = subscriber["id"]
        subscribed_themes = subscriber["subscribed_themes"]

        # for each subscribed theme, retrieve messages based on keywords and last crawl timestamp
        # messages found are considered matches, sent back to the subscriber via telegram
        # last crawl timestamp is updated with the latest message timestamp
        for subscribed_theme in subscribed_themes:
            theme = subscribed_theme["theme"]
            keywords = subscribed_theme["keywords"]
            timestamp = subscribed_theme["last_crawl_timestamp"]
            message_iso_dates = []  # datetime for comparison later

            messages = message_service.get_messages(keywords_list=keywords, theme=theme, iso_date=timestamp)

            for message in messages:
                message_iso_dates.append(message["timestamp"])
                await send_message_from_bot(message["text"], subscriber_id)

            latest_message_iso_datetime = get_latest_iso_datetime(message_iso_dates)

            # update subscriber last crawl timestamp to the latest message datetime
            # subsequent retrievals will be after this date for this theme
            if latest_message_iso_datetime is not None:
                subscriber_service.update_subscriber_theme_timestamp(
                    subscriber_id=subscriber_id,
                    theme=theme,
                    iso_timestamp=latest_message_iso_datetime,
                )


async def download_telegram_messages():
    channel_service = ChannelService()

    channels = channel_service.get_active_channels()
    for channel in channels:
        channel_id = channel["id"]
        offset_id = channel["offset_id"]
        channel_themes = channel["themes"]
        await extract_and_ingest_messages(
            channel_id,
            offset_id=-1 if offset_id is None else offset_id,
            themes=channel_themes,
        )


async def start_background_download_service():
    """
    runs the crawling of messages on a set interval
    """
    while True:
        await download_telegram_messages()
        await asyncio.sleep(60 * 15)  # download messages every 15 minutes


async def start_background_notify_service():
    """
    runs notification service of subscribers on a set interval
    """
    while True:
        await notify_subscribers()
        await asyncio.sleep(60 * 60)  # notify subscriber every 60 minutes


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--notify", action="store_true")
    parser.add_argument("--start", action="store_true")

    args = parser.parse_args()

    if args.download:
        print("Starting telegram message download service...")
        await download_telegram_messages()

    if args.notify:
        print("Starting notification service...")
        await notify_subscribers()

    if args.start:
        print("Starting download and notification background service...")
        task_1 = asyncio.create_task(start_background_download_service())
        task_2 = asyncio.create_task(start_background_notify_service())
        await asyncio.wait([task_1, task_2])


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
