import argparse
import asyncio

from telegram_helper.telegram_client import telegram_client
from database_connector.database_client import database_client
from utils.message_helper import extract_and_ingest_messages


async def notify_subscribers():
    users = database_client.get_users()

    for user in users:
        user_id = user["id"]
        keywords_dict_list = user["keywords"]

        for keywords_dict in keywords_dict_list:
            theme = keywords_dict["theme"]
            keywords = keywords_dict["keywords"]
            timestamp = keywords_dict["last_crawl_timestamp"]

            # update last crawl date to current date
            database_client.update_subscriber_theme_timestamp(subscriber_id=user_id, theme=theme)
            messages = database_client.get_messages(query_string_list=keywords, theme=theme, iso_date=timestamp)

            for message in messages:
                await telegram_client.send_message(
                    message=message["text"], target_id=user_id
                )


async def download_telegram_messages():
    channels = database_client.get_channels()
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
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--notify', action='store_true')

    args = parser.parse_args()

    if args.download:
        print("Starting telegram message download service...")
        await download_telegram_messages()
    
    if args.notify:
        print("Starting notification service...")
        await notify_subscribers()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
