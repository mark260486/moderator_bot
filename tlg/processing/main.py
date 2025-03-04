# -*- coding: utf-8 -*-
# Reviewed: March 03, 2025
from __future__ import annotations

from aiogram import Bot
from aiogram.methods import SendMessage, DeleteMessage, RestrictChatMember
from aiogram.types import chat_permissions
from loguru import logger
from loguru import logger as tlg_proc_log
from datetime import timedelta

from config.logs import Logs
from filter import Filter
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

        # Result = 0 - false
        # Result = 1 - true
        # Result = 2 - suspicious
        self.result = {"result": 0, "text": "", "case": ""}
        return self

    @tlg_proc_log.catch
    async def mute_user(self, event, result, text) -> None:
        """Mute user and notify"""
        # Remove message
        await self.bot(DeleteMessage(chat_id=event.chat.id, message_id=event.message_id))

        # Add to DB and mute
        await self.db.add_user(user_id=event.from_user.id)
        await self.db.increase_violations(user_id=event.from_user.id)
        user = await self.db.get_user(user_id=event.from_user.id)
        if user:
            await self.bot(RestrictChatMember(
                chat_id=event.chat.id,
                user_id=event.from_user.id,
                until_date=timedelta(seconds=3600 * int(user.violations)),
                permissions=chat_permissions.ChatPermissions(
                    can_send_messages=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_send_media_messages=False
                )
            ))
        # Notify
            # Compose message for notification
            div = "-----------------------------"
            msg_main = f"# Message to remove from {event.from_user.first_name}:\n# '{text.replace('.', '[.]').replace(':', '[:]')}'."
            words = result["text"]
            case = f"# Case: {result['case']}"
            msg = f"{msg_main}\n{div}\n# {words}\n{div}\n{case}"
            tlg_proc_log.info(msg)
            await self.bot(SendMessage(
                chat_id=event.chat.id,
                text=f"Предупреждение {event.from_user.first_name} за нарушение: {result['case']}\nНарушений: {user.violations}.\nОтправка сообщений ограничена на {user.violations} час(а)",
            ))

    @tlg_proc_log.catch
    async def moderate_event(self, event) -> None:
        """Moderate event"""

        urls = [entity.url for entity in event.entities] if event.entities else []

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
