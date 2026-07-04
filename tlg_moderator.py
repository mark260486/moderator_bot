# -*- coding: utf-8 -*-
# Reviewed: July 04, 2026
from __future__ import annotations

import argparse
import asyncio
from loguru import logger
from notifiers.logging import NotificationHandler
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import ChatMemberUpdatedFilter
from aiogram.filters import Command, CommandObject
from aiogram.filters import LEFT, MEMBER, RESTRICTED, KICKED
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy

from config.tlg import Telegram
from tlg.handlers import ModeratorBot


async def main() -> None:
    parser = argparse.ArgumentParser(
        prog="Telegram Moderator bot",
        description="This script can strictly moderate Telegram chats",
    )
    parser.add_argument(
        "-d", "--debug", dest="debug_enabled",
        action="store_true",
        default=False,
        required=False,
    )
    parser.add_argument(
        "-t", "--tlg", dest="send_msg_to_tlg",
        action="store_true",
        help="Send Notification messages to moderator Telegram Chat",
        default=False,
        required=False,
    )
    parser.add_argument(
        "-m", "--moderate", dest="moderate_admins_enabled",
        action="store_true",
        help="If set admins messages shall be checked too",
        default=False,
        required=False,
    )
    args = parser.parse_args()

    logger.remove()
    if args.debug_enabled:
        logger.add(
            Telegram.log_path,
            level="DEBUG" if args.debug_enabled else "INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
            rotation="1 MB",
            retention=2,
        )
        logger.debug("# Telegram moderator will run in Debug mode.")

    if args.send_msg_to_tlg:
        tg_params = {
            "token": Telegram.tlg_api.api_key,
            "chat_id": Telegram.tlg_api.log_chat_id,
        }
        tg_handler = NotificationHandler("telegram", defaults=tg_params)
        logger.add(tg_handler, format="{message}", level="INFO")

    bot = Bot(token=Telegram.tlg_api.api_key, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage(), fsm_strategy=FSMStrategy.CHAT)
    moderator_bot = ModeratorBot(bot, dp, args)

    @dp.chat_member(ChatMemberUpdatedFilter(LEFT >> MEMBER))
    @logger.catch()
    async def chat_member_greet(event: types.ChatMemberUpdated, state: FSMContext):
        await moderator_bot.greet_new_user(event, state)

    @dp.chat_member(ChatMemberUpdatedFilter((RESTRICTED | MEMBER) >> LEFT))
    @logger.catch()
    async def chat_member_bye(event: types.ChatMemberUpdated):
        await moderator_bot.announce_user_leave(event)

    @dp.chat_member(ChatMemberUpdatedFilter(MEMBER >> RESTRICTED))
    async def chat_member_mute(event: types.ChatMemberUpdated):
        await moderator_bot.announce_user_mute(event)

    @dp.chat_member(ChatMemberUpdatedFilter((RESTRICTED | KICKED) >> MEMBER))
    async def chat_member_unmute(event: types.ChatMemberUpdated):
        await moderator_bot.announce_user_unmute(event)

    @dp.chat_member(ChatMemberUpdatedFilter((RESTRICTED | MEMBER) >> KICKED))
    async def chat_member_ban(event: types.ChatMemberUpdated):
        await moderator_bot.announce_user_ban(event)

    @dp.message(Command("mute"))
    async def handle_bot_commands(event: types.Message, command: CommandObject):
        args = command.args
        await moderator_bot.handle_bot_commands(event, command, args)

    @dp.message()
    @dp.edited_message()
    async def moderate_user_message(event: types.Message):
        await moderator_bot.moderate_user_message(event)


    await moderator_bot.start()

if __name__ == "__main__":
    asyncio.run(main())
