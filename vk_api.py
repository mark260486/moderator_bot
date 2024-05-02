# Reviewed: May 02, 2024

import random
import requests
import json
from loguru import logger as vk_api_log
from loguru import logger
from datetime import datetime, timedelta
from config import VK


class VK_API:
    def __init__(self, vk_api_log: logger = vk_api_log, debug_enabled: bool = False, # type: ignore
                 use_ssl: bool = True) -> None:
        """
        VK API class init

        :type vk_api_log: ``logger``
        :param vk_api_log: Logger instance.

        :type debug_enabled: ``bool``
        :param debug_enabled: Boolean to switch on and off debugging. False by default.

        :return: Returns the class instance.
        """

        self.use_ssl = use_ssl
        self.lp_key = ""
        self.lp_ts = 0
        self.lp_server = ""
        self.lp_wait = VK.vk_longpoll.wait
        self.vk_api_url = VK.vk_api.api_url
        self.result = {
            'text': '',
            'error': 0
        }
        if vk_api_log == None:
            if debug_enabled:
                vk_api_log.add(VK.log_path, level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
                vk_api_log.debug("# VK API class will run in Debug mode.")
            else:
                vk_api_log.add(VK.log_path, level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            self.vk_api_log = vk_api_log
        else:
            self.vk_api_log = vk_api_log


    @vk_api_log.catch
    def do_request(self, method: str, url: str, headers: dict = None, params: dict = None,
                   data: dict = None, auth: str = None, use_ssl: bool = True) -> dict:
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

        self.vk_api_log.debug(f"============== Do request ================")
        self.vk_api_log.debug(f"# Requesting for: {url}")
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
            self.vk_api_log.error(msg)
            return msg
        try:
            self.vk_api_log.debug(f"# Request result: {response}")
            res = json.loads(response.text)
            self.vk_api_log.debug(f"# Response text: {res}")
            return res
        except ValueError as exception:
            msg = f"# Failed to parse json object from response. Exception: {exception}"
            raise ValueError(msg)


    @vk_api_log.catch
    def reset_result(self) -> None:
        """
        VK API class method to reset reques results.
        """

        self.result = {
            'text': '',
            'error': 0
        }


    # GET request to VK LongPoll API to listen for messages
    @vk_api_log.catch
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

        response = self.do_request('GET', self.lp_server, params = payload, use_ssl = self.use_ssl)
        return response


class Users(VK_API):
    def __init__(self):
        """
        VK API Users subclass init

        :return: Returns the class instance.
        """
        super().__init__()


    @vk_api_log.catch
    def get(self, user_id: int) -> dict:
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
            'v': VK.vk_api.version
        }
        headers = {
            'Authorization': f"Bearer {VK.vk_api.api_key}"
        }
        response = self.do_request("GET", vk_api_url, headers = headers, params = payload, use_ssl = self.use_ssl)
        if response['response'] == []:
            self.result['text'] = VK.public_name
            return self.result
        if 'error' in response['response'][0].keys():
            msg = f"[VK ERROR] Response: error code - {response['response'][0]['error']['code']}, description: {response['response'][0]['error']['description']}"
            vk_api_log.error(msg)
            self.result['text'] = msg
            self.result['error'] = 1
            return self.result
        self.result['text'] = f"{response['response'][0]['first_name']} {response['response'][0]['last_name']}"
        return self.result


class Groups(VK_API):
    def __init__(self):
        """
        VK API Groups subclass init

        :return: Returns the class instance.
        """
        super().__init__()


    @vk_api_log.catch
    def isMember(self, user_id: int, group_id: int) -> dict:
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
            'v': VK.vk_api.version
        }
        headers = {
            'Authorization': f"Bearer {VK.vk_api.api_key}"
        }

        response = self.do_request("GET", vk_api_url, headers = headers, params = payload, use_ssl = self.use_ssl)
        self.result['text'] = str(response['response'])
        return self.result


    @vk_api_log.catch
    def getLongPollServer(self) -> dict:
        """
        VK API class method to get LongPoll server parameters.
        https://dev.vk.com/ru/method/groups.getLongPollServer

        :return: Returns the request result.
        :rtype: ``dict``
        """

        self.reset_result()
        vk_method = "groups.getLongPollServer"
        vk_api_url = f"{self.vk_api_url}{vk_method}"
        vk_group_id = VK.vk_api.group_id
        vk_api_version =  VK.vk_api.version

        payload = {
            'group_id': vk_group_id,
            'v': vk_api_version
        }
        headers = {
            'Authorization': f"Bearer {VK.vk_api.api_key}"
        }

        response = self.do_request("GET", vk_api_url, headers = headers, params = payload, use_ssl = self.use_ssl)
        if 'error' in response.keys():
            try:
                msg = f"[VK ERROR] Response: error code - {response['error']['error_code']}, description: {response['error']['error_msg']}"
                self.result['text'] = msg
                self.result['error'] = 1
            except:
                self.result['text'] = "Cannot get neccessary keys from VK API response."
                self.result['error'] = 1
            return self.result
        self.lp_server, self.lp_key, self.lp_ts = response['response']['server'], response['response']['key'], response['response']['ts']
        self.result['text'] = "Longpoll server parameters were received"
        return self.result


class Messages(VK_API):
    def __init__(self):
        """
        VK API Messages subclass init

        :return: Returns the class instance.
        """
        super().__init__()


    @vk_api_log.catch
    def send(self, text: str, group_id: int, peer_id: int) -> dict:
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
            'v':  VK.vk_api.version
        }
        headers = {
            'Authorization': f"Bearer {VK.vk_api.api_key}"
        }

        response = self.do_request("GET", vk_api_url, headers = headers, params = payload, use_ssl = self.use_ssl)
        if 'error' in response['response'][0].keys():
            msg = f"[VK ERROR] Response: error code - {response['response'][0]['error']['code']}, description: {response['response'][0]['error']['description']}"
            vk_api_log.error(msg)
            self.result['text'] = msg
            self.result['error'] = 1
            return self.result
        self.result['text'] = "Message was sent"
        return self.result


    @vk_api_log.catch
    def search(self, group_id: int, peer_id: int, count: int) -> dict:
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
            'v':  VK.vk_api.version
        }
        headers = {
            'Authorization': f"Bearer {VK.vk_api.api_key}"
        }

        response = self.do_request("GET", vk_api_url, headers = headers, params = payload, use_ssl = self.use_ssl)
        if 'error' in response['response'].keys():
            msg = f"[VK ERROR] Response: error code - {response['response'][0]['error']['code']}, description: {response['response'][0]['error']['description']}"
            vk_api_log.error(msg)
            self.result['text'] = msg
            self.result['error'] = 1
            return self.result
        self.result['text'] = response['response']
        return self.result



    @vk_api_log.catch
    def delete(self, group_id: int, cm_id: int, peer_id: int) -> dict:
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
            'delete_for_all': VK.vk_api.delete_for_all,
            'v':  VK.vk_api.version
        }
        headers = {
            'Authorization': f"Bearer {VK.vk_api.api_key}"
        }

        response = self.do_request("GET", vk_api_url, headers = headers, params = payload, use_ssl = self.use_ssl)
        if 'error' in response['response'][0].keys():
            msg = f"[VK ERROR] Response: error code - {response['response'][0]['error']['code']}, description: {response['response'][0]['error']['description']}"
            vk_api_log.error(msg)
            self.result['text'] = msg
            self.result['error'] = 1
            return self.result
        self.result['text'] = "Message was deleted"
        return self.result
