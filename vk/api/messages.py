# -*- coding: utf-8 -*-
# Reviewed: July 25, 2025
from __future__ import annotations

import random
from datetime import datetime, timedelta

from vk.api import VK_API, vk_api_log
from config.vk import VK_config


class Messages(VK_API):
    # To avoid async __init__
    @classmethod
    async def create(cls, use_ssl: bool = True) -> Messages:
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

        vk_method = "messages.send"
        vk_api_url = f"{VK_config.API.api_url}{vk_method}"
        payload = {
            "group_id": group_id,
            "peer_id": peer_id,
            "message": text,
            "random_id": random.randint(100, 100000),
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
        return self.process_response(response, "Message was sen")

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

        vk_method = "messages.search"
        vk_api_url = f"{VK_config.API.api_url}{vk_method}"
        payload = {
            "group_id": group_id,
            "peer_id": peer_id,
            "count": count,
            "date": tomorrow,
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
        return self.process_response(response, response["response"])

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

        vk_method = "messages.delete"
        vk_api_url = f"{VK_config.API.api_url}{vk_method}"
        payload = {
            "group_id": group_id,
            "cmids": cm_id,
            "peer_id": peer_id,
            "delete_for_all": VK_config.API.delete_for_all,
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
        return self.process_response(response, "Message was deleted")

    @vk_api_log.catch
    async def remove_chat_user(self, group_id: int, user_id: int, member_id: int) -> dict:
        """
        VK API class method to remove user from the chat.
        https://dev.vk.com/en/method/messages.removeChatUser

        :type group_id: ``int``
        :param group_id: Public ID.

        :type user_id: ``int``
        :param user_id: ID of the user to be removed from the chat.

        :type member_id: ``int``
        :param member_id: ID of the member to be removed. For communities: **-**group_id.

        :return: Returns the request result.
        :rtype: ``dict``
        """

        vk_method = "messages.removeChatUser"
        vk_api_url = f"{VK_config.API.api_url}{vk_method}"
        payload = {
            "group_id": group_id,
            "user_id": user_id,
            "member_id": member_id,
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
        return self.process_response(response, "User was removed")
