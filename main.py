# Reviewed: January 10, 2024
# ToDo:
# - verify params from file;
# - process different attachments types - in progress. Repost and link are done.
# - Telegram interactivity:
#   - make button in Telegram to download bot logs. Button - done. Callback - no.
# - Repost processing:
#   - send to Tlg defanged repost text/link, and From section information
# - Important improvements:
#   - add chat ID of new message to log
#   - send to Telegram only Warnings and higher. Replace levels of according alerts
#   - change suspicious words check procedure, too many false cases (send warning to Tlg?)
# - Possible improvements:
#   - add flag to log for new message if there was attachment
#   - autorestart bot with params.json changes
#   - make tests about user kick (1. Message about kick - done; 2. Can kicked user return? - Yes, by admin invitation)
#   - ban for links, for example, and not ban for curses
#   - Create database for bad users
#     - implement limit to removed messages to get banned
#     - implement Telegram buttons to work with DB
#   - change logging to JSON
#   - all bots in one chat
#   - try to use regexes for different susp/curse words


from loguru import logger
from notifiers.logging import NotificationHandler

import vk_api_dev
import aux_dev
import processing_dev


DEBUG_ENABLED = False


@logger.catch
def main():
    aux = aux_dev.aux()
    params = aux.read_params()
    log_file = params['VK']['log_path']
    cases_log_file = params['VK']['cases_log_path']

    # Logging params
    if DEBUG_ENABLED:
        logger.add(log_file, level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB", filter = aux.make_filter("main_log"))
    else:
        logger.add(log_file, level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB", filter = aux.make_filter("main_log"))
    logger.add(cases_log_file, level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB", filter = aux.make_filter("cases_log"))

    main_log = logger.bind(name = "main_log")
    cases_log = logger.bind(name = "cases_log")

    # Telegram messages logging
    # tg_params = {
    #     'token': params['TLG']['VK_MOD']['key'],
    #     'chat_id': params['TLG']['VK_MOD']['chat_id']
    # }
    # tg_handler = NotificationHandler("telegram", defaults = tg_params)
    aux = aux_dev.aux(main_log)
    processing = processing_dev.processing(aux, main_log)

    # logger.add(tg_handler, format = "{message}", level = "INFO")
    main_log.info(f"# VK Moderator bot is (re)starting...")

    # Create VK API object
    vk = vk_api_dev.vk_api(aux, logger)

    # Get longpoll server parameters
    main_log.debug("# Get LongPoll server parameters to listen")
    result = vk.get_lp_server_params()
    if not isinstance(result, str):
        main_log.debug("# LongPoll server parameters were received")
        while True:
            main_log.debug("# Listening to LongPoll API...")
            # Listening
            longpoll_result = aux.listen_longpoll(vk, main_log)
            if longpoll_result['error'] == 1:
                main_log.info("# Bot has stopped")
                # In case of error - break glass
                break
            if longpoll_result['response_type'] != "":
                response_type = longpoll_result['response_type']
                # Response type, like 'message' or 'comment' will call according function from Filter
                function_to_call = getattr(processing, response_type)
                function_to_call(longpoll_result['response'], vk, main_log, cases_log)
    else:
        logger.error(f"# Get Longpoll server parameters error. {result}")


if __name__ == '__main__':
    main()
