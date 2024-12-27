# -*- coding: utf-8 -*-
# Reviewed: December 27, 2024
from __future__ import annotations

from vk.api import VK_API, vk_api_log
from config.vk import VK


class Wall(VK_API):
    # To avoid async __init__
    @classmethod
    async def create(cls, use_ssl: bool = True) -> None:
        self = cls()
        self.use_ssl = use_ssl
        return self

    @vk_api_log.catch
    async def deleteComment(self, owner_id, comment_id) -> dict:
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
        if "error" in response["response"][0].keys():
            msg = f"[VK ERROR] Response: error code - {response['response'][0]['error']['code']}, description: {response['response'][0]['error']['description']}"
            vk_api_log.error(msg)
            self.result["text"] = msg
            self.result["error"] = 1
            return self.result
        self.result["text"] = "Comment was deleted"
        return self.result
