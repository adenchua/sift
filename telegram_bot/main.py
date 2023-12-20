import sys

sys.path.append("..")

import logging
import os

import dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from services.logging_service import LoggingService
from services.subscriber_service import Subscriber, SubscriberService
from utils.string_helper import clean_string, get_newline_separated_strings

dotenv.load_dotenv()
telegram_bot_token = os.getenv("ENV_TG_BOT_TOKEN") or ""

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
error_logging_service = LoggingService()

THEME_STATE, KEYWORDS_STATE = range(2)

# category of themes
FOOD = "food"
NEWS = "news"
SHOPPING = "shopping"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts a subscription between the user and the bot.

    Sends back a list of themes for the subscriber to register.

    """
    subscriber_service = SubscriberService()

    user = update.message.from_user
    telegram_username = user["username"]
    telegram_id = str(user["id"])

    new_subscriber = Subscriber(telegram_id=telegram_id, telegram_username=telegram_username)
    try:
        subscriber_already_exists = subscriber_service.check_subscriber_exists(id=telegram_id)

        if not subscriber_already_exists:
            subscriber_service.add_subscriber(new_subscriber)
    except Exception as err:
        error_logging_service.log_error(err)
        await update.message.reply_text("Sorry, something went wrong, please try again later")
        return

    await update.message.reply_text(
        f"Hi {telegram_username}! You may set your keywords for specific themes using /setkeywords command."
    )


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribes a user from receiving messages"""
    subscriber_service = SubscriberService()

    user = update.message.from_user
    telegram_id = str(user["id"])

    try:
        subscriber_exist = subscriber_service.check_subscriber_exists(id=telegram_id)
        if not subscriber_exist:
            await update.message.reply_text("Eh? I don't know you.")
            return

        subscriber_service.unsubscribe(subscriber_id=telegram_id)
        await update.message.reply_text("Yes master. This is the last time you'll hear from me.")
    except Exception as err:
        error_logging_service.log_error(err)
        await update.message.reply_text(f"Something went wrong, please try again later")


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribes a new user to the bot to start receiving messages. If a user had previously unsubscribed, it will re-subscribe the user"""
    subscriber_service = SubscriberService()

    user = update.message.from_user
    telegram_username = user["username"]
    telegram_id = str(user["id"])

    new_subscriber = Subscriber(telegram_id=telegram_id, telegram_username=telegram_username)

    try:
        subscriber_already_exists = subscriber_service.check_subscriber_exists(id=telegram_id)

        # subscriber already exist, re-subscribes the person instead
        if subscriber_already_exists:
            subscriber_service.subscribe(subscriber_id=telegram_id)
            await update.message.reply_text(
                f"I have re-enabled your subscription! You'll hear from me soon, master {telegram_username}"
            )
            return

        subscriber_service.add_subscriber(subscriber=new_subscriber)
        await update.message.reply_text(
            f"Greetings master {telegram_username}. Thank you for subscribing to Sift! Let's set up some subscription themes shall we?"
        )
    except Exception as err:
        error_logging_service.log_error(err)
        await update.message.reply_text(f"Something went wrong, please try again later")


async def set_keywords_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [
            InlineKeyboardButton("🍔 Food", callback_data=FOOD),
            InlineKeyboardButton("🗞️ News", callback_data=NEWS),
            InlineKeyboardButton("🛍️ Shopping", callback_data=SHOPPING),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"Please select a theme to update keywords: ", reply_markup=reply_markup)
    return THEME_STATE


async def handle_select_theme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    theme = str(query.data)
    context.user_data["selected_theme"] = theme
    await query.answer()
    await query.edit_message_text(
        f'Theme "{theme}" selected. Please provide comma-separated keywords to start monitoring. Type /cancel to end this conversation.'
    )
    return KEYWORDS_STATE


async def handle_update_theme_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    subscriber_service = SubscriberService()

    selected_theme = context.user_data.get("selected_theme", None)
    user = update.message.from_user
    telegram_id = str(user["id"])
    keywords = update.message.text

    try:
        keywords = clean_string(keywords)
        keywords = list(filter(None, keywords.split(",")))  # split into an array, remove empty keywords
        keywords = [keyword.strip() for keyword in keywords]  # remove trailing whitespaces
        keywords = list(filter(None, keywords))  # remove empty strings in list
        subscriber_service.update_subscriber_theme_keywords(
            subscriber_id=telegram_id, theme=selected_theme, new_keywords=keywords
        )
        newline_separated_keywords = get_newline_separated_strings(keywords)

        await update.message.reply_text(
            f'Keywords for theme "{selected_theme}" updated: \n{newline_separated_keywords}'
        )
    except Exception as err:
        error_logging_service.log_error(err)
        await update.message.reply_text("Something went wrong, please try again later")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text("Operation cancelled", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(telegram_bot_token).build()

    # handle different commands
    application.add_handler(CommandHandler("start", start))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("setkeywords", set_keywords_command)],
        states={
            THEME_STATE: [
                CallbackQueryHandler(handle_select_theme, pattern="^" + str(FOOD) + "$"),
                CallbackQueryHandler(handle_select_theme, pattern="^" + str(NEWS) + "$"),
                CallbackQueryHandler(handle_select_theme, pattern="^" + str(SHOPPING) + "$"),
            ],
            KEYWORDS_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_update_theme_keywords)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
