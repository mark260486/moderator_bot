# Reviewed: May 02, 2024

import argparse
from telegram import Update
from telegram.ext import ChatMemberHandler, MessageHandler, Application, filters
from loguru import logger
from notifiers.logging import NotificationHandler
from tlg_processing import TLG_processing
from config import Telegram


@logger.catch
def main() -> None:
    """Start the bot."""
    # # # # Parsing args # # # #
    parser = argparse.ArgumentParser(
        prog = "Telegram Moderator bot",
        description = "This script can strictly moderate Telegram chats"
        )

    parser.add_argument("-d", "--debug", dest = "debug_enabled",
                        action = "store_true", default = False,
                        required = False)
    args = parser.parse_args()

    # # # # Logger settings # # # #
    # Need to remove default logger settings
    logger.remove()

    # Logging params
    if args.debug_enabled:
        logger.add(Telegram.log_path, level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB")
        logger.debug("# Telegram moderator will run in Debug mode.")
    else:
        logger.add(Telegram.log_path, level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB")

    # Telegram messages logging
    tg_params = {
        'token': Telegram.telegram_moderator.api_key,
        'chat_id': Telegram.telegram_moderator.log_chat_id
    }
    tg_handler = NotificationHandler("telegram", defaults = tg_params)
    logger.add(tg_handler, format = "{message}", level = "INFO")

    logger.info("Telegram moderator bot listener re/starting..")

    # # # # Start Telegram listener # # # #
    # Get TLG Processing class instance
    proc = TLG_processing(debug_enabled = args.debug_enabled)

    # Apply TLG token
    app = Application.builder().token( Telegram.telegram_moderator.api_key).build()

    # On non command i.e message - moderate message content
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, proc.moderate_message))
    app.add_handler(MessageHandler(filters.ATTACHMENT, proc.moderate_message))

    # Handle members joining/leaving chats.
    app.add_handler(ChatMemberHandler(proc.greet_chat_members, ChatMemberHandler.CHAT_MEMBER))

    # Run the bot until the user presses Ctrl-C
    app.run_polling(allowed_updates = Update.ALL_TYPES)


if __name__ == "__main__":
    main()
