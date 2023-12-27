import argparse
import asyncio
import json

from services.channel_service import ChannelService
from services.download_service import download_service
from services.logging_service import LoggingService
from services.message_service import MessageService
from services.notification_service import NotificationService
from services.subscriber_service import SubscriberService
from utils.date_helper import get_latest_iso_datetime

logging_service = LoggingService()


async def send_message_from_bot(message: str, receiver_chat_id: str):
    """send messages from bot. A user must first interact with this bot first"""
    notification_service = NotificationService()
    await notification_service.send_message(message, receiver_chat_id)


async def notify_subscribers():
    subscriber_service = SubscriberService()
    message_service = MessageService()

    subscribers = subscriber_service.get_subscribers(True)

    for subscriber in subscribers:
        subscriber_id = subscriber["id"]
        subscribed_themes = subscriber["subscribed_themes"]

        # for each subscribed theme, retrieve messages based on keywords and last notified timestamp
        # messages found are considered matches, sent back to the subscriber via telegram
        # last notified timestamp is updated with the latest message timestamp
        for subscribed_theme in subscribed_themes:
            theme = subscribed_theme["theme"]
            keywords = subscribed_theme["keywords"]
            timestamp = subscribed_theme["last_notified_timestamp"]
            message_iso_dates = []  # datetime for comparison later

            messages = message_service.get_matched_messages(
                keywords_list=keywords, theme=theme, iso_date_from=timestamp
            )

            for message in messages:
                message_iso_dates.append(message["timestamp"])
                log_content = {"message_id": message["id"], "subscriber_id": subscriber_id}
                logging_service.log_info(f"Sending message to user from telegram bot: {json.dumps(log_content)}")
                await send_message_from_bot(message["text"], subscriber_id)

            latest_message_iso_datetime = get_latest_iso_datetime(message_iso_dates)

            # update subscriber last notified timestamp to the latest message datetime
            # subsequent retrievals will be after this date for this theme
            if latest_message_iso_datetime is not None:
                subscriber_service.update_subscriber_theme_timestamp(
                    subscriber_id=subscriber_id,
                    theme=theme,
                    iso_timestamp=latest_message_iso_datetime,
                )


async def download_telegram_messages():
    """
    loops through all active telegram channels and download messages from it
    """
    channel_service = ChannelService()

    channels = channel_service.get_active_channels()
    for channel in channels:
        log_content = {"channel_id": channel["id"], "channel_offset_id": channel["offset_id"]}
        logging_service.log_info(f"Downloading message from channel: {json.dumps(log_content)}")
        await download_service.download_messages_from_channel(channel=channel)


async def start_background_download_service():
    """
    runs the download of messages on a set interval
    """
    SLEEP_DURATION_SECONDS = 60 * 15  # download messages every 15 minutes
    while True:
        logging_service.log_info("Downloading messages from Telegram")
        await download_telegram_messages()
        logging_service.log_info(f"Downloaded messages from Telegram, sleeping for {SLEEP_DURATION_SECONDS} seconds")
        await asyncio.sleep(SLEEP_DURATION_SECONDS)


async def start_background_notify_service():
    """
    runs notification service of subscribers on a set interval
    """
    SLEEP_DURATION_SECONDS = 60 * 60  # notify subscriber every 60 minutes
    while True:
        logging_service.log_info("Notifying subscribers")
        await notify_subscribers()
        logging_service.log_info(f"Notified subscribers, sleeping for {SLEEP_DURATION_SECONDS} seconds")
        await asyncio.sleep(SLEEP_DURATION_SECONDS)  # notify subscriber every 60 minutes


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--notify", action="store_true")
    parser.add_argument("--start", action="store_true")

    args = parser.parse_args()

    if args.download:
        logging_service.log_info("Starting telegram message download service")
        await download_telegram_messages()

    if args.notify:
        logging_service.log_info("Starting notification service")
        await notify_subscribers()

    if args.start:
        logging_service.log_info("Starting download and notification background service")
        task_1 = asyncio.create_task(start_background_download_service())
        task_2 = asyncio.create_task(start_background_notify_service())
        await asyncio.wait([task_1, task_2])

    logging_service.log_error("Invalid script command to run main script")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
