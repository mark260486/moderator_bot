# Reviewed: May 02, 2024

from telegram import (Update)
from telegram.ext import (ChatMemberHandler, MessageHandler, Application, filters)
from loguru import logger
from notifiers.logging import NotificationHandler
import auxiliary
from tlg_processing import tlg_processing


CONFIG_FILE = "/home/mark/moderator_bot/config.json"
DEBUG_ENABLED = True


@logger.catch
def main() -> None:
    """Start the bot."""
    aux = auxiliary.auxiliary(debug_enabled = DEBUG_ENABLED, config_file = CONFIG_FILE)
    params = aux.read_config()
    main_log_file = params['TLG']['log_path']

    # Need to remove default logger settings
    logger.remove()

    # Logging params
    if DEBUG_ENABLED:
        logger.add(main_log_file, level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB")
    else:
        logger.add(main_log_file, level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB")

    # Telegram messages logging
    tg_params = {
        'token': params['TLG']['TLG_MOD']['key'],
        'chat_id': params['TLG']['TLG_MOD']['log_chat_id']
    }
    tg_handler = NotificationHandler("telegram", defaults = tg_params)
    logger.add(tg_handler, format = "{message}", level = "INFO")

    logger.info("Telegram moderator bot listener re/starting..")

    # Get TLG Processing class instance
    proc = tlg_processing(aux, debug_enabled = DEBUG_ENABLED)

    # Apply TLG token
    app = Application.builder().token(params['TLG']['TLG_MOD']['key']).build()

    # On non command i.e message - moderate message content
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, proc.moderate_message))
    app.add_handler(MessageHandler(filters.ATTACHMENT, proc.moderate_message))

    # Handle members joining/leaving chats.
    app.add_handler(ChatMemberHandler(proc.greet_chat_members, ChatMemberHandler.CHAT_MEMBER))

    # Run the bot until the user presses Ctrl-C
    app.run_polling(allowed_updates = Update.ALL_TYPES)


if __name__ == "__main__":
    main()
