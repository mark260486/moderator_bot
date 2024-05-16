# -*- coding: utf-8 -*-
# Reviewed: May 16, 2024
from __future__ import annotations

import asyncio
import json
import random
from datetime import datetime, timedelta

import requests
from loguru import logger
from loguru import logger as vk_api_log

from config import VK


class VK_API:
    # To avoid async __init__
    @classmethod
    async def create(
        cls,
        vk_api_log: logger = vk_api_log,  # type: ignore
        debug_enabled: bool = False,
    ) -> None:
        """
        VK API class init

        :type vk_api_log: ``logger``
        :param vk_api_log: Logger instance.

        :type debug_enabled: ``bool``
        :param debug_enabled: Boolean to switch on and off debugging. False by default.

        :return: Returns the class instance.
        """

        self = cls()
        self.result = {"text": "", "error": 0}

        if vk_api_log is None:
            if debug_enabled:
                vk_api_log.add(
                    VK.log_path,
                    level="DEBUG",
                    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
                )
                vk_api_log.debug("# VK API class will run in Debug mode.")
            else:
                vk_api_log.add(
                    VK.log_path,
                    level="INFO",
                    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
                )
            self.vk_api_log = vk_api_log
        else:
            self.vk_api_log = vk_api_log

    @vk_api_log.catch
    async def do_request(
        self,
        method: str,
        url: str,
        headers: dict = None,
        params: dict = None,
        data: dict = None,
        auth: str = None,
        use_ssl: bool = True,
    ) -> dict:
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

        vk_api_log.debug("============== Do request ================")
        vk_api_log.debug(f"# Requesting for: {url}")
        try:
            response = requests.request(
                method,
                url,
                verify=bool(use_ssl),
                headers=headers,
                params=params,
                auth=auth,
                data=data,
            )
        except (
            requests.ConnectionError,
            requests.HTTPError,
            requests.Timeout,
        ) as e:
            msg = f"# Error occure during the request: {str(e)}"
            vk_api_log.error(msg)
            return msg
        try:
            vk_api_log.debug(f"# Request result: {response}")
            res = json.loads(response.text)
            vk_api_log.debug(f"# Response text: {res}")
            return res
        except ValueError as exception:
            msg = f"# Failed to parse json object from response. Exception: {exception}"
            raise ValueError(msg)

    @vk_api_log.catch
    def reset_result(self) -> None:
        """
        VK API class method to reset request results.
        """

        self.result = {"text": "", "error": 0}


class Users(VK_API):
    # To avoid async __init__
    @classmethod
    async def create(cls, use_ssl: bool = True) -> None:
        """
        VK API Users subclass init

        :return: Returns the class instance.
        """
        self = cls()
        self.use_ssl = use_ssl
        super().__init__(self)
        return self

    @vk_api_log.catch
    async def get(self, user_id: int) -> dict:
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
        vk_api_url = f"{VK.vk_api.api_url}{vk_method}"
        payload = {"user_ids": user_id, "v": VK.vk_api.version}
        headers = {"Authorization": f"Bearer {VK.vk_api.api_key}"}
        response = await self.do_request(
            "GET",
            vk_api_url,
            headers=headers,
            params=payload,
            use_ssl=self.use_ssl,
        )
        if response["response"] == []:
            self.result["text"] = VK.public_name
            return self.result
        if "error" in response["response"][0].keys():
            msg = f"[VK ERROR] Response: error code - {response['response'][0]['error']['code']}, description: {response['response'][0]['error']['description']}"
            vk_api_log.error(msg)
            self.result["text"] = msg
            self.result["error"] = 1
            return self.result
        self.result["text"] = (
            f"{response['response'][0]['first_name']} {response['response'][0]['last_name']}"
        )
        return self.result


class Groups(VK_API):
    # To avoid async __init__
    @classmethod
    async def create(cls, use_ssl: bool = True) -> None:
        """
        VK API Groups subclass init

        :return: Returns the class instance.
        """
        self = cls()
        self.use_ssl = use_ssl
        VK.vk_api.api_url = VK.vk_api.api_url
        return self

    @vk_api_log.catch
    async def isMember(self, user_id: int, group_id: int) -> dict:
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
        vk_api_url = f"{VK.vk_api.api_url}{vk_method}"
        payload = {
            "user_id": user_id,
            "group_id": group_id,
            "v": VK.vk_api.version,
        }
        headers = {"Authorization": f"Bearer {VK.vk_api.api_key}"}

        response = await self.do_request(
            "GET",
            vk_api_url,
            headers=headers,
            params=payload,
            use_ssl=self.use_ssl,
        )
        self.result["text"] = str(response["response"])
        return self.result

    @vk_api_log.catch
    async def getLongPollServer(self) -> dict:
        """
        VK API class method to get LongPoll server parameters.
        https://dev.vk.com/ru/method/groups.getLongPollServer

        :return: Returns the request result.
        :rtype: ``dict``
        """

        self.reset_result()
        vk_method = "groups.getLongPollServer"
        vk_api_url = f"{VK.vk_api.api_url}{vk_method}"
        vk_group_id = VK.vk_api.group_id
        vk_api_version = VK.vk_api.version

        payload = {"group_id": vk_group_id, "v": vk_api_version}
        headers = {"Authorization": f"Bearer {VK.vk_api.api_key}"}

        response = await self.do_request(
            "GET",
            vk_api_url,
            headers=headers,
            params=payload,
            use_ssl=self.use_ssl,
        )
        if "error" in response.keys():
            try:
                msg = f"[VK ERROR] Response: error code - {response['error']['error_code']}, description: {response['error']['error_msg']}"
                self.result["text"] = msg
                self.result["error"] = 1
            except Exception:
                self.result["text"] = (
                    "Cannot get neccessary keys from VK API response."
                )
                self.result["error"] = 1
                raise
            return self.result
        self.lp_server = response["response"]["server"]
        self.lp_key = response["response"]["key"]
        self.lp_ts = response["response"]["ts"]
        self.result["text"] = "Longpoll server parameters were received"
        return self.result


class Messages(VK_API):
    # To avoid async __init__
    @classmethod
    async def create(cls, use_ssl: bool = True) -> None:
        """
        VK API Messages subclass init

        :return: Returns the class instance.
        """
        self = cls()
        self.use_ssl = use_ssl
        super().__init__(self)
        return self

    @vk_api_log.catch
    async def send(self, text: str, group_id: int, peer_id: int) -> dict:
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
        vk_api_url = f"{VK.vk_api.api_url}{vk_method}"
        payload = {
            "group_id": group_id,
            "peer_id": peer_id,
            "message": text,
            "random_id": random.randint(100, 100000),
            "v": VK.vk_api.version,
        }
        headers = {"Authorization": f"Bearer {VK.vk_api.api_key}"}

        response = await self.do_request(
            "GET",
            vk_api_url,
            headers=headers,
            params=payload,
            use_ssl=self.use_ssl,
        )
        if "error" in response["response"][0].keys():
            msg = f"[VK ERROR] Response: error code - {response['response'][0]['error']['code']}, description: {response['response'][0]['error']['description']}"
            vk_api_log.error(msg)
            self.result["text"] = msg
            self.result["error"] = 1
            return self.result
        self.result["text"] = "Message was sent"
        return self.result

    @vk_api_log.catch
    async def search(self, group_id: int, peer_id: int, count: int) -> dict:
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
        tomorrow = datetime.strftime(
            datetime.today() + timedelta(days=1),
            "%d%m%Y",
        )

        self.reset_result()
        vk_method = "messages.search"
        vk_api_url = f"{VK.vk_api.api_url}{vk_method}"
        payload = {
            "group_id": group_id,
            "peer_id": peer_id,
            "count": count,
            "date": tomorrow,
            "v": VK.vk_api.version,
        }
        headers = {"Authorization": f"Bearer {VK.vk_api.api_key}"}

        response = await self.do_request(
            "GET",
            vk_api_url,
            headers=headers,
            params=payload,
            use_ssl=self.use_ssl,
        )
        if "error" in response["response"].keys():
            msg = f"[VK ERROR] Response: error code - {response['response'][0]['error']['code']}, description: {response['response'][0]['error']['description']}"
            vk_api_log.error(msg)
            self.result["text"] = msg
            self.result["error"] = 1
            return self.result
        self.result["text"] = response["response"]
        return self.result

    @vk_api_log.catch
    async def delete(self, group_id: int, cm_id: int, peer_id: int) -> dict:
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
        vk_api_url = f"{VK.vk_api.api_url}{vk_method}"
        payload = {
            "group_id": group_id,
            "cmids": cm_id,
            "peer_id": peer_id,
            "delete_for_all": VK.vk_api.delete_for_all,
            "v": VK.vk_api.version,
        }
        headers = {"Authorization": f"Bearer {VK.vk_api.api_key}"}

        response = await self.do_request(
            "GET",
            vk_api_url,
            headers=headers,
            params=payload,
            use_ssl=self.use_ssl,
        )
        if "error" in response["response"][0].keys():
            msg = f"[VK ERROR] Response: error code - {response['response'][0]['error']['code']}, description: {response['response'][0]['error']['description']}"
            vk_api_log.error(msg)
            self.result["text"] = msg
            self.result["error"] = 1
            return self.result
        self.result["text"] = "Message was deleted"
        return self.result


class Longpoll(Groups):
    # To avoid async __init__
    @classmethod
    async def create(cls, use_ssl: bool = True) -> None:
        self = cls()
        # Longpoll params init
        self.lp_key = ""
        self.lp_ts = 0
        self.lp_server = ""
        self.use_ssl = use_ssl
        VK.vk_api.api_url = VK.vk_api.api_url
        # self.vk_groups = Groups()
        # Get Longpoll server parameters
        vk_api_log.debug("# Get LongPoll server parameters to listen")
        get_lp_server_result = await self.getLongPollServer()
        if get_lp_server_result["error"] != 1:
            vk_api_log.debug(f"# {get_lp_server_result['text']}")
        else:
            vk_api_log.error(
                f"# Get Longpoll server parameters error. {get_lp_server_result['text']}",
            )
        return self

    # GET request to VK LongPoll API to listen for messages
    @vk_api_log.catch
    async def listen_longpoll(self) -> dict:
        """
        Longpoll subclass method to listen VK LongPoll response.

        :return: Returns the request result.
        :rtype: ``dict``
        """

        # Form request params
        payload = {
            "act": "a_check",
            "key": self.lp_key,
            "ts": self.lp_ts,
            "wait": VK.vk_longpoll.wait,
        }

        response = await self.do_request(
            "GET",
            self.lp_server,
            params=payload,
            use_ssl=self.use_ssl,
        )
        return response

    # Listen to VK Longpoll server and manage results
    @vk_api_log.catch
    async def process_longpoll_response(self) -> dict:
        """
        Longpoll subclass method to listen VK LongPoll server response.

        :return: Returns the result of VK LongPoll request.
        :rtype: ``dict``
        """

        # # Errors counter for warnings.
        # +1 if warning was received (e.g. API key deprecated)
        # reset if next request is OK
        errors_limit = VK.errors_limit
        wait_period = VK.wait_period
        vk_api_log.debug(
            "# Start to listen LongPoll API. Errors counter was resetted",
        )
        lp_res = {
            "errors_counter": 0,
            "response": "",
            "response_type": "",
            "error": 0,
        }
        response = await self.listen_longpoll()
        # If there is error in VK Longpoll response - process it
        vk_api_log.debug(f"# Longpoll API response: {response}")
        if "Error" in response:
            lp_res["errors_counter"] += 1
            vk_api_log.info(f"# Errors counter: {lp_res['errors_counter']}")
            vk_api_log.warning(f"# {response}")
            if lp_res["errors_counter"] == errors_limit:
                msg = "# Errors limit is over. Shut down."
                vk_api_log.error(msg)
                lp_res["response"] = msg
                lp_res["error"] = 1
                return lp_res
            await asyncio.sleep(wait_period)
            return lp_res
        if "failed" in response:
            process_result = await self.process_longpoll_errors(response)
            # Result contains tuple: True/False, error message to log
            if process_result["error"] == 0:
                # In case of warning we count to ERRORS_LIMIT and then stop
                lp_res["errors_counter"] += 1
                vk_api_log.debug(process_result["text"])
                vk_api_log.debug(
                    f"# Errors counter: {lp_res['errors_counter']}",
                )
                if lp_res["errors_counter"] == errors_limit:
                    msg = "# Errors limit is over. Shut down."
                    vk_api_log.error(msg)
                    lp_res["response"] = msg
                    lp_res["error"] = 1
                    return lp_res
                await asyncio.sleep(wait_period)
                return lp_res
            else:
                msg = f"# Critical error. {process_result['text']}"
                vk_api_log.error(msg)
                lp_res["response"] = msg
                lp_res["error"] = 1
                return lp_res
        else:
            vk_api_log.debug(
                "# No failures in response. Errors counter was resetted",
            )
            lp_res["errors_counter"] = 0
            if response["updates"] == []:
                vk_api_log.debug(
                    "# Listening interval passed, nothing new. Proceeding...",
                )
                return lp_res
            # Process response with message
            self.lp_ts = response["ts"]

            # If this is new/edited comment
            if (
                response["updates"][0]["type"] == "wall_reply_new"
                or response["updates"][0]["type"] == "wall_reply_edit"
                or response["updates"][0]["type"] == "photo_comment_new"
                or response["updates"][0]["type"] == "photo_comment_edit"
            ):
                lp_res["response"] = response
                lp_res["response_type"] = "comment"
                return lp_res

            # If this is new message
            if response["updates"][0]["type"] == "message_new":
                lp_res["response"] = response
                lp_res["response_type"] = "message"
                return lp_res
            return lp_res

    @vk_api_log.catch
    async def process_longpoll_errors(self, result: dict) -> dict:
        """
        Longpoll subclass method to process VK LongPoll server response.

        :type result: ``dict``
        :param result: Dictionary with VK LongPoll request results.

        :return: Returns the result of processing.
        :rtype: ``dict``
        """

        vk_api_log.debug(f"# Processing Longpoll error: {result}")
        if result["failed"] == 1:
            self.result["text"] = (
                f"[VK WARNING] Event history is deprecated or lost. New TS provided: {result['ts']}."
            )
            self.result["error"] = 0
            self.lp_ts = result["ts"]
        if result["failed"] == 2:
            self.result["text"] = (
                "[VK WARNING] API Key is deprecated. Need to get new with 'groups.getLongPollServer'."
            )
            self.result["error"] = 0
            await self.getLongPollServer()
        if result["failed"] == 3:
            self.result["text"] = (
                "[VK WARNING] Information is lost. Need to get new API Key and TS with 'groups.getLongPollServer'."
            )
            self.result["error"] = 0
        if result["failed"] == 4:
            self.result["text"] = (
                "[VK WARNING] Incorrect version of VK API was passed."
            )
            self.result["error"] = 0
            await self.getLongPollServer()
        if self.result["text"] == "":
            self.result["text"] = (
                "[GENERAL ERROR] Something went wrong during VK request managing."
            )
            self.result["error"] = 1
        return self.result
