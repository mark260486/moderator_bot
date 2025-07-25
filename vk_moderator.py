# -*- coding: utf-8 -*-
# Reviewed: July 26, 2025
from __future__ import annotations

import argparse
import asyncio

from loguru import logger
from notifiers.logging import NotificationHandler

from config.vk import VK_config
from config.tlg import Telegram
from vk.api.longpoll import Longpoll
from vk.processing import VK_processing


@logger.catch
async def main() -> None:
    # # # # Parsing args # # # #
    parser = argparse.ArgumentParser(
        prog="VK Moderator bot",
        description="This script can strictly moderate VK public's chats",
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
    parser.add_argument(
        "-s",
        "--send_msg",
        dest="send_msg_to_vk",
        action="store_true",
        help="Send Notification message to VK Chat about Message removal or error",
        default=False,
        required=False,
    )
    args = parser.parse_args()

    # # # # Logger settings # # # #
    # Need to remove default logger settings
    logger.remove()

    # Logging params
    main_log_file = VK_config.log_path
    if args.debug_enabled:
        logger.add(
            main_log_file,
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
            rotation="1 MB",
            retention=2,
        )
        logger.debug("# VK moderator will run in Debug mode.")
    else:
        logger.add(
            main_log_file,
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
            rotation="1 MB",
            retention=2,
        )
    main_log = logger.bind(name="main_log")

    # Telegram messages logging
    if args.send_msg_to_tlg:
        tg_params = {
            "token": Telegram.tlg_api.api_key,
            "chat_id": Telegram.tlg_api.log_chat_id,
        }
        tg_handler = NotificationHandler("telegram", defaults=tg_params)
        main_log.add(tg_handler, format="{message}", level="INFO")

    main_log.info("# VK Moderator bot is (re)starting...")

    # # # # Start VK longpoll # # # #
    vk_longpoll = await Longpoll.create()
    proc = await VK_processing.create(
        debug_enabled=args.debug_enabled,
        send_msg_to_vk=args.send_msg_to_vk,
    )

    if vk_longpoll and proc:
        errors_limit = VK_config.Longpoll.errors_limit
        errors = 0
        while True:
            # Listening
            longpoll_result = await vk_longpoll.process_longpoll_response()
            if longpoll_result:
                if longpoll_result["type"] != "":
                    response_type = longpoll_result["type"]
                    # Response type, like 'message' or 'comment' will call
                    # according function from Processing. Error will be processed.
                    if not response_type == "error" and not response_type == "pass":
                        function_to_call = getattr(proc, response_type)
                        await function_to_call(response=longpoll_result["text"])
                    elif response_type == "error":
                        errors += 1
                        await asyncio.sleep(VK_config.Longpoll.wait_period)
                        if errors >= errors_limit:
                            main_log.error("# Errors limit is over. Shutting down.")
                            return None
                    elif response_type == "pass":
                        pass
    else:
        main_log.error("# Cannot start VK Longpoll or Processing. Shutting down.")
        return None


if __name__ == "__main__":
    vk_loop = asyncio.get_event_loop()
    vk_loop.run_until_complete(main())
