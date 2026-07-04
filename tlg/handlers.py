# -*- coding: utf-8 -*-
# Reviewed: June 20, 2026
from __future__ import annotations

import argparse
import asyncio
from loguru import logger
from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import AiogramError
from aiogram.filters import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.methods import SendMessage, DeleteMessage, GetChatAdministrators
from aiogram.types import LinkPreviewOptions, chat_permissions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import timedelta
import re

from config import Telegram
from faq.faq_defs import FaqDef
from tlg.processing import TLG_processing
from tlg.db import DB
from faq import get_local_definition, get_remote_definition


COINCIDENCE_THRESHOLD = 90
DEFINITIONS = FaqDef.DEFINITIONS


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
        # logger.debug(f"# Event: {event}")
        logger.debug(f"# Joining username: {event.new_chat_member.user.first_name}, user ID: {event.new_chat_member.user.id}")
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
        # logger.debug(f"# Event: {event}")
        logger.debug(f"# Leaving username: {event.old_chat_member.user.first_name}, user ID: {event.old_chat_member.user.id}")
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
        # logger.debug(f"# Event: {event}")
        try:
            await self.bot(SendMessage(
                chat_id=event.chat.id,
                text=Telegram.Messages.Mute.replace("member_name", event.old_chat_member.user.mention_html())))
        except AiogramError as e:
            logger.error(f"# Something went wrong: {e}")

    async def announce_user_unmute(self, event: types.ChatMemberUpdated):
        logger.debug("# Chat member unmuted ========================================"[:70])
        # logger.debug(f"# Event: {event}")
        try:
            await self.bot(SendMessage(
                chat_id=event.chat.id,
                text=Telegram.Messages.Unmute_is_member.replace("member_name", event.old_chat_member.user.mention_html())))
        except AiogramError as e:
            logger.error(f"# Something went wrong: {e}")

    async def announce_user_ban(self, event: types.ChatMemberUpdated):
        logger.debug("# Chat member banned ========================================"[:70])
        # logger.debug(f"# Event: {event}")
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

        # Suppose we get Frequently Asked Questions
        # If it's not in local FAQ definitions, checking remote
        if Telegram.FAQ.local_faq_enabled:
            if event.text:
                faq_answer = await self.check_faq(event.text)
                if not faq_answer and Telegram.FAQ.remote_faq_enabled:
                    logger.debug("# No matching local FAQ found. Trying remote...")
                    faq_answer = await self.check_remote_faq(event.text)
                if faq_answer:
                    faq_answer = faq_answer.replace(";", "")
                    await self.bot(SendMessage(
                        chat_id = event.chat.id,
                        text = faq_answer,
                        reply_to_message_id = event.message_id,
                    ))

        if not self.args.moderate_admins_enabled or Telegram.Settings.moderate_admins_enabled:
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

    async def check_faq(self, message: str) -> str | None:
        logger.debug("# Check local FAQ ========================================"[:70])
        answer = get_local_definition(message)
        if answer:
            logger.debug(f"# Found answer for: '{message}'")
            return answer

        # If it's not found directly, we'll try to go through aliases for debugging.
        for term_key, term_data in DEFINITIONS.items():
            for alias in term_data.get("aliases", []):
                if alias.lower() == message.lower():
                    logger.debug(f"# Exact alias match found: '{alias}' for term '{term_key}'")
                    return get_local_definition(alias)
        return None

    async def check_remote_faq(self, message: str) -> str | None:
        logger.debug("# Check remote FAQ ========================================"[:70])
        answer = get_remote_definition(message)
        if answer:
            logger.debug(f"# Found answer for: '{message}'")
            return answer
        return None

    async def handle_bot_commands(self, event: types.Message, command: CommandObject, args: list):
        if Telegram.Settings.bot_commands_enabled:
            logger.debug("# Bot command received ========================================"[:70])
            admins_list = await self.get_chat_administrators(chat_id=event.chat.id)
            if admins_list and event.from_user.id in admins_list:
                logger.debug(f"# Admin command: {command}, args: {args}")
                mute_commands = ["mute", "мут"]
                if command.command in mute_commands:
                    # Default in minutes
                    time_to_mute = re.search(r'\d+', args) if args else None
                    reason_to_mute = re.search(r'\s([А-Яа-я ]+)', args) if len(args) > 1 else None
                    await self.tlg_proc.mute_user(
                        event=event,
                        time_to_mute=time_to_mute.group() if time_to_mute else None,
                        text=reason_to_mute.group() if reason_to_mute else None
                    )
                # elif command.command == "ban":
                #     await self.tlg_proc.ban_user(event, args)
            else:
                logger.debug("# User is not an admin. Deleting message.")
                await self.bot(DeleteMessage(chat_id=event.chat.id, message_id=event.message_id))
