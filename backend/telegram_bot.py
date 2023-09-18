from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)
import os
import dotenv

from services.subscriber_service import (
    SubscriberService,
    Subscriber,
)

dotenv.load_dotenv()
telegram_bot_token = os.getenv("ENV_TG_BOT_TOKEN") or ""

THEME, KEYWORDS = range(2)

FOOD, NEWS, SHOPPING = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts a subscription between the user and the bot.

    Sends back a list of themes for the subscriber to register.

    """
    subscriber_service = SubscriberService()

    user = update.message.from_user
    subscriber_username = user["username"]
    subscriber_telegram_id = str(user["id"])

    new_subscriber = Subscriber(id=subscriber_username, telegram_id=subscriber_telegram_id)
    try:
        subscriber_already_exists = subscriber_service.check_subscriber_exists(subscriber_id=subscriber_username)

        if not subscriber_already_exists:
            subscriber_service.add_subscriber(new_subscriber)
    except:
        await update.message.reply_text("Sorry, something went wrong, please try again later")
        return

    await update.message.reply_text(
        f"Hi {subscriber_username}! You may set your keywords for specific themes using /setkeywords command."
    )


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
    except:
        await update.message.reply_text(f"Something went wrong, please try again later")


async def set_keywords_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["Food", "News", "Shopping"]]

    await update.message.reply_text(
        f"Please choose a theme to update: ",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Select theme to update keywords"
        ),
    )
    return THEME


async def handle_select_theme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    theme = update.message.text
    await update.message.reply_text(
        f'You have selected "{theme}". Please provide comma-separated keywords to start monitoring.'
    )
    context.user_data["selected_theme"] = theme
    return KEYWORDS


async def handle_update_theme_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    selected_theme = context.user_data.get("selected_theme", None)

    await update.message.reply_text("Thank you! I hope we can talk again some day.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    await update.message.reply_text("If you change your mind, just let me know!", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main() -> None:
    """Start the bot."""
    print("initializing bot...")
    application = Application.builder().token(telegram_bot_token).build()

    # handle different commands
    application.add_handler(CommandHandler("start", start))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("setkeywords", set_keywords_command)],
        states={
            THEME: [MessageHandler(filters.Regex("^(Food|News|Shopping)$"), handle_select_theme)],
            KEYWORDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_update_theme_keywords)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))

    print("telegram bot listening...")
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
