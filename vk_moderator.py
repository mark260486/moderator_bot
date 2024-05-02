# Reviewed: May 02, 2024

from loguru import logger
from notifiers.logging import NotificationHandler

import vk_api
import auxiliary
import vk_processing


# Move these to arguments
DEBUG_ENABLED = True
SEND_MSG_TO_VK = False
CONFIG_FILE = "/home/mark/moderator_bot/config.json"


@logger.catch
def main() -> None:
    aux = auxiliary.auxiliary(debug_enabled = DEBUG_ENABLED, config_file = CONFIG_FILE)
    params = aux.read_config()
    main_log_file = params['VK']['log_path']
    aux = None

    # Need to remove default logger settings
    logger.remove()

    # Telegram messages logging
    tg_params = {
        'token': params['TLG']['VK_MOD']['key'],
        'chat_id': params['TLG']['VK_MOD']['chat_id']
    }
    tg_handler = NotificationHandler("telegram", defaults = tg_params)
    logger.add(tg_handler, format = "{message}", level = "INFO")

    # Logging params
    main_log = logger.bind(name = "main_log")
    if DEBUG_ENABLED:
        logger.add(main_log_file, level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB")
    else:
        logger.add(main_log_file, level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB")

    aux = auxiliary.auxiliary(main_log, debug_enabled = DEBUG_ENABLED, config_file = CONFIG_FILE)
    proc = vk_processing.vk_processing(aux, main_log, DEBUG_ENABLED, SEND_MSG_TO_VK)

    main_log.info(f"# VK Moderator bot is (re)starting...")

    # Create VK API object
    vk = vk_api.vk_api(aux, vk_logger = main_log)

    # Get longpoll server parameters
    main_log.debug("# Get LongPoll server parameters to listen")
    result = vk.get_lp_server_params()
    if not isinstance(result, str):
        main_log.debug("# LongPoll server parameters were received")
        while True:
            main_log.debug("# Listening to LongPoll API...")
            # Listening
            longpoll_result = aux.listen_longpoll(vk_api = vk, main_log = main_log)
            if longpoll_result['error'] == 1:
                main_log.info("# Bot has stopped")
                # In case of error - break glass
                break
            if longpoll_result['response_type'] != "":
                response_type = longpoll_result['response_type']
                # Response type, like 'message' or 'comment' will call according function from Processing
                function_to_call = getattr(proc, response_type)
                function_to_call(
                    response = longpoll_result['response'],
                    vk_api = vk, 
                    main_log = main_log
                    )
    else:
        logger.error(f"# Get Longpoll server parameters error. {result}")


if __name__ == '__main__':
    main()
