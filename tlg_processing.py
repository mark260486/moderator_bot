# Reviewed: May 16, 2024

from loguru import logger as tlg_proc_log
from loguru import logger
from filter import Filter
from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from typing import Optional, Tuple
from config import Telegram, Logs


class TLG_processing:
    def __init__(self, tlg_proc_log: logger = tlg_proc_log, debug_enabled: bool = False) -> None:  # type: ignore
        """
        Telegram Processing class init

        :type processing_tlg_log: ``logger``
        :param processing_tlg_log: Logger instance.

        :type debug_enabled: ``bool``
        :param debug_enabled: Boolean to switch on and off debugging. False by default.

        :return: Returns the class instance.
        """

        if tlg_proc_log is None:
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
        was_muted = False
        if update.chat_member.old_chat_member.status == ChatMember.MEMBER:
            was_muted = True
        cause_name = update.chat_member.from_user.mention_html()
        member_name = update.chat_member.new_chat_member.user.mention_html()

        tlg_proc_log.debug(f"# Update for user greeting: {update}")

        msg = None
        # Greeting message
        if not was_member and is_member:
            msg = Telegram.greeting_msg.replace("member_name", member_name)
        elif was_member and not is_member:
            if any(admin in cause_name for admin in Telegram.admin_ids):
                # Ban message
                msg = Telegram.ban_msg.replace("member_name", member_name).replace("cause_name", cause_name)
                # Remove "Deleted account" message
                if "><" in member_name:
                    msg = Telegram.clear_msg.replace("cause_name", cause_name)
            else:
                # Leave message
                msg = Telegram.leave_msg.replace("member_name", member_name)
        # Mute message
        elif was_member and is_member and was_muted:
            msg = Telegram.mute_msg.replace("member_name", member_name)
        # Unmute message
        # is_member can be in two states: True if user still here and False if user leave while was muted.
        elif was_member and is_member and not was_muted:
            msg = Telegram.unmute_msg_is_member.replace("member_name", member_name)
        elif was_member and not is_member and not was_muted:
            msg = Telegram.unmute_msg_was_member.replace("member_name", member_name)

        tlg_proc_log.debug(f"Cause name: {cause_name}, member name: {member_name}, msg: {msg}")
        if msg:
            await context.bot.send_message(update.chat_member.chat.id, msg, parse_mode = ParseMode.HTML)

    @tlg_proc_log.catch
    async def notify_and_remove(self, check_result, text, message, context: ContextTypes.DEFAULT_TYPE):
        # Compose message for notification
        div = "-----------------------------"
        msg_main = f"# Message to remove from {message.from_user.first_name}(@{message.from_user.username}):\n \
                    '{text.replace('.', '[.]').replace(':', '[:]')}'."
        words = check_result['text']
        case = f"# Case: {check_result['case']}"
        msg = f"{msg_main}\n{div}\n# {words}\n{div}\n{case}"
        tlg_proc_log.info(msg)

        await context.bot.delete_message(message.chat_id, message.message_id)
        await context.bot.send_message(message.chat_id, msg)

    @tlg_proc_log.catch
    async def moderate_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Moderate message"""

        res = update.to_dict()
        tlg_proc_log.debug(f"# Update: {res}")

        urls = []
        message = update.message or update.edited_message

        if message:
            if message.entities:
                for entity in message.entities:
                    urls.append(entity.url)

            if urls != []:
                for url in urls:
                    check_url_result = self.filter.check_for_links(url)

                tlg_proc_log.debug(f"# Filter result: {check_url_result}")
                if check_url_result['result'] == 1:
                    tlg_proc_log.info(f"Message to remove from {message.from_user.first_name}(@{message.from_user.username})\n \
                                    '{check_url_result['text'].replace('.', '[.]')}'")
                    await context.bot.delete_message(message.chat.id, message.message_id)
                    await context.bot.send_message(
                        message.chat_id,
                        f"Сообщение от {message.from_user.first_name}(@{message.from_user.username}) \
                            было удалено автоматическим фильтром. Причина: подозрительная ссылка.")

            tlg_proc_log.debug(
                f"# Text: {message.text or None}, \
                    Caption: {message.caption or None}, \
                    Name: {message.from_user.first_name}, \
                    Login: {message.from_user.username}, \
                    URLS:{urls}, \
                    Chat ID: {message.chat_id}, \
                    Message ID: {message.message_id}")

            check_text_result = None
            if message.text:
                check_text_result = self.filter.check_text(message.text, message.from_user.username)
                text = message.text
            if message.caption:
                check_text_result = self.filter.check_text(message.caption, message.from_user.username)
                text = message.caption

            if check_text_result:
                tlg_proc_log.debug(f"# Filter result: {check_text_result}")
                if check_text_result['result'] == 1:
                    await self.notify_and_remove(check_text_result, text, message, context)
            else:
                tlg_proc_log.debug("No check text result.")
