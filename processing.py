# Reviewed: January, 10
# ToDo:
#   - comment all


from loguru import logger
import filter


DEBUG_ENABLED = False


class processing:
    def __init__(self, aux, processing_logger = None) -> None:
        self.params = aux.read_params()
        self.filter = filter.filter(aux, processing_logger)
        if processing_logger == None:
            if DEBUG_ENABLED:
                logger.add(self.params['processing_log'], level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            else:
                logger.add(self.params['processing_log'], level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            self.logger = logger
        else:
            self.logger = processing_logger
        # Result = 0 - false
        # Result = 1 - true
        # Result = 2 - suspicious
        self.result = {
            'result': 0,
            'text': "",
            'case': ""
        }


    @logger.catch
    def replacements(self, text):
        # Neccessary replaces in text for further processing
        replaced = text.replace('.', '[.]')
        replaced = replaced.replace('\n', ' ')
        replaced = replaced.replace('ё', 'е')
        return replaced


    @logger.catch
    def message(self, response, vk_api, main_log, cases_log = None):
        main_log.debug("# Processing message")
        message = self.replacements(response['updates'][0]['object']['message']['text'])
        attachments = response['updates'][0]['object']['message']['attachments']
        user_id = response['updates'][0]['object']['message']['from_id']
        username = vk_api.get_user(user_id)
        chat_id = response['updates'][0]['object']['message']['peer_id']
        if username['error'] == 1:
            main_log.error(f"# Can't get username from ID: {username['text']}")
        else:
            username = username['text']

        # If all is OK - start checking message
        main_log.debug(f"# New message: {message}; New TS: {vk_api.lp_ts}; User: {username}")
        filter_result = self.filter.filter_response(message, username, attachments)
        main_log.debug(f"# Filter result: {filter_result}")
        # If filter returns 1 - we catch something
        if filter_result['result'] == 1:
            main_log.info(f"# Filter result: {filter_result}")
            main_log.info(f"# Message to remove from {username}: '{message}'")
            if cases_log:
                cases_log.info(f"# Message to remove from {username}: '{message}'")

            group_id = response['updates'][0]['group_id']
            cm_id = response['updates'][0]['object']['message']['conversation_message_id']
            peer_id = response['updates'][0]['object']['message']['peer_id']
            main_log.debug(f"# Group ID: {group_id}, CM ID: {cm_id}, Peer ID: {peer_id}")
            delete_result = vk_api.delete_message(group_id, cm_id, peer_id)
            main_log.debug(f"# Delete result: {delete_result['text']}")

            if delete_result['error'] == 0:
                main_log.info("# Message was removed")
                send_result = vk_api.send_message(f"Сообщение от {username} было удалено автоматическим фильтром. Причина: {filter_result['case']}", group_id, chat_id)
            else:
                main_log.error(f"# Message delete error: {delete_result['text']}")
                main_log.info("# Message was not removed")
                send_result = vk_api.send_message(f"# Сообщение от {username} не было удалено автоматическим фильтром.", group_id, chat_id)

            if send_result['error'] == 0:
                main_log.info(f"# Service message was sent to {self.params['VK']['chats'][str(chat_id)]}")
            else:
                main_log.error(f"# Service message send error: {send_result}")
        # If filter returns 2 - we should get warning to Telegram
        if filter_result['result'] == 2:
            main_log.info(f"# Suspicious message from {username}: '{message}' was found.")
            main_log.info(f"# Text: {filter_result['text']}.\n# Case: {filter_result['case']}")
            if cases_log:
                cases_log.info(f"# Suspicious message from {username}: '{message}' was found.")
                cases_log.info(f"# Text: {filter_result['text']}.\n# Case: {filter_result['case']}")


    @logger.catch
    def comment(self, response, vk_api, main_log, cases_log = None):
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
            main_log.info(f"# Filter result: {filter_result}")
            main_log.info(f"# Comment to remove from {username}\n'{message}'")
            if cases_log:
                cases_log.info(f"# Filter result: {filter_result}")
                cases_log.info(f"# Comment to remove from {username}: '{message}'")