# Reviewed: April 09, 2024

from loguru import logger
import auxiliary
import vk_api
import filter
from time import sleep


class processing:
    def __init__(self, aux: auxiliary, processing_logger: logger = None, debug_enabled: bool = False, # type: ignore
                 send_msg_to_vk: bool = False) -> None:
        """
        Processing class init

        :type aux: ``auxiliary``
        :param aux: Auxiliary class instance.

        :type processing_logger: ``logger``
        :param processing_logger: Logger instance.

        :type debug_enabled: ``bool``
        :param debug_enabled: Boolean to switch on and off debugging. False by default.

        :return: Returns the class instance.
        """

        self.params = aux.read_config()
        if processing_logger == None:
            logger.remove()
            if debug_enabled:
                logger.add(self.params['processing_log'], level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            else:
                logger.add(self.params['processing_log'], level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            self.logger = logger
        else:
            self.logger = processing_logger
        self.filter = filter.filter(aux, self.logger)
        self.send_msg_to_vk = send_msg_to_vk
        # Result = 0 - false
        # Result = 1 - true
        # Result = 2 - suspicious
        self.result = {
            'result': 0,
            'text': "",
            'case': ""
        }


    @logger.catch
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
        # replaced = text.replace('.', '[.]')
        replaced = text.replace('\n', ' ')
        replaced = replaced.replace('ё', 'е')
        replaced = replaced.lower()
        return replaced


    @logger.catch
    def get_username(self, main_log: logger, vk_api: vk_api, user_id: int) -> str: # type: ignore
        """
        Processing class method to get username and process possible error in the response..

        :type main_log: ``logger``
        :param main_log: Logger instance.

        :type vk_api: ``vk_api``
        :param vk_api: VK API Class instance.

        :type user_id: ``int``
        :param user_id: User ID.
        """
        username = vk_api.get_user(user_id)
        if username['error'] == 1:
            main_log.error(f"# Can't get username from ID: {username['text']}")
            return "Can't get username"
        else:
            return username['text']


    @logger.catch
    def filter_response_processing(self, main_log: logger, vk_api: vk_api,  # type: ignore
                                message: str, username: str, group_id: int, isMember: dict,
                                peer_id: int = None, cm_id: int = None,
                                attachments: dict = None, false_positive: bool = False) -> None:
        """
        Processing class method to work with filter response.
        I'm suppose to use this method for comments in future, so it's the dedicated function.

        :type main_log: ``logger``
        :param main_log: Logger instance.

        :type vk_api: ``vk_api``
        :param vk_api: VK API Class instance.

        :type message: ``str``
        :param message: Text of message/comment.

        :type username: ``str``
        :param username: Username as text.

        :type group_id: ``int``
        :param group_id: Group ID.

        :type isMember: ``dict``
        :param isMember: Is user member of the public.

        :type peer_id: ``int``
        :param peer_id: Peer ID. It is Int chat ID.

        :type cm_id: ``int``
        :param cm_id: Conversation message ID.

        :type attachments: ``dict``
        :param attachments: Message attachments, if they are.
        """

        filter_result = self.filter.filter_response(message, username, attachments)
        main_log.debug(f"============== Filter response processing =================")
        main_log.debug(f"# False positive: {false_positive}")
        main_log.debug(f"# Filter result: {filter_result}")
        # Exit if None
        if filter_result == None:
            return
        # If filter returns 0, we should wait for a couple of seconds.
        # Reason: there is no more ID for messages in public chat and we can't
        #    know if message was edited. So we wait for bad bot to edit message and then
        #    through VK API search messages get possibly redacted message and check it once again.
        # ToDo: lookup for several messages and specify it as parameter.
        if filter_result['result'] == 0 and false_positive == False:
            main_log.debug(f"# Clear message, wait for {self.params['VK']['check_delay']} seconds and check it once more.")
            sleep(self.params['VK']['check_delay'])
            main_log.debug(f"Group ID: {group_id}, Peer ID: {peer_id}")
            last_reply = vk_api.search_messages(group_id, peer_id, self.params['VK']['messages_search_count'])['text']
            main_log.debug(f"# Last reply: {last_reply}")
            last_reply_msg = last_reply['items'][0]['text']
            last_reply_username = self.get_username(main_log, vk_api, last_reply['items'][0]['from_id'])
            last_reply_cm_id = last_reply['items'][0]['conversation_message_id']
            last_reply_peer_id = last_reply['items'][0]['peer_id']
            last_reply_attachments = last_reply['items'][0]['attachments']
            self.filter_response_processing(main_log, vk_api,
                                            last_reply_msg, last_reply_username,
                                            group_id, isMember, last_reply_peer_id,
                                            last_reply_cm_id, last_reply_attachments, false_positive = True)
        # If filter returns 1 - we catch something
        if filter_result['result'] == 1:
            div = "-----------------------------"
            msg_main = f"# Message to remove from {username}: '{message}'."
            words = filter_result['text']
            case = f"# Case: {filter_result['case']}"
            msg = f"{msg_main}\n{div}\n# {words}\n{div}\n{case}"
            main_log.info(msg)
            main_log.debug(f"# Group ID: {group_id}, CM ID: {cm_id}, Peer ID: {peer_id}")
            delete_result = vk_api.delete_message(group_id, cm_id, peer_id)
            main_log.debug(f"# Delete result: {delete_result['text']}")

            if delete_result['error'] == 0:
                main_log.info("# Message was removed")
                if self.send_msg_to_vk:
                    send_result = vk_api.send_message(f"Сообщение от {username} было удалено автоматическим фильтром. Причина: {filter_result['case']}", group_id, peer_id)
            else:
                main_log.info("# Message was not removed")
                if self.send_msg_to_vk:
                    send_result = vk_api.send_message(f"# Сообщение от {username} не было удалено автоматическим фильтром.", group_id, peer_id)

            if self.send_msg_to_vk:
                if send_result['error'] == 0:
                    main_log.info(f"# Service message was sent to {self.params['VK']['chats'][str(peer_id)]}")
        # If filter returns 2 - we should get warning to Telegram
        if filter_result['result'] == 2:
            div = "-----------------------------"
            msg_main = f"# Suspicious message from {username}: '{message}' was found."
            words = filter_result['text']
            case = f"# Case: {filter_result['case']}"
            # This was made for avoid mess in msg
            msg = f"{msg_main}\n{div}\n# {words}\n{div}\n{case}"
            main_log.info(msg)
            if self.send_msg_to_vk:
                main_log.info(f"# Text: {filter_result['text']}.")


    @logger.catch
    def message(self, response: dict, vk_api: vk_api, main_log: logger) -> None: # type: ignore
        """
        Processing class method to process new VK message.

        :type response: ``dict``
        :param response: VK LongPoll response.

        :type vk_api: ``vk_api``
        :param vk_api: VK API Class instance.

        :type main_log: ``logger``
        :param main_log: Logger instance.
        """

        main_log.debug("# Processing message")
        message = self.replacements(response['updates'][0]['object']['message']['text'])
        attachments = response['updates'][0]['object']['message']['attachments']
        user_id = response['updates'][0]['object']['message']['from_id']
        group_id = response['updates'][0]['group_id']
        peer_id = response['updates'][0]['object']['message']['peer_id']
        cm_id = response['updates'][0]['object']['message']['conversation_message_id']
        username = self.get_username(main_log, vk_api, user_id)
        # Check if user is in Group. If not - it's suspicious
        main_log.debug(f"# Checking if User is in Group")
        isMember = vk_api.is_group_member(user_id, self.params['VK']['VK_API']['group_id'])
        if isMember['text'] == "0":
            main_log.info(f"# Message was sent by User not in Group")

        # Kick user notification
        if message == "" and attachments == "":
            try:
                action_type = response['updates'][0]['object']['message']['action']['type']
            except:
                main_log.error(f"# Can't get Action Type from the response")
            if action_type != "":
                if action_type == "chat_kick_user":
                    kicked_user_id = response['updates'][0]['object']['message']['action']['member_id']
                    kicked_username = vk_api.get_user(kicked_user_id)
                    if kicked_username['error'] == 1:
                        main_log.error(f"# Can't get username from ID: {kicked_username['text']}")
                    else:
                        kicked_username = kicked_username['text']
                        msg = f"# {username} kicked {kicked_username} from {self.params['VK']['chats'][str(peer_id)]}"
                        main_log.info(msg)

        # If all is OK - start checking message
        main_log.debug(f"# New message: {message}; New TS: {vk_api.lp_ts}; User: {username}")
        self.filter_response_processing(main_log, vk_api,
                                        message = message, username = username,
                                        group_id = group_id, peer_id = peer_id, cm_id = cm_id, attachments = attachments,
                                        isMember = isMember)

        # # Tests section # #
        # Check for language of username and message.
        # main_log.debug(f"# Username lang: {detect(username)}. Message lang: {detect(message)}")
        # # End of Tests section # #


    @logger.catch
    def comment(self, response: dict, vk_api: vk_api, main_log: logger) -> None: # type: ignore
        """
        Processing class method to process new VK commentary.

        :type response: ``dict``
        :param response: VK LongPoll response.

        :type response: ``vk_api``
        :param response: VK API Class instance.

        :type main_log: ``logger``
        :param main_log: Logger instance.
        """

        main_log.debug("# Processing comment")
        message = self.replacements(response['updates'][0]['object']['text'])
        user_id = response['updates'][0]['object']['from_id']
        username = vk_api.get_user(user_id)
        if username['error'] == 1:
            main_log.error(f"# Can't get username from ID: {username['text']}")
            return False
        else:
            username = username['text']

        main_log.debug(f"# New/edited comment: {message}; New TS: {vk_api.lp_ts}; User: {username}")
        filter_result = self.filter.filter_response(message, username, [])
        main_log.debug(f"# Filter result: {filter_result}")
        if filter_result['result'] == 1:
            main_log.info(f"# Comment to remove from {username}: '{message}'")
