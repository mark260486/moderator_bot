# Reviewed: April 03, 2024


import random
from loguru import logger
from datetime import datetime, timedelta
import auxiliary


class vk_api:
    def __init__(self, aux: auxiliary, vk_logger: logger, debug_enabled: bool = False) -> None:
        """
        VK API class init

        :type aux: ``auxiliary``
        :param aux: Auxiliary class instance.

        :type vk_logger: ``logger``
        :param vk_logger: Logger instance.

        :type debug_enabled: ``bool``
        :param debug_enabled: Boolean to switch on and off debugging. False by default.

        :return: Returns the class instance.
        """

        self.params = aux.read_params()
        self.use_ssl = self.params['VK']['use_ssl']
        self.lp_key = ""
        self.lp_ts = 0
        self.lp_server = ""
        self.lp_wait = self.params['VK']['VK_LP']['wait']
        self.aux = aux
        self.vk_api_url = self.params['VK']['VK_API']['url']
        self.result = {
            'text': '',
            'error': 0
        }
        if vk_logger == None:
            logger.remove()
            if debug_enabled:
                logger.add(self.params['VK']['log_path'], level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            else:
                logger.add(self.params['VK']['log_path'], level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            self.logger = logger
        else:
            self.logger = vk_logger


    @logger.catch
    def reset_result(self) -> None:
        """
        VK API class method to reset reques results.
        """

        self.result = {
            'text': '',
            'error': 0
        }


    # GET request to VK LongPoll API to listen for messages
    @logger.catch
    def listen_longpoll(self) -> dict:
        """
        VK API class method to listen VK LongPoll response.

        :return: Returns the request result.
        :rtype: ``dict``
        """

        # Form request params
        payload = {
            'act': 'a_check',
            'key': self.lp_key,
            'ts': self.lp_ts,
            'wait': self.lp_wait
        }

        response = self.aux.do_request('GET', self.lp_server, params = payload, use_ssl = self.use_ssl)
        return response


    @logger.catch
    def get_user(self, user_id: int) -> dict:
        """
        VK API class method to get user's data like name.
        https://dev.vk.com/ru/method/users.get

        :type user_id: ``int``
        :param user_id: User ID.

        :return: Returns the request result.
        :rtype: ``dict``
        """

        self.reset_result()
        vk_method = "users.get"
        vk_api_url = f"{self.vk_api_url}{vk_method}"
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


    @logger.catch
    def is_group_member(self, user_id: int, group_id: int) -> dict:
        """
        VK API class method to find if user is in Group.
        https://dev.vk.com/ru/method/groups.isMember

        :type user_id: ``int``
        :param user_id: User ID.

        :type group_id: ``int``
        :param group_id: Group ID.

        :return: Returns the request result.
        :rtype: ``dict``
        """

        self.reset_result()
        vk_method = "groups.isMember"
        vk_api_url = f"{self.vk_api_url}{vk_method}"
        payload = {
            'user_id': user_id,
            'group_id': group_id,
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
        self.result['text'] = str(response['response'])
        return self.result


    @logger.catch
    def send_message(self, text: str, group_id: int, peer_id: int) -> dict:
        """
        VK API class method to send message.
        https://dev.vk.com/ru/method/messages.send

        :type text: ``str``
        :param text: Text to send.

        :type group_id: ``int``
        :param group_id: Public ID to message as administrator.

        :type peer_id: ``int``
        :param peer_id: Chat ID.

        :return: Returns the request result.
        :rtype: ``dict``
        """

        self.reset_result()
        vk_method = "messages.send"
        vk_api_url = f"{self.vk_api_url}{vk_method}"
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


    @logger.catch
    def search_messages(self, group_id: int, peer_id: int, count: int) -> dict:
        """
        VK API class method to send message.
        https://dev.vk.com/ru/method/messages.search

        :type group_id: ``int``
        :param group_id: Public ID to message as administrator.

        :type peer_id: ``int``
        :param peer_id: Chat ID.

        :type count: ``int``
        :param count: Count of messages to return

        :return: Returns the request result.
        :rtype: ``dict``
        """

        # We will need current date in DDMMYYYY format to search all before this date.
        # There will be tomorrow to get latest messages.
        tomorrow = datetime.strftime(datetime.today() + timedelta(days = 1), '%d%m%Y')

        self.reset_result()
        vk_method = "messages.search"
        vk_api_url = f"{self.vk_api_url}{vk_method}"
        payload = {
            'group_id': group_id,
            'peer_id': peer_id,
            'count': count,
            'date': tomorrow,
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
        self.result['text'] = response['response']
        return self.result



    @logger.catch
    def delete_message(self, group_id: int, cm_id: int, peer_id: int) -> dict:
        """
        VK API class method to delete message.
        https://dev.vk.com/ru/method/messages.delete

        :type group_id: ``int``
        :param group_id: Public ID.

        :type cm_id: ``int``
        :param cm_id: Message ID.

        :type peer_id: ``int``
        :param peer_id: Chat ID.

        :return: Returns the request result.
        :rtype: ``dict``
        """

        self.reset_result()
        vk_method = "messages.delete"
        vk_api_url = f"{self.vk_api_url}{vk_method}"
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



    @logger.catch
    def get_lp_server_params(self) -> dict:
        """
        VK API class method to get LongPoll server parameters.
        https://dev.vk.com/ru/method/groups.getLongPollServer

        :return: Returns the request result.
        :rtype: ``dict``
        """

        self.reset_result()
        vk_method = "groups.getLongPollServer"
        vk_api_url = f"{self.vk_api_url}{vk_method}"
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
