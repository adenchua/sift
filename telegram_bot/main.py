import json
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
from utils.string_helper import clean_string, format_bullet_point_newline_separated_string

dotenv.load_dotenv()
telegram_bot_token = os.getenv("ENV_TG_BOT_TOKEN") or ""

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logging_service = LoggingService()

THEME_STATE, KEYWORDS_STATE = range(2)

# category of themes
FOOD = "food"
NEWS = "news"
SHOPPING = "shopping"

# for internal logging
MODULE = "TELEGRAM-BOT"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts a subscription between the user and the bot.

    Sends back a list of themes for the subscriber to register.

    """
    subscriber_service = SubscriberService()

    user = update.message.from_user
    telegram_username = user["username"]
    telegram_id = str(user["id"])
    user_dict = {"id": telegram_id, "username": telegram_username}
    logging_service.log_info(message=f"Initiated conversation with the bot: {json.dumps(user_dict)}")

    new_subscriber = Subscriber(telegram_id=telegram_id, telegram_username=telegram_username)
    try:
        subscriber_already_exists = subscriber_service.check_subscriber_exists(id=telegram_id)

        if not subscriber_already_exists:
            subscriber_service.add_subscriber(new_subscriber)
    except Exception as error:
        error_dict = {"id": telegram_id, "username": telegram_username, "error": str(error)}
        logging_service.log_error(
            message=f"Failed to start service: {json.dumps(error_dict)}",
            module=MODULE,
        )
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
    telegram_username = user["username"]
    user_dict = {
        "id": telegram_id,
        "username": telegram_username,
    }

    try:
        subscriber_exist = subscriber_service.check_subscriber_exists(id=telegram_id)
        if not subscriber_exist:
            logging_service.log_info(
                message=f"Tried to unsubscribed from the bot, but does not exist in the database: {json.dumps(user_dict)}",
                module=MODULE,
            )
            await update.message.reply_text("You are not subscribed in the first place.")
            return

        subscriber_service.unsubscribe(subscriber_id=telegram_id)
        logging_service.log_info(message=f"Unsubscribed from the bot: {json.dumps(user_dict)}", module=MODULE)
        await update.message.reply_text("Yes master. This is the last time you'll hear from me.")
    except Exception as error:
        error_dict = {"username": telegram_username, "id": telegram_id, "error": str(error)}
        logging_service.log_error(
            message=f"Unsubscribe error: {json.dumps(error_dict)}",
            module=MODULE,
        )
        await update.message.reply_text(f"Something went wrong, please try again later")


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribes a new user to the bot to start receiving messages. If a user had previously unsubscribed, it will re-subscribe the user"""
    subscriber_service = SubscriberService()

    user = update.message.from_user
    telegram_username = user["username"]
    telegram_id = str(user["id"])
    user_dict = {"username": telegram_username, "id": telegram_id}

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
        logging_service.log_info(message=f"Subscribed to the bot: {json.dumps(user_dict)}", module=MODULE)
        await update.message.reply_text(
            f"Greetings master {telegram_username}. Thank you for subscribing to Sift! Let's set up some subscription themes with /setkeywords command"
        )
    except Exception as error:
        error_dict = {**user_dict, "error": str(error)}
        logging_service.log_error(
            message=f"Subscribe error: {json.dumps(error_dict)}",
            module=MODULE,
        )
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
    try:
        subscriber_service = SubscriberService()
        query = update.callback_query
        theme = str(query.data)
        telegram_user_id = str(query.from_user["id"])
        context.user_data["selected_theme"] = theme
        subscribed_theme = subscriber_service.get_subscriber_theme(
            telegram_user_id, theme
        )  # is None when no keywords are selected for that theme

        main_prompt = f'Theme "{theme}" selected. Please provide comma-separated keywords to start monitoring. Type /cancel to end this conversation.'

        # users have previously set keywords for that theme. Display the list to user
        if subscribed_theme is not None:
            subscribed_theme_keywords = subscribed_theme["keywords"]
            previous_selections_display_text = ", ".join(subscribed_theme_keywords)
            keywords_list_prompt = f"The current keywords set are: \n\n{previous_selections_display_text}"
            main_prompt = (
                f"{main_prompt}\n\n{keywords_list_prompt}"  # update main prompt to include previous selections
            )

        await query.edit_message_text(main_prompt)
        return KEYWORDS_STATE

    except Exception as error:
        logging_service.log_error(f"Handle select theme error: {str(error)}", module=MODULE)
        await update.callback_query.edit_message_text("Something went wrong, please try again later")


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
        newline_separated_keywords = format_bullet_point_newline_separated_string(keywords)

        await update.message.reply_text(
            f'Keywords for theme "{selected_theme}" updated: \n\n{newline_separated_keywords}'
        )
    except Exception as error:
        error_dict = {
            "id": telegram_id,
            "theme": selected_theme,
            "keywords": update.message.text,
            "error": str(error),
        }
        logging_service.log_error(
            message=f"Update theme keywords failed: {json.dumps(error_dict)}",
            module=MODULE,
        )
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
