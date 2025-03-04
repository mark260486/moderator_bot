# -*- coding: utf-8 -*-
# Reviewed: March 03, 2025
from __future__ import annotations

from vk.api import VK_API, vk_api_log
from config.vk import VK


class Wall(VK_API):
    # To avoid async __init__
    @classmethod
    async def create(cls, use_ssl: bool = True) -> Wall:
        """
        VK API Wall subclass init

        :return: Returns the class instance.
        """

        self = cls()
        self.use_ssl = use_ssl
        return self

    @vk_api_log.catch
    async def deleteComment(self, owner_id: int, comment_id: int) -> dict:
        """
        VK API class method to delete comment.
        https://dev.vk.com/ru/method/wall.deleteComment

        :type owner_id: ``int``
        :param owner_id: Public ID with minus. Like -100500

        :type comment_id: ``int``
        :param comment_id: Comment ID.

        :return: Returns the request result.
        :rtype: ``dict``
        """
        vk_method = "wall.deleteComment"
        vk_api_url = f"{VK.vk_api.api_url}{vk_method}"
        payload = {
            "owner_id": owner_id,
            "comment_id": comment_id,
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
        return self.process_response(response, "Comment was removed")
