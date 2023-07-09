import asyncio

from src.telegram_client import telegram_client


async def main():
    channel_messages = await telegram_client.get_channel_messages("sgfooddeals")
    for message in channel_messages:
        print(message.text)


asyncio.get_event_loop().run_until_complete(main())
