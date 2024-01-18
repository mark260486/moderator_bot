# Reviewed: November 29, 2023

import random
from loguru import logger

DEBUG_ENABLED = False

class vk_api:

    def __init__(self, aux, vk_logger):
        self.params = aux.read_params()
        self.use_ssl = self.params['VK']['use_ssl']
        self.lp_key = ""
        self.lp_ts = 0
        self.lp_server = ""
        self.lp_wait = self.params['VK']['VK_LP']['wait']
        self.aux = aux
        self.result = {
            'text': '',
            'error': 0
        }
        if vk_logger == None:
            if DEBUG_ENABLED:
                logger.add(self.params['VK']['log_path'], level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            else:
                logger.add(self.params['VK']['log_path'], level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            self.logger = logger
        else:
            self.logger = vk_logger


    def reset_result(self):
        self.result = {
            'text': '',
            'error': 0
        }


    # GET request to VK LongPoll API to listen for messages
    def listen_longpoll(self):
        # Form request params
        payload = {
            'act': 'a_check',
            'key': self.lp_key,
            'ts': self.lp_ts,
            'wait': self.lp_wait
        }

        response = self.aux.do_request('GET', self.lp_server, params = payload, use_ssl = self.use_ssl)
        return response


    # Get user name from message
    def get_user(self, user_id):
        self.reset_result()
        vk_method = "users.get"
        vk_api_url = f"{self.params['VK']['VK_API']['url']}{vk_method}"
        payload = {
            'user_ids': user_id,
            'v': self.params['VK']['VK_API']['version']
        }
        headers = {
            'Authorization': f"Bearer {self.params['VK']['VK_API']['key']}"
        }
        response = self.aux.do_request("GET", vk_api_url, headers = headers, params = payload, use_ssl = self.use_ssl)
        if response['response'] == []:
            self.result['text'] = "Чернобыль и Припять"
            return self.result
        if 'error' in response:
            msg = f"[VK ERROR] Response: error code - {response['error']['error_code']}, description: {response['error']['error_msg']}"
            logger.error(msg)
            self.result['text'] = msg
            self.result['error'] = 1
            return self.result
        self.result['text'] = f"{response['response'][0]['first_name']} {response['response'][0]['last_name']}"
        return self.result


    def send_message(self, text, group_id, peer_id):
        self.reset_result()
        vk_method = "messages.send"
        vk_api_url = f"{self.params['VK']['VK_API']['url']}{vk_method}"
        payload = {
            'group_id': group_id,
            'peer_id': peer_id,
            'message': text,
            'random_id': random.randint(100, 100000),
            'v': self.params['VK']['VK_API']['version']
        }
        headers = {
            'Authorization': f"Bearer {self.params['VK']['VK_API']['key']}"
        }

        response = self.aux.do_request("GET", vk_api_url, headers = headers, params = payload, use_ssl = self.use_ssl)
        if 'error' in response:
            msg = f"[VK ERROR] Response: error code - {response['error']['error_code']}, description: {response['error']['error_msg']}"
            logger.error(msg)
            self.result['text'] = msg
            self.result['error'] = 1
            return self.result
        self.result['text'] = "Message was sent"
        return self.result


    def delete_message(self, group_id, cm_id, peer_id):
        self.reset_result()
        vk_method = "messages.delete"
        vk_api_url = f"{self.params['VK']['VK_API']['url']}{vk_method}"
        payload = {
            'group_id': group_id,
            'cmids': cm_id,
            'peer_id': peer_id,
            'delete_for_all': self.params['VK']['VK_API']['delete_for_all'],
            'v': self.params['VK']['VK_API']['version']
        }
        headers = {
            'Authorization': f"Bearer {self.params['VK']['VK_API']['key']}"
        }

        response = self.aux.do_request("GET", vk_api_url, headers = headers, params = payload, use_ssl = self.use_ssl)
        if 'error' in response:
            msg = f"[VK ERROR] Response: error code - {response['error']['error_code']}, description: {response['error']['error_msg']}"
            logger.error(msg)
            self.result['text'] = msg
            self.result['error'] = 1
            return self.result
        self.result['text'] = "Message was deleted"
        return self.result



    # Get Longpoll API server parameters as link, key and TS
    def get_lp_server_params(self):
        self.reset_result()
        vk_method = "groups.getLongPollServer"
        vk_api_url = f"{self.params['VK']['VK_API']['url']}{vk_method}"
        vk_group_id = self.params['VK']['VK_API']['group_id']
        vk_api_version = self.params['VK']['VK_API']['version']

        payload = {
            'group_id': vk_group_id,
            'v': vk_api_version
        }
        headers = {
            'Authorization': f"Bearer {self.params['VK']['VK_API']['key']}"
        }

        response = self.aux.do_request("GET", vk_api_url, headers = headers, params = payload, use_ssl = self.use_ssl)
        if 'error' in response:
            msg = f"[VK ERROR] Response: error code - {response['error']['error_code']}, description: {response['error']['error_msg']}"
            logger.error(msg)
            self.result['text'] = msg
            self.result['error'] = 1
            return self.result
        self.lp_server, self.lp_key, self.lp_ts = response['response']['server'], response['response']['key'], response['response']['ts']
        self.result['text'] = "Longpoll server parameters were received"
        return self.result
