# -*- coding: utf-8 -*-
# Reviewed: May 26, 2024
from __future__ import annotations

from aiogram import Bot
from aiogram.methods import SendMessage, DeleteMessage
from loguru import logger
from loguru import logger as tlg_proc_log

from config import Logs
from filter import Filter


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
        # Result = 0 - false
        # Result = 1 - true
        # Result = 2 - suspicious
        self.result = {"result": 0, "text": "", "case": ""}
        return self

    @tlg_proc_log.catch
    async def notify_and_remove(self, message, result, text):
        tlg_proc_log.info(
            f"Message to remove from {message.from_user.first_name}:\n'{text.replace('.', '[.]')}'"
        )
        await self.bot(DeleteMessage(chat_id=message.chat.id, message_id=message.message_id))
        await self.bot(SendMessage(
            chat_id=message.chat.id,
            text=f"Сообщение от {message.from_user.first_name} было удалено автоматическим фильтром.\nПричина: {result['case']}",
        ))

    @tlg_proc_log.catch
    async def moderate_message(self, message) -> None:
        """Moderate message"""

        urls = []

        if message.entities:
            for entity in message.entities:
                urls.append(entity.url)

        if urls != []:
            for url in urls:
                check_url_result = await self.filter.check_for_links(url)

            tlg_proc_log.debug(f"# Filter result: {check_url_result}")
            if check_url_result["result"] == 1:
                await self.notify_and_remove(message, check_url_result["text"])

        tlg_proc_log.debug(
            f"# Text: {message.text or None}, "
            "Caption: {message.caption or None}, "
            "Name: {message.from_user.first_name}, "
            "Login: {message.from_user.username}, "
            "URLS:{urls}, "
            "Chat ID: {message.chat.id}, "
            "Message ID: {message.message_id}"
        )

        check_text_result = None
        if message.text:
            check_text_result = await self.filter.check_text(
                message.text,
                message.from_user.username,
            )
            text = message.text
        if message.caption:
            check_text_result = await self.filter.check_text(
                message.caption,
                message.from_user.username,
            )
            text = message.caption

        if check_text_result:
            tlg_proc_log.debug(f"# Filter result: {check_text_result}")
            if check_text_result["result"] == 1:
                await self.notify_and_remove(message, check_text_result, text)
        else:
            tlg_proc_log.debug("# No check text result.")
