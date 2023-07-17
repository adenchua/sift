import sys
import asyncio

sys.path.append("..")

from opensearch_helper.opensearch_client import opensearch_client
from telegram_helper.telegram_client import telegram_client


async def main():
    users = opensearch_client.get_users()

    for user in users:
        user_id = user["id"]
        keywords_dict_list = user["keywords"]

        for keywords_dict in keywords_dict_list:
            theme = keywords_dict["theme"]
            keywords = keywords_dict["keywords"]
            timestamp = keywords_dict["last_crawl_timestamp"]

            # update last crawl date to current date
            opensearch_client.update_subscriber_theme_timestamp(user_id, theme=theme)
            messages = opensearch_client.get_messages(keywords, theme, timestamp)

            for message in messages:
                await telegram_client.send_message(
                    message=message["text"], target_id=user_id
                )


if __name__ == "__main__":
    print("Starting notification service...")
    asyncio.get_event_loop().run_until_complete(main())
