# Reviewed: January, 17
# ToDo:
#   - comment all


import requests
import json
from loguru import logger
import time


DEBUG_ENABLED = False
PARAMS_FILE = "params.json"


class auxiliary:
    def __init__(self, aux_logger = None) -> None:
        self.params = self.read_params()
        if aux_logger == None:
            if DEBUG_ENABLED:
                logger.add(self.params['aux_log'], level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            else:
                logger.add(self.params['aux_log'], level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            self.logger = logger
        else:
            self.logger = aux_logger
        # Result = 0 - false
        # Result = 1 - true
        # Result = 2 - suspicious
        self.result = {
            'result': 0,
            'text': "",
            'case': ""
        }

    # # # # # # # # Auxiliary section start # # # # # # # # # #
    @logger.catch
    def do_request(self, method, url, headers = None, params = None, data = None, auth = None, use_ssl = True):
        """
        A wrapper for requests lib to send our requests and handle requests and responses better.

        :type method: ``str``
        :param method: HTTP method for the request.

        :type url: ``str``
        :param url: The suffix of the URL (endpoint)

        :type headers: ``dict``
        :param headers: Request headers

        :type params: ``dict``
        :param params: The URL params to be passed.

        :type data: ``str``
        :param data: The body data of the request.

        :type auth: ``str``
        :param auth: Basic HTTP authentication

        :return: Returns the http request response json
        :rtype: ``dict``
        """

        try:
            response = requests.request(
                method,
                url,
                verify = bool(use_ssl),
                headers = headers,
                params = params,
                auth = auth,
                data = data
            )
        except (requests.ConnectionError,
                requests.HTTPError,
                requests.Timeout) as e:
            msg = f"# Error occure during the request: {str(e)}"
            self.logger.error(msg)
            return msg
        try:
            self.logger.debug(f"# Request result: {response}")
            res = json.loads(response.text)
            self.logger.debug(f"# Response text: {res}")
            return res
        except ValueError as exception:
            msg = f"# Failed to parse json object from response. Exception: {exception}"
            raise ValueError(msg)


    # Read parameters from file
    @logger.catch
    def read_params(self):
        with open(PARAMS_FILE, "r", encoding="UTF-8") as params_file:
            return json.loads(params_file.read())


    # Filter for differentiation of logs
    @logger.catch
    def make_filter(self, name):
        def filter(record):
            return record["extra"].get("name") == name
        return filter


    # Replacing Latin/Number/Other characters with Cyrillic
    @logger.catch
    def lat_to_cyr(self, text, dictionary):
        self.logger.debug(f"# Processing Latyn to Cyrillic conversion for: {text}")
        text = text.lower()
        for key in dictionary:
            for character in text:
                if character in dictionary[key]:
                    text = text.replace(character, key)
        self.logger.debug(f"# Text after characters replacement: {text}")
        return text
    # # # # # # # # Auxiliary section end # # # # # # # # # #


    # # # # # # # # Processing section start # # # # # # # # # #
    @logger.catch
    def process_longpoll_errors(self, vk_api, result):
        self.logger.debug(f"# Processing Longpoll error: {result}")
        if result['failed'] == 1:
            self.result['text'] = f"[VK WARNING] Event history is deprecated or lost. New TS provided: {result['ts']}"
            self.result['error'] = 0
            vk_api.lp_ts = result['ts']
        if result['failed'] == 2:
            self.result['text'] = "[VK WARNING] API Key is deprecated. Need to get new with 'groups.getLongPollServer'"
            self.result['error'] = 0
            vk_api.get_lp_server_params()
        if result['failed'] == 3:
            self.result['text'] = "[VK WARNING] Information is lost. Need to get new API Key and TS with 'groups.getLongPollServer'"
            self.result['error'] = 0
            vk_api.get_lp_server_params()
        if self.result['text'] == "":
            self.result['text'] = "[GENERAL ERROR] Something went wrong during VK request managing!"
            self.result['error'] = 1
        return self.result


    # Listen to VK Longpoll server and manage results
    @logger.catch
    def listen_longpoll(self, vk_api, main_log):
        # # Errors counter for warnings.
        # +1 if warning was received (e.g. API key deprecated)
        # reset if next request is OK
        errors_limit = self.params['VK']['errors_limit']
        wait_period = self.params['VK']['wait_period']
        main_log.debug("# Start to listen LongPoll API. Errors counter was resetted")
        longpoll = {
            'errors_counter': 0,
            'response': '',
            'response_type': '',
            'error': 0
        }
        response = vk_api.listen_longpoll()
        # If there is error in VK Longpoll response - process
        main_log.debug(f"# Longpoll API response: {response}")
        if 'Error' in response:
            longpoll['errors_counter'] += 1
            main_log.info(f"# Errors counter: {longpoll['errors_counter']}")
            logger.warning(f"# {response}")
            if longpoll['errors_counter'] == errors_limit:
                msg = "# Errors limit is over. Shut down."
                logger.error(msg)
                longpoll['response'] = msg
                longpoll['error'] = 1
                return longpoll
            time.sleep(wait_period)
            return longpoll
        if 'failed' in response:
            process_result = self.process_longpoll_errors(vk_api, response)
            # Result contains tuple: True/False, error message to log
            if process_result['error'] == 0:
                # In case of warning we count to ERRORS_LIMIT and then stop
                longpoll['errors_counter'] += 1
                main_log.debug(process_result['text'])
                main_log.debug(f"# Errors counter: {longpoll['errors_counter']}")
                if longpoll['errors_counter'] == errors_limit:
                    msg = "# Errors limit is over. Shut down."
                    logger.error(msg)
                    longpoll['response'] = msg
                    longpoll['error'] = 1
                    return longpoll
                time.sleep(wait_period)
                return longpoll
            else:
                msg = f"# Critical error. {process_result['text']}"
                logger.error(msg)
                longpoll['response'] = msg
                longpoll['error'] = 1
                return longpoll
        else:
            main_log.debug("# No failures in response. Errors counter was resetted")
            longpoll['errors_counter'] = 0
            if response['updates'] == []:
                main_log.debug("# Listening interval passed, nothing new. Proceeding...")
                return longpoll
            # Process response with message
            vk_api.lp_ts = response['ts']

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
    # # # # # # # # Processing section end # # # # # # # # # #
