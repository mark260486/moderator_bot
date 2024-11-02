# -*- coding: utf-8 -*-
# Reviewed: November 02, 2024
from __future__ import annotations

from aiogram import Bot
from aiogram.methods import SendMessage, DeleteMessage, RestrictChatMember
from aiogram.types import chat_permissions
from loguru import logger
from loguru import logger as tlg_proc_log
from loguru import logger as db_int_log
from datetime import timedelta

from config import Logs
from filter import Filter

from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# DB settings
CONNECTION_STRING = "sqlite:////telegram.db"
Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key = True)
    violations = Column(Integer)

    def __repr__(self):
        return f"User name: {self.user_id}, violations: {self.violations}"


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
        # Remove message
        await self.bot(DeleteMessage(chat_id=event.chat.id, message_id=event.message_id))

        # Add to DB and mute
        await self.db.add_user(user_id = event.from_user.id)
        await self.db.increase_violations(user_id = event.from_user.id)
        user = await self.db.get_user(user_id = event.from_user.id)
        if user:
            await self.bot(RestrictChatMember(
                chat_id = event.chat.id,
                user_id = event.from_user.id,
                until_date = timedelta(seconds = 3600 * int(user.violations)),
                permissions = chat_permissions.ChatPermissions(can_send_messages=False,
                                                               can_send_polls=False,
                                                               can_send_other_messages=False,
                                                               can_send_media_messages=False
                                                               )))
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

        urls = []

        if event.entities:
            for entity in event.entities:
                urls.append(entity.url)

        if urls != []:
            for url in urls:
                check_url_result = await self.filter.check_for_links(url)

            tlg_proc_log.debug(f"# Filter result: {check_url_result}")
            if check_url_result["result"] == 1:
                await self.mute_user(event = event, result = check_url_result["text"])

        tlg_proc_log.debug(
            f"# Text: {event.text or None}, "
            f"Caption: {event.caption or None}, "
            f"Name: {event.from_user.first_name}, "
            f"Login: {event.from_user.username}, "
            f"URLS:{urls}, "
            f"Chat ID: {event.chat.id}, "
            f"event ID: {event.message_id}"
        )

        check_text_result = None
        if event.text:
            check_text_result = await self.filter.check_text(
                event.text,
                event.from_user.username,
            )
            text = event.text
        if event.caption:
            check_text_result = await self.filter.check_text(
                event.caption,
                event.from_user.username,
            )
            text = event.caption

        if check_text_result:
            tlg_proc_log.debug(f"# Filter result: {check_text_result}")
            if check_text_result["result"] == 1:
                await self.mute_user(event = event, result = check_text_result, text = text)
        else:
            tlg_proc_log.debug("# No check text result.")


class DB:
    # To avoid async __init__
    @classmethod
    async def create(cls, db_int_log: logger = db_int_log, debug_enabled: bool = False) -> None:  # type: ignore
        """
        Database interaction class init

        :type db_int_log: ``logger``
        :param db_int_log: Logger instance.

        :type debug_enabled: ``bool``
        :param debug_enabled: Boolean to switch on and off debugging. False by default.

        :return: Returns the class instance.
        """

        self = cls()
        if db_int_log is None:
            db_int_log.remove()
            if debug_enabled:
                db_int_log.add(
                    Logs.processing_log,
                    level="DEBUG",
                    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
                )
                db_int_log.debug(
                    "# Database interaction class will run in Debug mode.",
                )
            else:
                db_int_log.add(
                    Logs.processing_log,
                    level="INFO",
                    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
                )
            self.db_int_log = db_int_log
        else:
            self.db_int_log = db_int_log

        # DB Session configuration
        self.engine = create_engine(CONNECTION_STRING)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind = self.engine)
        self.session = Session()
        return self

    @db_int_log.catch
    async def add_user(self, user_id) -> None:
        """Add user to DB"""
        self.db_int_log.debug(f"# Add user {user_id} with 0 violations to DB")
        user_check = await self.get_user(user_id = user_id)
        if user_check == False:
            new_user = Users(user_id = user_id, violations = 0)
            self.session.add(new_user)
            self.session.commit()
        else:
            self.db_int_log.debug(f"# User {user_id} already exists in DB")

    @db_int_log.catch
    async def update_user(self, user_id, violations) -> None:
        """Update user in DB"""
        self.db_int_log.debug(f"# Update user {user_id}")
        user_to_update = self.session.get(Users, user_id)
        user_to_update.violations = violations
        self.session.commit()

    @db_int_log.catch
    async def get_user(self, user_id) -> None:
        """Get user from DB"""
        self.db_int_log.debug(f"# Get user {user_id} from DB")
        # user_check = self.session.query(Users).filter_by(user_id = user_id)
        user_check = self.session.get(Users, user_id)
        if user_check:
            self.db_int_log.debug(f"# DB data: {user_check}")
            return user_check
        self.db_int_log.debug("# No such user")
        return False

    @db_int_log.catch
    async def remove_user(self, user_id) -> None:
        """Remove user from DB"""
        self.db_int_log.debug(f"# Remove user {user_id} from DB")
        user_check = await self.get_user(user_id = user_id)
        if user_check:
            removed_user = self.session.get(Users, user_id)
            self.session.delete(removed_user)
            self.session.commit()

    @db_int_log.catch
    async def increase_violations(self, user_id) -> None:
        """Increase user violations to 1"""
        self.db_int_log.debug(f"# Increase user {user_id} violations")
        user_check = await self.get_user(user_id = user_id)
        if user_check:
            await self.update_user(user_id = user_id, violations = user_check.violations + 1)
            await self.get_user(user_id = user_id)
