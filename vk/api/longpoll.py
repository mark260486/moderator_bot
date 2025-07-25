# -*- coding: utf-8 -*-
# Reviewed: July 25, 2025
from __future__ import annotations

from vk.api.groups import Groups
from vk.api import vk_api_log, VK_API
from config.vk import VK_config


class Longpoll(Groups, VK_API):
    # To avoid async __init__
    @classmethod
    async def create(cls, use_ssl: bool = True) -> Longpoll:
        """
        VK API Longpoll subclass init

        :return: Returns the class instance.
        """

        self = cls()
        # Longpoll params init
        self.key = ""
        self.ts = 0
        self.server = ""
        self.use_ssl = use_ssl
        # result variables
        self.result = {
            "text": "",
            "type": "",
        }
        # self.vk_groups = Groups()
        # Get Longpoll server parameters
        vk_api_log.debug("# Get LongPoll server parameters to listen")
        get_server_result = await self.get_long_poll_server()
        if get_server_result:
            if get_server_result["error"] != 1:
                vk_api_log.debug(f"# {get_server_result['text']}")
            else:
                vk_api_log.error(
                    f"# Get Longpoll server parameters error. {get_server_result['text']}",
                )
            return self
        return None

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
            "key": self.key,
            "ts": self.ts,
            "wait": VK_config.Longpoll.wait,
        }

        response = await self.do_request(
            "GET",
            self.server,
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

        vk_api_log.debug("# Starting to listen LongPoll API.")
        response = await self.listen_longpoll()

        # If there are errors in VK Longpoll response - process it
        # Else - process response
        vk_api_log.debug(f"# Longpoll API response: {response}")
        if not response:
            vk_api_log.error("# Longpoll response is empty!")
            return 1
        else:
            if "Error" in response:
                vk_api_log.error(f"# Error during LP request: {response}")
                return 1
            if "failed" in response:
                process_result = await self.process_longpoll_errors(response)
                if process_result["error"] == 0:
                    vk_api_log.error(f"# {process_result['text']}")
                    return 1
                else:
                    msg = f"# Critical error. {process_result['text']}"
                    vk_api_log.error(msg)
                    return 1
            else:
                vk_api_log.debug(
                    "# No failures in response.",
                )
                if response["updates"] == []:
                    vk_api_log.debug("# Listening interval passed, nothing new.")
                    return 0
                # Process response with message
                self.ts = response["ts"]

                # If this is new/edited comment
                if (
                    response["updates"][0]["type"] == "wall_reply_new"
                    or response["updates"][0]["type"] == "wall_reply_edit"
                    or response["updates"][0]["type"] == "photo_comment_new"
                    or response["updates"][0]["type"] == "photo_comment_edit"
                ):
                    self.result['text'] = response
                    self.result['type'] = "comment"
                    return self.result

                # If this is new message
                if response["updates"][0]["type"] == "message_new":
                    self.result['text'] = response
                    self.result['type'] = "message"
                    return self.result
                return self.result

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
            self.ts = result["ts"]
        if result["failed"] == 2:
            self.result["text"] = (
                "[VK WARNING] API Key is deprecated. Need to get new with 'groups.getLongPollServer'."
            )
            self.result["error"] = 0
            await self.get_long_poll_server()
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
            await self.get_long_poll_server()
        if self.result["text"] == "":
            self.result["text"] = (
                "[GENERAL ERROR] Something went wrong during VK request managing."
            )
            self.result["error"] = 1
        return self.result
