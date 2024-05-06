# Reviewed: May 06, 2024

from loguru import logger
from loguru import logger as vk_proc_log
from vk_api import Messages, Users, Groups
from filter import Filter
from time import sleep
from config import VK, Logs


class VK_processing:
    def __init__(self, vk_proc_log: logger = vk_proc_log, debug_enabled: bool = False, # type: ignore
                 send_msg_to_vk: bool = False) -> None:
        """
        VK Processing class init

        :type processing_vk_log: ``logger``
        :param processing_vk_log: Logger instance.

        :type debug_enabled: ``bool``
        :param debug_enabled: Boolean to switch on and off debugging. False by default.

        :return: Returns the class instance.
        """

        if vk_proc_log == None:
            if debug_enabled:
                vk_proc_log.add(Logs.processing_log, level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
                vk_proc_log.debug("# VK Processing class will run in Debug mode.")
            else:
                vk_proc_log.add(Logs.processing_log, level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            self.vk_proc_log = vk_proc_log
        else:
            self.vk_proc_log = vk_proc_log

        # Neccesary instances
        self.filter = Filter(debug_enabled = debug_enabled)
        self.vk_groups = Groups()
        self.vk_messages = Messages()
        self.vk_users = Users()

        # Internal variables and options
        # Result = 0 - false
        # Result = 1 - true
        # Result = 2 - suspicious
        self.result = {
            'result': 0,
            'text': "",
            'case': ""
        }
        self.send_msg_to_vk = send_msg_to_vk


    @vk_proc_log.catch
    def replacements(self, text: str) -> str:
        """
        Processing class method to replace unwanted symbols in provided text.
        Replaced symbols: ё -> е, \n -> ' '

        :type text_to_check: ``str``
        :param text_to_check: Text to check.

        :return: Returns the text with replacements.
        :rtype: ``str``
        """

        # Neccessary replaces in text for further processing
        replaced = text.replace('.', '[.]')
        replaced = text.replace('\n', ' ')
        replaced = replaced.replace('ё', 'е')
        replaced = replaced.lower()
        return replaced


    @vk_proc_log.catch
    def get_username(self, user_id: int) -> str: # type: ignore
        """
        Processing class method to get username and process possible error in the response..

        :type user_id: ``int``
        :param user_id: User ID.
        """
        username = self.vk_users.get(user_id = user_id)
        if username['error'] == 1:
            vk_proc_log.error(f"# Can't get username from ID: {username['text']}")
            return "Can't get username"
        else:
            return username['text']


    @vk_proc_log.catch
    def filter_response_processing(self, message: str, username: str, group_id: int, isMember: bool,
                                peer_id: int = None, cm_id: int = None,
                                attachments: dict = None, false_positive: bool = False) -> None:
        """
        Processing class method to work with filter response.
        I'm suppose to use this method for comments in future, so it's the dedicated function.

        :type message: ``str``
        :param message: Text of message/comment.

        :type username: ``str``
        :param username: Username as text.

        :type group_id: ``int``
        :param group_id: Group ID.

        :type isMember: ``bool``
        :param isMember: Is user member of the public. True by default.

        :type peer_id: ``int``
        :param peer_id: Peer ID. It is Int chat ID.

        :type cm_id: ``int``
        :param cm_id: Conversation message ID.

        :type attachments: ``dict``
        :param attachments: Message attachments, if they are.
        """

        filter_result = self.filter.filter_response(message, username, attachments, isMember)
        vk_proc_log.debug(f"============== Filter response processing =================")
        vk_proc_log.debug(f"# False positive: {false_positive}")
        vk_proc_log.debug(f"# Filter result: {filter_result}")

        # Exit if None
        if filter_result == None:
            return

        # If filter returns 0, we should wait for a couple of seconds.
        # Reason: there is no more ID for messages in public chat and we can't
        #    know if message was edited. So we wait for bad bot to edit message and then
        #    through VK API search messages get possibly redacted message and check it once again.
        if filter_result['result'] == 0 and false_positive == False:
            vk_proc_log.debug(f"# Clear message, wait for {VK.check_delay} seconds and check it once more.")
            sleep(VK.check_delay)
            vk_proc_log.debug(f"Group ID: {group_id}, Peer ID: {peer_id}")
            last_reply = self.vk_messages.search(group_id, peer_id, VK.messages_search_count)['text']
            vk_proc_log.debug(f"# Last reply: {last_reply}")
            last_reply_msg = last_reply['items'][0]['text']
            last_reply_username = self.get_username(user_id = last_reply['items'][0]['from_id'])
            last_reply_cm_id = last_reply['items'][0]['conversation_message_id']
            last_reply_peer_id = last_reply['items'][0]['peer_id']
            last_reply_attachments = last_reply['items'][0]['attachments']
            self.filter_response_processing(last_reply_msg, last_reply_username,
                                            group_id, isMember, last_reply_peer_id,
                                            last_reply_cm_id, last_reply_attachments, false_positive = True)

        # If filter returns 1 - we catch something
        if filter_result['result'] == 1:
            div = "-----------------------------"
            msg_main = f"# Message to remove from {username}: '{message}'."
            words = filter_result['text']
            case = f"# Case: {filter_result['case']}"
            msg = f"{msg_main}\n{div}\n# {words}\n{div}\n{case}"
            vk_proc_log.info(msg)
            vk_proc_log.debug(f"# Group ID: {group_id}, CM ID: {cm_id}, Peer ID: {peer_id}")
            delete_result = self.vk_messages.delete(group_id, cm_id, peer_id)
            vk_proc_log.debug(f"# Delete result: {delete_result['text']}")

            if delete_result['error'] == 0:
                vk_proc_log.info("# Message was removed")
                if self.send_msg_to_vk:
                    send_result = self.vk_messages.send(f"Сообщение от {username} было удалено автоматическим фильтром. Причина: {filter_result['case']}", group_id, peer_id)
            else:
                vk_proc_log.info("# Message was not removed")
                if self.send_msg_to_vk:
                    send_result = self.vk_messages.send(f"# Сообщение от {username} не было удалено автоматическим фильтром.", group_id, peer_id)

            if self.send_msg_to_vk:
                if send_result['error'] == 0:
                    vk_proc_log.info(f"# Service message was sent to {VK.chats[str(peer_id)]}")

        # If filter returns 2 - we should get warning to Telegram
        if filter_result['result'] == 2:
            div = "-----------------------------"
            msg_main = f"# Suspicious message from {username}: '{message}' was found."
            words = filter_result['text']
            case = f"# Case: {filter_result['case']}"
            # This was made for avoid mess in msg var
            msg = f"{msg_main}\n{div}\n# {words}\n{div}\n{case}"
            vk_proc_log.info(msg)
            if self.send_msg_to_vk:
                vk_proc_log.info(f"# Text: {filter_result['text']}.")


    @vk_proc_log.catch
    def message(self, response: dict) -> None: # type: ignore
        """
        Processing class method to process new VK message.

        :type response: ``dict``
        :param response: VK LongPoll response.
        """

        vk_proc_log.debug("# Processing message")
        message = self.replacements(response['updates'][0]['object']['message']['text'])
        attachments = response['updates'][0]['object']['message']['attachments']
        user_id = response['updates'][0]['object']['message']['from_id']
        group_id = response['updates'][0]['group_id']
        peer_id = response['updates'][0]['object']['message']['peer_id']
        cm_id = response['updates'][0]['object']['message']['conversation_message_id']
        username = self.get_username(user_id)
        # Check if user is in Group. If not - it's suspicious
        vk_proc_log.debug(f"# Checking if User is in Group")
        isMember = True
        isMemberRes = self.vk_groups.isMember(user_id = user_id, group_id = VK.vk_api.group_id)
        if isMemberRes['text'] == "0":
            vk_proc_log.info(f"# Message was sent by User not in Group")
            isMember = False

        # Kick user notification
        if message == "" and attachments == "":
            try:
                action_type = response['updates'][0]['object']['message']['action']['type']
            except:
                vk_proc_log.error(f"# Can't get Action Type from the response")
            if action_type != "":
                if action_type == "chat_kick_user":
                    kicked_user_id = response['updates'][0]['object']['message']['action']['member_id']
                    kicked_username = self.vk_users.get(kicked_user_id)
                    if kicked_username['error'] == 1:
                        vk_proc_log.error(f"# Can't get username from ID: {kicked_username['text']}")
                    else:
                        kicked_username = kicked_username['text']
                        msg = f"# {username} kicked {kicked_username} from {VK.chats[str(peer_id)]}"
                        vk_proc_log.info(msg)

        # If all is OK - start checking message
        vk_proc_log.debug(f"# New message: {message}; User: {username}")
        self.filter_response_processing(message = message, username = username,
                                        group_id = group_id, peer_id = peer_id, cm_id = cm_id, attachments = attachments,
                                        isMember = isMember)

        # # Tests section # #
        # Check for language of username and message.
        # vk_proc_log.debug(f"# Username lang: {detect(username)}. Message lang: {detect(message)}")
        # # End of Tests section # #


    @vk_proc_log.catch
    def comment(self, response: dict) -> None: # type: ignore
        """
        Processing class method to process new VK commentary.

        :type response: ``dict``
        :param response: VK LongPoll response.
        """

        vk_proc_log.debug("# Processing comment")
        message = self.replacements(response['updates'][0]['object']['text'])
        user_id = response['updates'][0]['object']['from_id']
        username = self.vk_users.get(user_id)
        if username['error'] == 1:
            vk_proc_log.error(f"# Can't get username from ID: {username['text']}")
            return False
        else:
            username = username['text']

        vk_proc_log.debug(f"# New/edited comment: {message}; User: {username}")
        filter_result = self.filter.filter_response(message, username, [], True)
        vk_proc_log.debug(f"# Filter result: {filter_result}")
        if filter_result['result'] == 1:
            vk_proc_log.info(f"# Comment to remove from {username}: '{message}'")
