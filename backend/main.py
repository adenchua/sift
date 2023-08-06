import argparse
import asyncio

from telegram_helper.telegram_client import telegram_client
from services.subscriber_service import SubscriberService
from services.channel_service import ChannelService
from services.message_service import MessageService
from utils.message_helper import extract_and_ingest_messages


async def notify_subscribers():
    subscriber_service = SubscriberService()
    message_service = MessageService()

    subscribers = subscriber_service.get_subscribers()

    for subscriber in subscribers:
        user_id = subscriber["id"]
        keywords_dict_list = subscriber["keywords"]

        for keywords_dict in keywords_dict_list:
            theme = keywords_dict["theme"]
            keywords = keywords_dict["keywords"]
            timestamp = keywords_dict["last_crawl_timestamp"]

            # update last crawl date to current date
            subscriber_service.update_subscriber_theme_timestamp(
                subscriber_id=user_id, theme=theme
            )
            messages = message_service.get_messages(
                keywords_list=keywords, theme=theme, iso_date=timestamp
            )

            for message in messages:
                await telegram_client.send_message(
                    message=message["text"], target_id=user_id
                )


async def download_telegram_messages():
    channel_service = ChannelService()

    channels = channel_service.get_channels()
    for channel in channels:
        channel_id = channel["id"]
        offset_id = channel["offset_id"]
        channel_themes = channel["themes"]
        await extract_and_ingest_messages(
            channel_id,
            offset_id=-1 if offset_id is None else offset_id,
            themes=channel_themes,
        )


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--notify", action="store_true")

    args = parser.parse_args()

    if args.download:
        print("Starting telegram message download service...")
        await download_telegram_messages()

    if args.notify:
        print("Starting notification service...")
        await notify_subscribers()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
