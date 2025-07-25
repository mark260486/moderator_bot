# -*- coding: utf-8 -*-
# Reviewed: July 25, 2025
from __future__ import annotations

from vk.api import VK_API, vk_api_log
from config.vk import VK_config


class Groups(VK_API):
    # To avoid async __init__
    @classmethod
    async def create(cls, result: dict = None, use_ssl: bool = True) -> Groups:
        """
        VK API Groups subclass init

        :return: Returns the class instance.
        """
        self = cls()
        self.use_ssl = use_ssl
        self.result = result or {}
        return self

    @vk_api_log.catch
    async def is_member(self, user_id: int, group_id: int) -> dict:
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

        vk_method = "groups.isMember"
        vk_api_url = f"{VK_config.API.api_url}{vk_method}"
        payload = {
            "user_id": user_id,
            "group_id": group_id,
            "v": VK_config.API.version,
        }
        headers = {"Authorization": f"Bearer {VK_config.API.api_key}"}

        response = await self.do_request(
            "GET",
            vk_api_url,
            headers=headers,
            params=payload,
            use_ssl=self.use_ssl,
        )
        if response:
            self.result["text"] = str(response["response"])
            return self.result
        return None

    @vk_api_log.catch
    async def get_long_poll_server(self) -> dict:
        """
        VK API class method to get LongPoll server parameters.
        https://dev.vk.com/ru/method/groups.getLongPollServer

        :return: Returns the request result.
        :rtype: ``dict``
        """

        vk_method = "groups.getLongPollServer"
        vk_api_url = f"{VK_config.API.api_url}{vk_method}"
        vk_group_id = VK_config.API.group_id
        vk_api_version = VK_config.API.version

        payload = {"group_id": vk_group_id, "v": vk_api_version}
        headers = {"Authorization": f"Bearer {VK_config.API.api_key}"}

        response = await self.do_request(
            "GET",
            vk_api_url,
            headers=headers,
            params=payload,
            use_ssl=self.use_ssl,
        )
        if isinstance(response, dict):
            self.server = response["response"]["server"]
            self.key = response["response"]["key"]
            self.ts = response["response"]["ts"]
            self.result["text"] = "Longpoll server parameters were received"
            return self.result
        else:
            self.result["text"] = "Cannot get Longpoll server parameters"
            self.result["error"] = 1
            return self.result
