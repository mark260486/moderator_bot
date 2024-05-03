# Reviewed: May 03, 2024

import time
from loguru import logger as longpoll_log
from loguru import logger
from vk_api import VK_API, Groups
from config import Logs, VK


class Longpoll:
    def __init__(self, vk_api: VK_API, longpoll_log: logger = longpoll_log, debug_enabled: bool = False, # type: ignore
                 use_ssl: bool = True) -> None:
        """
        Longpoll class init

        :type longpoll_log: ``logger``
        :param longpoll_log: Logger instance.

        :type debug_enabled: ``bool``
        :param debug_enabled: Boolean to switch on and off debugging. False by default.

        :type use_ssl: ``bool``
        :param use_ssl: Boolean to switch on and off SSL requests. True by default.

        :type config_file: ``str``
        :param config_file: Path to the config file. 'config.json' by default.

        :return: Returns the class instance.
        """

        self.use_ssl = use_ssl
        self.vk = vk_api
        self.vk_groups = Groups()

        if longpoll_log == None:
            if debug_enabled:
                longpoll_log.add(Logs.longpoll_log, level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
                longpoll_log.debug("# Longpoll class will run in Debug mode.")
            else:
                longpoll_log.add(Logs.longpoll_log, level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
        else:
            self.longpoll_log = longpoll_log
        # Result = 0 - false
        # Result = 1 - true
        # Result = 2 - suspicious
        self.result = {
            'result': 0,
            'text': "",
            'case': ""
        }


    @longpoll_log.catch
    def process_longpoll_errors(self, result: dict) -> dict:
        """
        longpolliliary class method to process VK LongPoll server response.

        :type vk_api: ``VK_API``
        :param vk_api: VK API class instance.

        :type result: ``dict``
        :param result: Dictionary with VK LongPoll request results.

        :return: Returns the result of processing.
        :rtype: ``dict``
        """

        self.longpoll_log.debug(f"# Processing Longpoll error: {result}")
        if result['failed'] == 1:
            self.result['text'] = f"[VK WARNING] Event history is deprecated or lost. New TS provided: {result['ts']}"
            self.result['error'] = 0
            self.vk.lp_ts = result['ts']
        if result['failed'] == 2:
            self.result['text'] = "[VK WARNING] API Key is deprecated. Need to get new with 'groups.getLongPollServer'"
            self.result['error'] = 0
            self.vk_groups.getLongPollServer()
        if result['failed'] == 3:
            self.result['text'] = "[VK WARNING] Information is lost. Need to get new API Key and TS with 'groups.getLongPollServer'"
            self.result['error'] = 0
            self.vk_groups.getLongPollServer()
        if self.result['text'] == "":
            self.result['text'] = "[GENERAL ERROR] Something went wrong during VK request managing!"
            self.result['error'] = 1
        return self.result


    # Listen to VK Longpoll server and manage results
    @longpoll_log.catch
    def listen_longpoll(self) -> dict: # type: ignore
        """
        longpolliliary class method to listen VK LongPoll server response.

        :return: Returns the result of VK LongPoll request.
        :rtype: ``dict``
        """

        # # Errors counter for warnings.
        # +1 if warning was received (e.g. API key deprecated)
        # reset if next request is OK
        errors_limit = VK.errors_limit
        wait_period = VK.wait_period
        longpoll_log.debug("# Start to listen LongPoll API. Errors counter was resetted")
        longpoll = {
            'errors_counter': 0,
            'response': '',
            'response_type': '',
            'error': 0
        }
        response = self.vk.listen_longpoll()
        # If there is error in VK Longpoll response - process
        longpoll_log.debug(f"# Longpoll API response: {response}")
        if 'Error' in response:
            longpoll['errors_counter'] += 1
            longpoll_log.info(f"# Errors counter: {longpoll['errors_counter']}")
            longpoll_log.warning(f"# {response}")
            if longpoll['errors_counter'] == errors_limit:
                msg = "# Errors limit is over. Shut down."
                longpoll_log.error(msg)
                longpoll['response'] = msg
                longpoll['error'] = 1
                return longpoll
            time.sleep(wait_period)
            return longpoll
        if 'failed' in response:
            process_result = self.process_longpoll_errors(response)
            # Result contains tuple: True/False, error message to log
            if process_result['error'] == 0:
                # In case of warning we count to ERRORS_LIMIT and then stop
                longpoll['errors_counter'] += 1
                longpoll_log.debug(process_result['text'])
                longpoll_log.debug(f"# Errors counter: {longpoll['errors_counter']}")
                if longpoll['errors_counter'] == errors_limit:
                    msg = "# Errors limit is over. Shut down."
                    longpoll_log.error(msg)
                    longpoll['response'] = msg
                    longpoll['error'] = 1
                    return longpoll
                time.sleep(wait_period)
                return longpoll
            else:
                msg = f"# Critical error. {process_result['text']}"
                longpoll_log.error(msg)
                longpoll['response'] = msg
                longpoll['error'] = 1
                return longpoll
        else:
            longpoll_log.debug("# No failures in response. Errors counter was resetted")
            longpoll['errors_counter'] = 0
            if response['updates'] == []:
                longpoll_log.debug("# Listening interval passed, nothing new. Proceeding...")
                return longpoll
            # Process response with message
            self.vk.lp_ts = response['ts']

            # If this is new/edited comment
            if response['updates'][0]['type'] == "wall_reply_new" or \
            response['updates'][0]['type'] == "wall_reply_edit" or \
            response['updates'][0]['type'] == "photo_comment_new" or \
            response['updates'][0]['type'] == "photo_comment_edit":
                longpoll['response'] = response
                longpoll['response_type'] = "comment"
                return longpoll

            # If this is new message
            if response['updates'][0]['type'] == "message_new":
                longpoll['response'] = response
                longpoll['response_type'] = "message"
                return longpoll
            return longpoll
