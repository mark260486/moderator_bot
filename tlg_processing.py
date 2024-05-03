# Reviewed: May 03, 2024

from loguru import logger as tlg_proc_log
from loguru import logger
from filter import Filter
from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from typing import Optional, Tuple
from config import Telegram, Logs


text = ""
caption = ""
first_name = ""
username = ""
urls = []


class TLG_processing:
    def __init__(self, tlg_proc_log: logger = tlg_proc_log, debug_enabled: bool = False) -> None: # type: ignore
        """
        Telegram Processing class init

        :type processing_tlg_log: ``logger``
        :param processing_tlg_log: Logger instance.

        :type debug_enabled: ``bool``
        :param debug_enabled: Boolean to switch on and off debugging. False by default.

        :return: Returns the class instance.
        """

        if tlg_proc_log == None:
            tlg_proc_log.remove()
            if debug_enabled:
                tlg_proc_log.add(Logs.processing_log, level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
                tlg_proc_log.debug("# Telegram Processing class will run in Debug mode.")
            else:
                tlg_proc_log.add(Logs.processing_log, level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            self.tlg_proc_log = tlg_proc_log
        else:
            self.tlg_proc_log = tlg_proc_log
        self.filter = Filter(debug_enabled = debug_enabled)
        # Result = 0 - false
        # Result = 1 - true
        # Result = 2 - suspicious
        self.result = {
            'result': 0,
            'text': "",
            'case': ""
        }


    @tlg_proc_log.catch
    def extract_status_change(self, chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
        """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
        of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
        the status didn't change.
        """
        status_change = chat_member_update.difference().get("status")
        old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

        if status_change is None:
            return None

        old_status, new_status = status_change
        was_member = old_status in [
            ChatMember.MEMBER,
            ChatMember.OWNER,
            ChatMember.ADMINISTRATOR,
        ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
        is_member = new_status in [
            ChatMember.MEMBER,
            ChatMember.OWNER,
            ChatMember.ADMINISTRATOR,
        ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

        return was_member, is_member


    @tlg_proc_log.catch
    async def greet_chat_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Greets new users in chats and announces when someone leaves"""
        result = self.extract_status_change(update.chat_member)
        if result is None:
            return

        was_member, is_member = result
        cause_name = update.chat_member.from_user.mention_html()
        member_name = update.chat_member.new_chat_member.user.mention_html()

        msg = ""
        if not was_member and is_member:
            msg = Telegram.greeting_msg.replace("member_name", member_name)
        elif was_member and not is_member:
            if any(admin in cause_name for admin in Telegram.admin_ids):
                msg = Telegram.ban_msg.replace("member_name", member_name).replace("cause_name", cause_name)
                if "><" in member_name:
                    msg = Telegram.clear_msg.replace("cause_name", cause_name)
            else:
                msg = Telegram.leave_msg.replace("member_name", member_name)
        tlg_proc_log.debug(f"Cause name: {cause_name}, member name: {member_name}, msg: {msg}")
        await context.bot.send_message(Telegram.tlg_api.chat_id, msg, parse_mode = ParseMode.HTML)


    @tlg_proc_log.catch
    async def notify_and_remove(self, check_text_result, chat_id, message_id, context: ContextTypes.DEFAULT_TYPE):
        if check_text_result['result'] == 1:
            tlg_proc_log.info(f"Message to remove from {first_name}(@{username}): '{text.replace('.', '[.]')}'")
            reason = check_text_result['case']

            await context.bot.delete_message(chat_id, message_id)
            await context.bot.send_message(Telegram.tlg_api.chat_id,
                                           f"Сообщение от {first_name}(@{username}) было удалено автоматическим фильтром. Причина: {reason}")


    @tlg_proc_log.catch
    async def moderate_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Moderate message"""

        res = update.to_dict()
        tlg_proc_log.debug(f"# Update: {res}")

        # Reset globals for future check
        global text, caption, first_name, username
        text = ""
        caption = ""
        first_name = ""
        username = ""
        urls = []

        message_key = ""
        if "edited_message" in res:
            message_key = "edited_message"
        else:
            message_key = "message"

        if "entities" in res[message_key]:
            for entity in res[message_key]['entities']:
                try:
                    urls.append(entity['url'])
                except: None

        if urls != []:
            for url in urls:
                check_url_result = self.filter.check_for_links(url)

            tlg_proc_log.debug(f"# Filter result: {check_url_result}")
            if check_url_result['result'] == 1:
                tlg_proc_log.info(f"Message to remove from {first_name}(@{username})\n'{text.replace('.', '[.]')}'")
                await context.bot.delete_message(chat_id, message_id)
                await context.bot.send_message(
                    Telegram.tlg_api.chat_id, 
                    f"Сообщение от {first_name}(@{username}) было удалено автоматическим фильтром. Причина: подозрительная ссылка."
                    )

        try:
            text = res[message_key]['text']
        except: None
        try:
            caption = res[message_key]['caption']
        except: None
        try:
            first_name = res[message_key]['from']['first_name']
        except: None
        try:
            username = res[message_key]['from']['username']
        except: None

        chat_id = res[message_key]['chat']['id']
        message_id = res[message_key]['message_id']
        tlg_proc_log.debug(f"# Text: {text}, Caption: {caption}, Name: {first_name}, Login: {username}, URLS: {urls}, Chat ID: {chat_id}, Message ID: {message_id}")

        check_text_result = ""
        if text != "":
            check_text_result = self.filter.check_text(text, username)
        if caption != "":
            check_text_result = self.filter.check_text(caption, username)

        tlg_proc_log.debug(f"# Filter result: {check_text_result}")
        if check_text_result:
            await self.notify_and_remove(check_text_result, chat_id, message_id, context)