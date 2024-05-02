# Reviewed: May 02, 2024

import argparse
from loguru import logger
from notifiers.logging import NotificationHandler
from vk_api import VK_API, Groups
from longpoll import Longpoll
from vk_processing import VK_processing
from config import VK, Telegram


@logger.catch
def main() -> None:
    # # # # Parsing args # # # #
    parser = argparse.ArgumentParser(
        prog = "VK Moderator bot",
        description = "This script can strictly moderate VK public's chats"
        )

    parser.add_argument("-d", "--debug", dest = "debug_enabled", action = "store_true",
                        default = False,
                        required = False)
    parser.add_argument("-s", "--send_msg",
                        dest = "send_msg_to_vk",
                        action = "store_true",
                        help = "Send Notification message to VK Chat about Message removal or error",
                        default = False,
                        required = False)
    args = parser.parse_args()

    # # # # Logger settings # # # #
    # Need to remove default logger settings
    logger.remove()

    # Logging params
    main_log_file = VK.log_path
    if args.debug_enabled:
        logger.add(main_log_file, level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB")
        logger.debug("# VK moderator will run in Debug mode.")
    else:
        logger.add(main_log_file, level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB")
    # Telegram messages logging
    tg_params = {
        'token': Telegram.vk_moderator.api_key,
        'chat_id': Telegram.vk_moderator.chat_id
    }
    tg_handler = NotificationHandler("telegram", defaults = tg_params)
    main_log = logger.bind(name = "main_log")
    main_log.add(tg_handler, format = "{message}", level = "INFO")
    main_log.info(f"# VK Moderator bot is (re)starting...")

    # # # # Start VK longpoll # # # #
    vk = VK_API(debug_enabled = args.debug_enabled)
    longpoll = Longpoll(vk, debug_enabled = args.debug_enabled)
    proc = VK_processing(debug_enabled = args.debug_enabled, send_msg_to_vk = args.send_msg_to_vk)

    # Get longpoll server parameters
    main_log.debug("# Get LongPoll server parameters to listen")
    result = Groups.getLongPollServer(vk)
    if result['error'] != 1:
        main_log.debug("# LongPoll server parameters were received")
        while True:
            # Listening
            longpoll_result = longpoll.listen_longpoll()
            if longpoll_result['error'] == 1:
                main_log.info("# Bot has stopped")
                # In case of error - break glass
                break
            if longpoll_result['response_type'] != "":
                response_type = longpoll_result['response_type']
                # Response type, like 'message' or 'comment' will call according function from Processing
                function_to_call = getattr(proc, response_type)
                function_to_call(response = longpoll_result['response'])
    else:
        main_log.error(f"# Get Longpoll server parameters error. {result['text']}")


if __name__ == '__main__':
    main()
