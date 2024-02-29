# Reviewed: February 11, 2024


from loguru import logger
from notifiers.logging import NotificationHandler

import vk_api
import auxiliary
import processing


DEBUG_ENABLED = False


@logger.catch
def main() -> None:
    aux = auxiliary.auxiliary(debug_enabled = DEBUG_ENABLED)
    params = aux.read_params()
    main_log_file = params['VK']['log_path']
    cases_log_file = params['VK']['cases_log_path']

    # Telegram messages logging
    tg_params = {
        'token': params['TLG']['VK_MOD']['key'],
        'chat_id': params['TLG']['VK_MOD']['chat_id']
    }
    tg_handler = NotificationHandler("telegram", defaults = tg_params)
    logger.add(tg_handler, format = "{message}", level = "INFO", filter = lambda record: record["extra"].get("name") == "main_log")

    # Logging params
    main_log = logger.bind(name = "main_log")
    cases_log = logger.bind(name = "cases_log")
    if DEBUG_ENABLED:
        logger.add(main_log_file, level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB",
                   filter = lambda record: record["extra"].get("name") == "main_log")
    else:
        logger.add(main_log_file, level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB",
                   filter = lambda record: record["extra"].get("name") == "main_log")
    logger.add(cases_log_file, level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB",
                    filter = lambda record: record["extra"].get("name") == "cases_log")

    aux = auxiliary.auxiliary(main_log)
    proc = processing.processing(aux, main_log)

    # logger.add(tg_handler, format = "{message}", level = "INFO")
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
                    main_log = main_log,
                    cases_log = cases_log
                    )
    else:
        logger.error(f"# Get Longpoll server parameters error. {result}")


if __name__ == '__main__':
    main()
