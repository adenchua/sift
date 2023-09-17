from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import os
import dotenv

from services.subscriber_service import (
    SubscriberService,
    Subscriber,
    SubscriberExistsException,
)

dotenv.load_dotenv()
telegram_bot_token = os.getenv("ENV_TG_BOT_TOKEN") or ""


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribes a user from receiving messages"""
    subscriber_service = SubscriberService()

    user = update.message.from_user
    subscriber_username = user["username"]

    try:
        subscriber_exist = subscriber_service.check_subscriber_exists(subscriber_id=subscriber_username)
        if not subscriber_exist:
            await update.message.reply_text("Eh? I don't even know you.")
            return

        subscriber_service.toggle_subscription(subscriber_id=subscriber_username, is_subscribed=False)
        await update.message.reply_text("Done. This is the last time you'll hear from me.")
    except:
        await update.message.reply_text(f"Something went wrong, please try again later")


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribes a new user to the bot to start receiving messages. If a user had previously unsubscribed, it will re-subscribe the user"""
    subscriber_service = SubscriberService()

    user = update.message.from_user
    subscriber_username = user["username"]
    subscriber_telegram_id = str(user["id"])

    new_subscriber = Subscriber(id=subscriber_username, telegram_id=subscriber_telegram_id)

    try:
        subscriber_already_exists = subscriber_service.check_subscriber_exists(subscriber_id=subscriber_username)

        # subscriber already exist, re-subscribes the person instead
        if subscriber_already_exists:
            subscriber_service.toggle_subscription(subscriber_id=subscriber_username, is_subscribed=True)
            await update.message.reply_text(
                f"I have re-enabled your subscription! You'll hear from me soon, master {subscriber_username}"
            )
            return

        subscriber_service.add_subscriber(subscriber=new_subscriber)
        await update.message.reply_text(
            f"Greetings master {subscriber_username}. Thank you for subscribing to Sift! Let's set up some subscription themes shall we?"
        )
    except SubscriberExistsException:
        await update.message.reply_text(f"You have already subscribed, master {subscriber_username}")
    except:
        await update.message.reply_text(f"Something went wrong, please try again later")


async def handle_other_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send back response for all other text messsages sent to the bot"""
    await update.message.reply_text("Sorry, I don't quite understand your message")


def main() -> None:
    """Start the bot."""
    print("initializing bot...")
    application = Application.builder().token(telegram_bot_token).build()

    # handle different commands
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))

    # on non command i.e message - send back generic dont understand message
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_other_messages))

    print("telegram bot listening...")
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
