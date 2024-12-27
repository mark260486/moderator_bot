# -*- coding: utf-8 -*-
# Reviewed: December 27, 2024
from __future__ import annotations

import json
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
        await self.reset_result()
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
            msg = f"Error occure during the request: {str(e)}"
            vk_api_log.error(msg)
            return msg
        try:
            # response.encoding('utf-8')
            vk_api_log.debug(f"# Request result: {response}")
            res = json.loads(response.text)
            vk_api_log.debug(f"# Response text: {res}")
            if "error" in res.keys():
                msg = f"[VK ERROR] Response: error code - {response['error']['error_code']}, description: {response['error']['error_msg']}"
                return msg
            return res
        except ValueError as exception:
            msg = f"# Failed to parse json object from response. Exception: {exception}"
            raise ValueError(msg)

    @vk_api_log.catch
    async def reset_result(self) -> None:
        """
        VK API class method to reset request results.
        """

        vk_api_log.debug("# Reset result")
        self.result = {"text": "", "error": 0}
