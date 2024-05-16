# -*- coding: utf-8 -*-
# Reviewed: May 15, 2024
from __future__ import annotations

import argparse
import asyncio

from loguru import logger
from notifiers.logging import NotificationHandler
from telegram import Update
from telegram.ext import (
    Application,
    ChatMemberHandler,
    MessageHandler,
    filters,
)

from config import Telegram
from tlg_processing import TLG_processing


@logger.catch
async def main(loop) -> None:
    """Start the bot."""
    # # # # Parsing args # # # #
    parser = argparse.ArgumentParser(
        prog="Telegram Moderator bot",
        description="This script can strictly moderate Telegram chats",
    )

    parser.add_argument(
        "-d",
        "--debug",
        dest="debug_enabled",
        action="store_true",
        default=False,
        required=False,
    )
    parser.add_argument(
        "-t",
        "--tlg",
        dest="send_msg_to_tlg",
        action="store_true",
        help="Send Notification message to moderator Telegram Chat",
        default=False,
        required=False,
    )
    args = parser.parse_args()

    # # # # Logger settings # # # #
    # Need to remove default logger settings
    logger.remove()

    # Logging params
    if args.debug_enabled:
        logger.add(
            Telegram.log_path,
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
            rotation="10 MB",
        )
        logger.debug("# Telegram moderator will run in Debug mode.")
    else:
        logger.add(
            Telegram.log_path,
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
            rotation="10 MB",
        )

    # Telegram messages logging
    if args.send_msg_to_tlg:
        tg_params = {
            "token": Telegram.tlg_api.api_key,
            "chat_id": Telegram.tlg_api.log_chat_id,
        }
        tg_handler = NotificationHandler("telegram", defaults=tg_params)
        logger.add(tg_handler, format="{message}", level="INFO")

    logger.info("Telegram moderator bot listener re/starting..")

    # # # # Start Telegram listener # # # #
    # Get TLG Processing class instance
    proc = await TLG_processing.create(debug_enabled=args.debug_enabled)

    # Apply TLG token
    app = Application.builder().token(Telegram.tlg_api.api_key).build()

    # On non command i.e message - moderate message content
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, proc.moderate_message),
    )
    app.add_handler(MessageHandler(filters.ATTACHMENT, proc.moderate_message))

    # Handle members joining/leaving chats.
    app.add_handler(
        ChatMemberHandler(
            proc.greet_chat_members,
            ChatMemberHandler.CHAT_MEMBER,
        ),
    )

    # Run the bot until the user presses Ctrl-C
    app.run_polling(allowed_updates=Update.ALL_TYPES)
    loop.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main(loop))

    try:
        loop.run_forever()
    finally:
        loop.close()
