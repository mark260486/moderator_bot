# -*- coding: utf-8 -*-
# Reviewed: November 12, 2024
from __future__ import annotations

import argparse
import asyncio

from loguru import logger
from notifiers.logging import NotificationHandler
from aiogram import Bot, Dispatcher, types
from aiogram.methods import SendMessage
from aiogram.filters import LEFT, MEMBER, RESTRICTED, KICKED
from aiogram.filters import ChatMemberUpdatedFilter
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import Telegram
from tlg_processing import TLG_processing
from tlg_processing import DB


dp = Dispatcher()
bot = Bot(token=Telegram.tlg_api.api_key, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
global tlg_proc
global db


@dp.chat_member(ChatMemberUpdatedFilter(LEFT >> MEMBER))
async def greet_chat_members(event: types.ChatMemberUpdated) -> None:
    """Greets new users in chats"""
    logger.debug("# Greet chat member")
    logger.debug(f"# Event: {event}")
    logger.debug(f"# Username: {event.new_chat_member.user.first_name}, user ID: {event.new_chat_member.user.id}")
    await bot(SendMessage(chat_id=event.chat.id, text=Telegram.greeting_msg.replace("member_name", event.new_chat_member.user.mention_html())))


@dp.chat_member(ChatMemberUpdatedFilter(MEMBER >> LEFT))
async def bye_chat_members(event: types.ChatMemberUpdated) -> None:
    """Announces when someone leaves"""
    logger.debug("# Chat member leave")
    logger.debug(f"# Event: {event}")
    logger.debug(f"# Username: {event.from_user.first_name}, user ID: {event.from_user.id}")
    await bot(SendMessage(chat_id=event.chat.id, text=Telegram.leave_msg.replace("member_name", event.from_user.mention_html())))


@dp.chat_member(ChatMemberUpdatedFilter(MEMBER >> RESTRICTED))
async def mute_chat_members(event: types.ChatMemberUpdated) -> None:
    """Announces when someone muted/unmuted"""
    logger.debug("# Chat member muted")
    logger.debug(f"# Event: {event}")
    await bot(SendMessage(chat_id=event.chat.id, text=Telegram.mute_msg.replace("member_name", event.old_chat_member.user.mention_html())))


@dp.chat_member(ChatMemberUpdatedFilter((RESTRICTED | KICKED) >> MEMBER))
async def unmute_chat_members(event: types.ChatMemberUpdated) -> None:
    """Announces when someone muted/unmuted"""
    logger.debug("# Chat member unmuted")
    logger.debug(f"# Event: {event}")
    await bot(SendMessage(chat_id=event.chat.id, text=Telegram.unmute_msg_is_member.replace("member_name", event.old_chat_member.user.mention_html())))


@dp.chat_member(ChatMemberUpdatedFilter(MEMBER >> KICKED))
async def ban_chat_members(event: types.ChatMemberUpdated) -> None:
    """Announces when someone banned"""
    logger.debug("# Chat member banned")
    logger.debug(f"# Event: {event}")
    # Removed account ignored
    if event.old_chat_member.user.first_name != '':
        await db.remove_user(user_id = event.from_user.id)
        await bot(SendMessage(chat_id=event.chat.id, text=Telegram.ban_msg
                              .replace("member_name", event.old_chat_member.user.mention_html())
                              .replace("cause_name", event.from_user.first_name)))


@dp.chat_member()
async def chat_members_transitions(event: types.ChatMemberUpdated) -> None:
    """Other transitions debug"""
    logger.debug("# Chat member unmuted")
    logger.debug(f"# Event: {event}")


@dp.message()
@dp.edited_message()
async def user_message(event: types.Message) -> None:
    """New/edited message"""
    logger.debug("# New/edited message")
    logger.debug(f"# Username: {event.from_user.first_name}, user ID: {event.from_user.id}, text: {event.text}")
    # Filtering
    global tlg_proc
    await tlg_proc.moderate_event(event)


@logger.catch
async def main() -> None:
    """Start the bot."""
    # # # # Parsing args # # # #
    parser = argparse.ArgumentParser(
        prog="Telegram Moderator bot",
        description="This script can strictly moderate Telegram chats",
    )

    parser.add_argument(
        "-d",
        "--debug",
        dest="debug_enabled",
        action="store_true",
        default=False,
        required=False,
    )
    parser.add_argument(
        "-t",
        "--tlg",
        dest="send_msg_to_tlg",
        action="store_true",
        help="Send Notification message to moderator Telegram Chat",
        default=False,
        required=False,
    )
    args = parser.parse_args()

    # # # # Logger settings # # # #
    # Need to remove default logger settings
    logger.remove()

    # Logging params
    if args.debug_enabled:
        logger.add(
            Telegram.log_path,
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
            rotation="10 MB",
        )
        logger.debug("# Telegram moderator will run in Debug mode.")
    else:
        logger.add(
            Telegram.log_path,
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
            rotation="10 MB",
        )

    # Telegram messages logging
    if args.send_msg_to_tlg:
        tg_params = {
            "token": Telegram.tlg_api.api_key,
            "chat_id": Telegram.tlg_api.log_chat_id,
        }
        tg_handler = NotificationHandler("telegram", defaults=tg_params)
        logger.add(tg_handler, format="{message}", level="INFO")

    # Processing and filter
    global tlg_proc
    tlg_proc = await TLG_processing.create(bot=bot, debug_enabled=args.debug_enabled)

    # DB connection
    global db
    db = await DB.create()

    logger.info("Telegram moderator bot listener re/starting..")

    # # # # Start Telegram listener # # # #
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
