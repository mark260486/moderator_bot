# -*- coding: utf-8 -*-
# Reviewed: May 05, 2025
from __future__ import annotations

import argparse
import asyncio
from loguru import logger
from notifiers.logging import NotificationHandler
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import AiogramError
from aiogram.filters import ChatMemberUpdatedFilter
from aiogram.filters import LEFT, MEMBER, RESTRICTED, KICKED
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram.methods import SendMessage, GetChatAdministrators
from aiogram.types import LinkPreviewOptions, chat_permissions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import timedelta

from config.tlg import Telegram
from tlg.processing import TLG_processing
from tlg.db import DB


class captchaDialog(StatesGroup):
    user_answering = State()
    user_answered = State()


class ModeratorBot:
    def __init__(self, bot: Bot, dispatcher: Dispatcher, args: argparse.Namespace):
        self.bot = bot
        self.dp = dispatcher
        self.args = args
        self.user_id = None
        self.message_id = None
        self.tlg_proc = None
        self.db = None

    async def start(self):
        self.tlg_proc = await TLG_processing.create(bot=self.bot, debug_enabled=self.args.debug_enabled)
        self.db = await DB.create()
        logger.info("Telegram moderator bot re/starting..")
        await self.dp.start_polling(self.bot)

    async def greet_new_user(self, event: types.ChatMemberUpdated, state: FSMContext):
        logger.debug("# Greet chat member ========================================"[:70])
        logger.debug(f"# Event: {event}")
        logger.info(f"# Joining username: {event.new_chat_member.user.first_name}, user ID: {event.new_chat_member.user.id}")
        if Telegram.Captcha.Enabled:
            await self.handle_captcha(event, state)
        else:
            await self.send_greeting(event)

    async def handle_captcha(self, event: types.ChatMemberUpdated, state: FSMContext):
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(
            text=Telegram.Captcha.temp_button,
            callback_data="yes"
        ))
        self.user_id = event.new_chat_member.user.id
        logger.debug(f"# New user {event.new_chat_member.user.first_name} was muted until answered to captcha")
        try:
            await self.bot.restrict_chat_member(
                chat_id=event.chat.id,
                user_id=event.new_chat_member.user.id,
                until_date=timedelta(seconds=29),
                permissions=chat_permissions.ChatPermissions(
                    can_send_messages=False,
                    can_send_other_messages=False,
                    can_send_media_messages=False,
                    can_invite_users=False
                )
            )
            await event.answer(Telegram.Captcha.temp_message.replace("member_name", event.new_chat_member.user.first_name),
                               reply_markup=builder.as_markup())
        except AiogramError as e:
            logger.error(f"# Something went wrong: {e}")
        logger.debug("# Waiting for new user input...")
        await state.set_state(captchaDialog.user_answering)
        await asyncio.sleep(Telegram.Captcha.Timeout)
        user_state = await state.get_state()
        if user_state == "captchaDialog:user_answering":
            logger.info(f"# Timeout passed. New user {event.new_chat_member.user.id} remains muted. User ID resetted")
            self.user_id = None
            try:
                await self.bot.delete_message(chat_id=event.chat.id, message_id=self.message_id + 1)
            except AiogramError as e:
                logger.error(f"# Something went wrong: {e}")

    async def send_greeting(self, event: types.ChatMemberUpdated):
        if self.is_supergroup(event):
            try:
                await self.bot(SendMessage(
                    chat_id=event.chat.id,
                    text=Telegram.Messages.Greeting.replace("member_name", event.new_chat_member.user.mention_html()),
                    link_preview_options=LinkPreviewOptions(is_disabled=True)),
                )
            except AiogramError as e:
                logger.error(f"# Something went wrong: {e}")

    async def announce_user_leave(self, event: types.ChatMemberUpdated):
        logger.debug("# Chat member leave ========================================"[:70])
        logger.debug(f"# Event: {event}")
        logger.info(f"# Leaving username: {event.old_chat_member.user.first_name}, user ID: {event.old_chat_member.user.id}")
        if self.is_supergroup(event):
            try:
                await self.bot(SendMessage(
                    chat_id=event.chat.id,
                    text=Telegram.Messages.Leave.replace("member_name", event.old_chat_member.user.mention_html())),
                )
            except AiogramError as e:
                logger.error(f"# Something went wrong: {e}")

    async def announce_user_mute(self, event: types.ChatMemberUpdated):
        if self.user_id == event.old_chat_member.user.id:
            return
        logger.debug("# Chat member muted ========================================"[:70])
        logger.debug(f"# Event: {event}")
        try:
            await self.bot(SendMessage(
                chat_id=event.chat.id,
                text=Telegram.Messages.Mute.replace("member_name", event.old_chat_member.user.mention_html())))
        except AiogramError as e:
            logger.error(f"# Something went wrong: {e}")

    async def announce_user_unmute(self, event: types.ChatMemberUpdated):
        logger.debug("# Chat member unmuted ========================================"[:70])
        logger.debug(f"# Event: {event}")
        try:
            await self.bot(SendMessage(
                chat_id=event.chat.id,
                text=Telegram.Messages.Unmute_is_member.replace("member_name", event.old_chat_member.user.mention_html())))
        except AiogramError as e:
            logger.error(f"# Something went wrong: {e}")

    async def announce_user_ban(self, event: types.ChatMemberUpdated):
        logger.debug("# Chat member banned ========================================"[:70])
        logger.debug(f"# Event: {event}")
        if event.old_chat_member.user.first_name != '':
            await self.db.remove_user(user_id=event.from_user.id)
            try:
                await self.bot(SendMessage(chat_id=event.chat.id, text=Telegram.Messages.Ban
                                           .replace("member_name", event.old_chat_member.user.mention_html())
                                           .replace("cause_name", event.from_user.first_name)))
            except AiogramError as e:
                logger.error(f"# Something went wrong: {e}")

    async def moderate_user_message(self, event: types.Message):
        logger.debug("# New/edited message ========================================"[:70])
        logger.debug(f"# Event: {event}")
        logger.debug(f"# Username: {event.from_user.first_name}, user ID: {event.from_user.id}, text: {event.text}")
        if not self.args.moderate_admins_enabled:
            logger.debug("# Skip admin messages")
            admins_list = await self.get_chat_administrators(chat_id=event.chat.id)
            if admins_list and event.from_user.id in admins_list:
                logger.debug("# Wouldn't moderate this message")
                return
        if event.from_user.id == 777000:
            logger.debug("# Skip Telegram messages")
            return
        if event.from_user.id == self.user_id and event.text is None:
            logger.debug(f"# This is empty message about new user join. Message ID: {event.message_id}")
            self.message_id = event.message_id
        await self.tlg_proc.moderate_event(event)

    async def get_chat_administrators(self, chat_id: int) -> list:
        logger.debug("# Get chat administrators ========================================"[:70])
        admins_list = []
        admins = await self.bot(GetChatAdministrators(chat_id=chat_id))
        for admin in admins:
            admins_list.append(admin.user.id)
        return admins_list if admins_list else None

    def is_supergroup(self, event) -> bool:
        logger.debug("# Check if user join/leave supergroup ========================================"[:70])
        if event.chat.type == "supergroup":
            return True
        return False


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
        help="Send Notification message to moderator Telegram Chat",
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
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
            rotation="1 MB",
            retention=2,
        )
        logger.debug("# Telegram moderator will run in Debug mode.")
    else:
        logger.add(
            Telegram.log_path,
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
            rotation="1 MB",
            retention=2,
        )

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

    @dp.message()
    @dp.edited_message()
    async def moderate_user_message(event: types.Message):
        await moderator_bot.moderate_user_message(event)

    await moderator_bot.start()

if __name__ == "__main__":
    asyncio.run(main())
