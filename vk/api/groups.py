# -*- coding: utf-8 -*-
# Reviewed: December 27, 2024
from __future__ import annotations

from vk.api import VK_API, vk_api_log
from config.vk import VK


class Groups(VK_API):
    # To avoid async __init__
    @classmethod
    async def create(cls, result: dict = None, use_ssl: bool = True) -> None:
        """
        VK API Groups subclass init

        :return: Returns the class instance.
        """
        self = cls()
        self.use_ssl = use_ssl
        self.result = result
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
