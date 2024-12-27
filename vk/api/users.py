# -*- coding: utf-8 -*-
# Reviewed: December 27, 2024
from __future__ import annotations

from vk.api import VK_API, vk_api_log
from config.vk import VK


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
