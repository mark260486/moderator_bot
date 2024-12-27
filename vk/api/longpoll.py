# -*- coding: utf-8 -*-
# Reviewed: December 27, 2024
from __future__ import annotations

import asyncio

from vk.api.groups import Groups
from vk.api import vk_api_log, VK_API
from config import VK


class Longpoll(Groups, VK_API):
    # To avoid async __init__
    @classmethod
    async def create(cls, use_ssl: bool = True) -> None:
        self = cls()
        # Longpoll params init
        self.lp_key = ""
        self.lp_ts = 0
        self.lp_server = ""
        self.use_ssl = use_ssl
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
            vk_api_log.info(f"Errors counter: {lp_res['errors_counter']}")
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
                vk_api_log.debug(f"# {process_result['text']}")
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
