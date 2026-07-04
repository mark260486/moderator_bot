# -*- coding: utf-8 -*-
# Reviewed: July 04, 2026
from __future__ import annotations
from typing import Any

from aiogram import Bot
from aiogram import types
from aiogram.methods import SendMessage, DeleteMessage, RestrictChatMember
from aiogram.types import chat_permissions
from loguru import logger
from loguru import logger as tlg_proc_log
from datetime import timedelta

from config.logs import Logs
from filter import Filter
from config.tlg import Telegram
from tlg.db.main import DB
class TLG_processing:
    # To avoid async __init__
    @classmethod
    async def create(cls, bot: Bot, tlg_proc_log: logger = tlg_proc_log, debug_enabled: bool = False) -> None:  # type: ignore
        """
        Telegram Processing class init

        :type processing_tlg_log: ``logger``
        :param processing_tlg_log: Logger instance.

        :type debug_enabled: ``bool``
        :param debug_enabled: Boolean to switch on and off debugging. False by default.

        :return: Returns the class instance.
        """

        self = cls()
        self.bot = bot
        if tlg_proc_log is None:
            tlg_proc_log.remove()
            if debug_enabled:
                tlg_proc_log.add(
                    Logs.processing_log,
                    level="DEBUG",
                    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
                )
                tlg_proc_log.debug(
                    "# Telegram Processing class will run in Debug mode.",
                )
            else:
                tlg_proc_log.add(
                    Logs.processing_log,
                    level="INFO",
                    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
                )
            self.tlg_proc_log = tlg_proc_log
        else:
            self.tlg_proc_log = tlg_proc_log
        self.filter = await Filter.create(debug_enabled=debug_enabled)
        self.db = await DB.create(debug_enabled=debug_enabled)

        # Result=0 - false
        # Result=1 - true
        # Result=2 - suspicious
        self.result = {"result": 0, "text": "", "case": ""}
        return self

    @tlg_proc_log.catch
    async def mute_user(
        self,
        event: types.Message,
        result: dict = None,
        text: str = "нарушение правил чата",
        time_to_mute: int = 60,
    ) -> None:
        """
        If this is the first violation in 24 hours, add user to warned DB and send warning message.
        If this is the second violation, add user to muted DB, restrict permissions and send mute message.
        If this is human moderator mute, add user to muted DB, restrict permissions and send mute message.
        """
        # DB manipulations with warned and muted users
        await self.db.add_user(user_id=event.from_user.id)
        await self.db.increase_violations(user_id=event.from_user.id)
        user = await self.db.get_user(user_id=event.from_user.id)
        if user:
            # Human moderator mute user
            if result is None:
                await self.restrict_user(
                    chat_id = event.chat.id,
                    user_id = event.reply_to_message.from_user.id,
                    duration=int(time_to_mute)
                )
                # Notify user about mute
                time_formatted = await self.format_time(int(time_to_mute))
                await self.bot(SendMessage(
                    chat_id=event.chat.id,
                    text=(
                        f"Модератор {event.from_user.first_name} заразил молчанкой {event.reply_to_message.from_user.first_name} за {text}.\n"
                        f"Нарушений: {user.violations}.\nОтправка сообщений ограничена на {time_formatted}"
                    ),
                ))
                # Compose message for admins notification
                div = "-----------------------------"
                msg_main = f"# Модератор {event.from_user.first_name} наконец-то заткнул рот {event.reply_to_message.from_user.first_name}."
                case = f"# Причина: {text}"
                time = f"# Время: {time_formatted}"
                msg = f"{msg_main}\n{div}\n{time}\n{div}\n{case}"
                tlg_proc_log.info(msg)
            else:
                # Remove message
                await self.bot(DeleteMessage(chat_id=event.chat.id, message_id=event.message_id))
                # Notify user about warning
                if user.violations == 1 and Telegram.no_mute_first_violation:
                    if event.from_user.username == "None":
                        text = f"Предупреждение {event.from_user.first_name} за нарушение: {result['case']}\n"
                    else:
                        text = f"Предупреждение @{event.from_user.username} за нарушение: {result['case']}\n"
                    text = text + "При повторном нарушении вы получите мут."
                    await self.bot(SendMessage(
                        chat_id=event.chat.id,
                        text=text,
                    ))
                else:
                    await self.restrict_user(event=event, duration=60 * user.violations)
                    # Notify user about mute
                    time_formatted = await self.format_time(60 * user.violations)
                    await self.bot(SendMessage(
                        chat_id=event.chat.id,
                        text=(
                            f"Предупреждение @{event.from_user.username} за нарушение: {result['case']}\n"
                            # f"Текст: {text.replace(result['findings'][0], '*****')}\n"
                            f"Нарушений: {user.violations}.\nОтправка сообщений ограничена на {time_formatted}"
                        ),
                    ))
                # Compose message for admins notification
                div = "-----------------------------"
                text = text.replace('.', '[.]').replace(':', '[:]')
                msg_main = f"# Нехорошее сообщение от {event.from_user.first_name}:\n# '{text}'."
                words = result["text"]
                case = f"# Причина: {result['case']}"
                msg = f"{msg_main}\n{div}\n# {words}\n{div}\n{case}"
                tlg_proc_log.info(msg)

    @tlg_proc_log.catch
    async def moderate_event(self, event: types.Message) -> None:
        """Moderate event"""

        urls = [entity.url for entity in event.entities] if event.entities else []

        check_url_result = None
        for url in urls:
            check_url_result = await self.filter.check_for_links(url)
            tlg_proc_log.debug(f"# Filter result: {check_url_result}")

        if check_url_result:
            if check_url_result["result"] == 1:
                await self.mute_user(event=event, result=check_url_result["text"])

        tlg_proc_log.debug(
            f"# Text: {event.text or None}, "
            f"Caption: {event.caption or None}, "
            f"Name: {event.from_user.first_name}, "
            f"Login: {event.from_user.username}, "
            f"URLS: {urls}, "
            f"Chat ID: {event.chat.id}, "
            f"Event ID: {event.message_id}"
        )

        check_text_result = None
        text = event.text or event.caption
        if text:
            check_text_result = await self.filter.check_text(text, event.from_user.username)

        if check_text_result:
            tlg_proc_log.debug(f"# Filter result: {check_text_result}")
            if check_text_result["result"] == 1:
                await self.mute_user(event=event, result=check_text_result, text=text)
        else:
            tlg_proc_log.debug("# No check text result.")

    @tlg_proc_log.catch
    async def restrict_user(
        self,
        user_id: int,
        chat_id: int,
        duration: int, # In minutes!
    ) -> None:
        """
        Restrict user permissions in the chat.

        :param event: The message event containing the user to restrict.
        :param duration: The duration of the restriction in seconds.
        """
        await self.bot(RestrictChatMember(
            chat_id=chat_id,
            user_id=user_id,
            until_date=timedelta(seconds=duration * 60),  # Convert minutes to seconds
            permissions=chat_permissions.ChatPermissions(
                can_send_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_send_media_messages=False
            )
        ))

    @tlg_proc_log.catch
    async def format_time(self, total_minutes: int) -> str:
        total_minutes = int(total_minutes)
        if total_minutes < 0:
            return "0 минут"

        hours = total_minutes // 60
        minutes = total_minutes % 60

        def get_noun_case(num: int, singular: str, genitive_sing: str, genitive_plur: str) -> str:
            if 11 <= num % 100 <= 19:
                return genitive_plur
            remainder = num % 10
            if remainder == 1:
                return singular
            if 2 <= remainder <= 4:
                return genitive_sing
            return genitive_plur

        result = []
        if hours > 0:
            h_word = get_noun_case(hours, "час", "часа", "часов")
            result.append(f"{hours} {h_word}")
        if minutes > 0 or not result:
            m_word = get_noun_case(minutes, "минута", "минуты", "минут")
            result.append(f"{minutes} {m_word}")
        return " ".join(result)
