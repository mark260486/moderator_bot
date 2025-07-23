# -*- coding: utf-8 -*-
# Reviewed: March 20, 2025
from __future__ import annotations

from time import sleep
from typing import Optional, Dict

from loguru import logger
from loguru import logger as vk_proc_log

from config.vk import VK
from config.logs import Logs
from filter import Filter
from vk.api.groups import Groups
from vk.api.messages import Messages
from vk.api.users import Users


class VK_processing:
    # To avoid async __init__
    @classmethod
    async def create(
        cls,
        vk_proc_log: logger = vk_proc_log,  # type: ignore
        debug_enabled: bool = False,
        send_msg_to_vk: bool = False,
    ) -> None:
        """
        VK Processing class init

        :type processing_vk_log: ``logger``
        :param processing_vk_log: Logger instance.

        :type debug_enabled: ``bool``
        :param debug_enabled: Boolean to switch on and off debugging. False by default.

        :return: Returns the class instance.
        """

        self = cls()
        if vk_proc_log is None:
            if debug_enabled:
                vk_proc_log.add(
                    Logs.processing_log,
                    level="DEBUG",
                    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
                )
                vk_proc_log.debug(
                    "# VK Processing class will run in Debug mode.",
                )
            else:
                vk_proc_log.add(
                    Logs.processing_log,
                    level="INFO",
                    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
                )
            self.vk_proc_log = vk_proc_log
        else:
            self.vk_proc_log = vk_proc_log

        # Necessary instances
        self.filter = await Filter.create(debug_enabled=debug_enabled)
        self.vk_groups = await Groups.create()
        self.vk_messages = await Messages.create()
        self.vk_users = await Users.create()

        # Internal variables and options
        # Result = 0 - false
        # Result = 1 - true
        # Result = 2 - suspicious
        self.result = {"result": 0, "text": "", "case": ""}
        self.send_msg_to_vk = send_msg_to_vk
        return self

    @vk_proc_log.catch
    async def replacements(self, text: str) -> str:
        """
        Processing class method to replace unwanted symbols in provided text.
        Replaced symbols: ё -> е, \n -> ' '

        :type text_to_check: ``str``
        :param text_to_check: Text to check.

        :return: Returns the text with replacements.
        :rtype: ``str``
        """

        replaced = text.replace("\n", " ").replace("ё", "е").lower()
        return replaced

    @vk_proc_log.catch
    async def get_username(self, user_id: int) -> str:
        """
        Processing class method to get username and process possible error in the response.

        :type user_id: ``int``
        :param user_id: User ID.

        :return: Returns the username.
        :rtype: ``str``
        """
        username = await self.vk_users.get(user_id=user_id)
        if username["error"] == 1:
            vk_proc_log.error(f"# Can't get username from ID: {username['text']}")
            return "Can't get username"
        return username["text"]

    @vk_proc_log.catch
    async def filter_response_processing(
        self,
        message: str,
        username: str,
        group_id: int,
        is_member: bool,
        peer_id: Optional[int] = None,
        cm_id: Optional[int] = None,
        attachments: Optional[Dict] = None,
        false_positive: bool = False,
    ) -> None:
        """
        Processing class method to work with filter response.
        I'm suppose to use this method for comments in future, so it's the dedicated function.

        :type message: ``str``
        :param message: Text of message/comment.

        :type username: ``str``
        :param username: Username as text.

        :type group_id: ``int``
        :param group_id: Group ID.

        :type is_member: ``bool``
        :param is_member: Is user member of the public. True by default.

        :type peer_id: ``Optional[int]``
        :param peer_id: Peer ID. It is Int chat ID.

        :type cm_id: ``Optional[int]``
        :param cm_id: Conversation message ID.

        :type attachments: ``Optional[Dict]``
        :param attachments: Message attachments, if they are.
        """

        filter_result = await self.filter.filter_response(
            message,
            username,
            attachments,
            is_member,
        )
        vk_proc_log.debug("============== Filter response processing =================")
        vk_proc_log.debug(f"# False positive: {false_positive}")
        vk_proc_log.debug(f"# Filter result: {filter_result}")

        # Exit if None
        if filter_result is None:
            return

        # If filter returns 0, we should wait for a couple of seconds.
        # Reason: there is no more ID for messages in public chat and we can't
        #    know if message was edited. So we wait for bad bot to edit message and then
        #    through VK API search messages get possibly redacted message and check it once again.
        # Additional condition is for Message type of the update
        if filter_result["result"] in [0, 2] and not false_positive and cm_id is not None:
            vk_proc_log.debug(f"# This was clear message, we'll wait for {VK.check_delay} seconds and check it once more.")
            sleep(VK.check_delay)
            vk_proc_log.debug(f"Group ID: {group_id}, Peer ID: {peer_id}")
            last_reply = await self.vk_messages.search(
                group_id,
                peer_id,
                VK.messages_search_count,
            )
            last_reply = last_reply["text"]
            vk_proc_log.debug(f"# Last reply: {last_reply}")
            if last_reply["items"] != []:
                await self.filter_response_processing(
                    last_reply["items"][0]["text"],
                    await self.get_username(
                        user_id=last_reply["items"][0]["from_id"]
                    ),
                    group_id,
                    is_member,
                    last_reply["items"][0]["peer_id"],
                    last_reply["items"][0]["conversation_message_id"],
                    last_reply["items"][0]["attachments"],
                    false_positive=True,
                )

        # If filter returns 1 - we catch something
        if filter_result["result"] == 1:
            # Compose message for notification
            div = "-----------------------------"
            # update_type = "Message"
            # if cm_id is not None:
            #     update_type = "Comment"
            msg_main = f"# Message to remove from {username}:\n# '{message.replace('.', '[.]').replace(':', '[:]')}'."
            words = filter_result["text"]
            case = f"# Case: {filter_result['case']}"
            msg = f"{msg_main}\n{div}\n# {words}\n{div}\n{case}"
            vk_proc_log.info(msg)
            # Message remove
            if cm_id is not None:
                vk_proc_log.debug(f"# Group ID: {group_id}, CM ID: {cm_id}, Peer ID: {peer_id}")

                delete_result = await self.vk_messages.delete(
                    group_id, cm_id, peer_id
                )
                vk_proc_log.debug(f"# Delete result: {delete_result['text']}")
                if delete_result["error"] == 0:
                    vk_proc_log.info("# Message was removed")
                    if self.send_msg_to_vk:
                        send_result = await self.vk_messages.send(
                            f"Сообщение от {username} было удалено автоматическим фильтром. Причина: {filter_result['case']}",
                            group_id,
                            peer_id,
                        )
                else:
                    vk_proc_log.info("# Message was not removed")
                    if self.send_msg_to_vk:
                        send_result = await self.vk_messages.send(
                            f"# Сообщение от {username} не было удалено автоматическим фильтром.",
                            group_id,
                            peer_id,
                        )
            # Comment remove
            else:
                pass

            if self.send_msg_to_vk:
                if send_result["error"] == 0:
                    vk_proc_log.info(
                        f"# Service message was sent to {VK.chats[str(peer_id)]}",
                    )

        # If filter returns 2 - we should get warning to Telegram
        if filter_result["result"] == 2:
            div = "-----------------------------"
            msg_main = f"# Suspicious message from {username}:\n# '{message.replace('.', '[.]').replace(':', '[:]')}'"
            words = filter_result["text"]
            case = f"# Case: {filter_result['case']}"
            # This was made for avoid mess in msg var
            msg = f"{msg_main}\n{div}\n# {words}\n{div}\n{case}"
            vk_proc_log.info(msg)
            if self.send_msg_to_vk:
                vk_proc_log.info(f"# Text: {filter_result['text']}.")

    @vk_proc_log.catch
    async def message(self, response: dict) -> None:
        """
        Processing class method to process new VK message.

        :type response: ``dict``
        :param response: VK LongPoll response.
        """

        vk_proc_log.debug("# Processing message")
        message = await self.replacements(response["updates"][0]["object"]["message"]["text"])
        attachments = response["updates"][0]["object"]["message"]["attachments"]
        user_id = response["updates"][0]["object"]["message"]["from_id"]
        group_id = response["updates"][0]["group_id"]
        peer_id = response["updates"][0]["object"]["message"]["peer_id"]
        cm_id = response["updates"][0]["object"]["message"]["conversation_message_id"]
        username = await self.get_username(user_id)
        # Check if user is in Group. If not - it's suspicious
        vk_proc_log.debug("# Checking if User is in Group")
        is_member = True
        is_memberRes = await self.vk_groups.is_member(
            user_id=user_id,
            group_id=VK.vk_api.group_id,
        )
        if is_memberRes:
            if is_memberRes["text"] == "0":
                vk_proc_log.info("# Message was sent by non subscribed User. Plus one suspicious point.")
                is_member = False

        # Kick user notification
        if message == "" and attachments == "":
            try:
                action_type = response["updates"][0]["object"]["message"]["action"]["type"]
            except Exception:
                vk_proc_log.error("# Can't get Action Type from the response")
                raise
            if action_type != "":
                if action_type == "chat_kick_user":
                    kicked_user_id = response["updates"][0]["object"]["message"]["action"]["member_id"]
                    kicked_username = await self.vk_users.get(kicked_user_id)
                    if kicked_username["error"] == 1:
                        vk_proc_log.error(f"# Can't get username from ID: {kicked_username['text']}")
                    else:
                        kicked_username = kicked_username["text"]
                        msg = f"# {username} kicked {kicked_username} from {VK.chats[str(peer_id)]}"
                        vk_proc_log.info(msg)

        # If all is OK - start checking message
        vk_proc_log.debug(f"# New message: {message}; User: {username}")
        await self.filter_response_processing(
            message=message,
            username=username,
            group_id=group_id,
            peer_id=peer_id,
            cm_id=cm_id,
            attachments=attachments,
            is_member=is_member,
        )

        # # Tests section # #
        # Check for language of username and message.
        # vk_proc_log.debug(f"# Username lang: {detect(username)}. Message lang: {detect(message)}")
        # # End of Tests section # #

    @vk_proc_log.catch
    async def comment(self, response: dict) -> None:
        """
        Processing class method to process new VK commentary.

        :type response: ``dict``
        :param response: VK LongPoll response.
        """

        vk_proc_log.debug("# Processing comment")
        message = await self.replacements(response["updates"][0]["object"]["text"])
        user_id = response["updates"][0]["object"]["from_id"]
        username = await self.get_username(user_id)

        vk_proc_log.debug(f"# New/edited comment: {message}; User: {username}")
        filter_result = await self.filter.filter_response(message, username, [], True)
        vk_proc_log.debug(f"# Filter result: {filter_result}")
        if filter_result["result"] == 1:
            # Compose message for notification
            div = "-----------------------------"
            msg_main = f"# Comment to remove from {username}:\n# '{message.replace('.', '[.]').replace(':', '[:]')}'."
            words = filter_result["text"]
            case = f"# Case: {filter_result['case']}"
            msg = f"{msg_main}\n{div}\n# {words}\n{div}\n{case}"
            vk_proc_log.info(msg)
