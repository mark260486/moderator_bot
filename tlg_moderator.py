# -*- coding: utf-8 -*-
# Reviewed: November 21, 2024
from __future__ import annotations

import argparse
import asyncio
from loguru import logger
from notifiers.logging import NotificationHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.methods import SendMessage
from aiogram.types import LinkPreviewOptions, chat_permissions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.strategy import FSMStrategy
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import LEFT, MEMBER, RESTRICTED, KICKED
from aiogram.filters import ChatMemberUpdatedFilter
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from datetime import timedelta
from config import Telegram
from tlg_processing import TLG_processing
from tlg_processing import DB


dp = Dispatcher(storage=MemoryStorage(), fsm_strategy=FSMStrategy.CHAT)
bot = Bot(token=Telegram.tlg_api.api_key, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
user_id = ""        # Global for User ID in captcha checks
global tlg_proc     # Telegram processing
global db           # Database with violating users


class captchaDialog(StatesGroup):
    user_answering = State()
    user_answered = State()


@dp.chat_member(ChatMemberUpdatedFilter(LEFT >> MEMBER))
async def chat_member_greet(event: types.ChatMemberUpdated, state: FSMContext) -> None:
    """Greets new users in chats"""
    logger.debug("# Greet chat member")
    logger.debug(f"# Event: {event}")
    logger.debug(f"# Username: {event.new_chat_member.user.first_name}, user ID: {event.new_chat_member.user.id}")
    # Ask user if use is a human
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Да",
        callback_data="yes"
    ))
    global user_id
    user_id = event.new_chat_member.user.id
    # Mute new user till answer
    logger.debug(f"# New user {event.new_chat_member.user.first_name} was muted until answered to captcha")
    await bot.restrict_chat_member(
        chat_id = event.chat.id,
        user_id = event.new_chat_member.user.id,
        until_date = timedelta(seconds = 29),   # 29 seconds means forever
        permissions = chat_permissions.ChatPermissions(
            can_send_messages=False,
            can_send_other_messages=False,
            can_send_media_messages=False,
            can_invite_users=False
        )
    )
    await event.answer("Вы человек?", reply_markup=builder.as_markup())
    logger.debug("# Waiting for new user input...")
    await state.set_state(captchaDialog.user_answering)
    await asyncio.sleep(Telegram.captcha_timeout)
    # Check if new user still answering and mute forever if is
    user_state = await state.get_state()
    if user_state == "captchaDialog:user_answering":
        logger.debug("# Timeout passed. New user muted")
    # await bot.delete_message(chat_id=event.chat.id, message_id=event.message_id)


@dp.chat_member(ChatMemberUpdatedFilter((RESTRICTED | MEMBER) >> LEFT))
async def chat_member_bye(event: types.ChatMemberUpdated) -> None:
    """Announces when someone leaves"""
    logger.debug("# Chat member leave")
    logger.debug(f"# Event: {event}")
    logger.debug(f"# Username: {event.user.first_name}, user ID: {event.user.id}")
    await bot(SendMessage(
        chat_id=event.chat.id,
        text=Telegram.leave_msg.replace("member_name", event.user.mention_html())))


@dp.chat_member(ChatMemberUpdatedFilter(MEMBER >> RESTRICTED))
async def chat_member_mute(event: types.ChatMemberUpdated) -> None:
    """Announces when someone muted/unmuted"""
    # If it is new user, do not announce
    if user_id == event.old_chat_member.user.id:
        return
    logger.debug("# Chat member muted")
    logger.debug(f"# Event: {event}")
    await bot(SendMessage(
        chat_id=event.chat.id,
        text=Telegram.mute_msg.replace("member_name", event.old_chat_member.user.mention_html())))


@dp.chat_member(ChatMemberUpdatedFilter((RESTRICTED | KICKED) >> MEMBER))
async def chat_member_unmute(event: types.ChatMemberUpdated) -> None:
    """Announces when someone muted/unmuted"""
    logger.debug("# Chat member unmuted")
    logger.debug(f"# Event: {event}")
    await bot(SendMessage(
        chat_id=event.chat.id,
        text=Telegram.unmute_msg_is_member.replace("member_name", event.old_chat_member.user.mention_html())))


@dp.chat_member(ChatMemberUpdatedFilter((RESTRICTED | MEMBER) >> KICKED))
async def chat_member_ban(event: types.ChatMemberUpdated) -> None:
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
async def chat_member_transitions(event: types.ChatMemberUpdated) -> None:
    """Other transitions debug"""
    # Find filter for automatic unmute. Such type of transition currently does not catched
    logger.debug("# Chat member transition")
    logger.debug(f"# Event: {event}")


@dp.message()
@dp.edited_message()
async def moderate_user_message(event: types.Message) -> None:
    """New/edited message"""
    logger.debug("# New/edited message")
    logger.debug(f"# Username: {event.from_user.first_name}, user ID: {event.from_user.id}, text: {event.text}")
    if event.text is None:
        logger.debug("# User entered chat | User leaved chat")
    # Filtering
    global tlg_proc
    await tlg_proc.moderate_event(event)


@dp.callback_query(F.data == "yes")
async def callback_handler_human_answer(callback: types.CallbackQuery, state: FSMContext):
    """New user pressed Yes in 'Captcha'"""
    logger.debug("# User pressed 'Yes'")
    # Check for user ID in 'Captcha' test
    # user_id = dp.storage.get_data(user_storage_key)['user']
    logger.debug(f"# User ID: {user_id}")
    if user_id != callback.from_user.id:
        await callback.answer("Это не ваша кнопка :)", show_alert=True)
        logger.debug("# This is not new user")
        return
    logger.debug(f"# Callback: {callback}")
    logger.debug(f"# Username: {callback.from_user.first_name}, user ID: {callback.from_user.id}")
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    logger.debug(f"# New user {callback.from_user.first_name} was unmuted after captcha test")
    await state.set_state(captchaDialog.user_answered)
    await bot.restrict_chat_member(
        chat_id = callback.message.chat.id,
        user_id = callback.from_user.id,
        until_date = timedelta(seconds = 45),   # Unmute user
        permissions = chat_permissions.ChatPermissions(
            can_send_messages=True,
            can_send_other_messages=True,
            can_send_media_messages=True,
            can_invite_users=True
        )
    )
    await bot(SendMessage(
        chat_id=callback.message.chat.id,
        text=Telegram.greeting_msg.replace("member_name", callback.from_user.mention_html()),
        link_preview_options=LinkPreviewOptions(is_disabled=True)))


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
