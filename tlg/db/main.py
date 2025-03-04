# -*- coding: utf-8 -*-
# Reviewed: March 03, 2024
from __future__ import annotations

from loguru import logger
from loguru import logger as db_int_log

from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.logs import Logs

# DB settings
CONNECTION_STRING = f"sqlite:////{Telegram.tlg_db_path}"
Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    violations = Column(Integer)

    def __repr__(self) -> str:
        return f"User name: {self.user_id}, violations: {self.violations}"


class DB:
    # To avoid async __init__
    @classmethod
    async def create(cls, db_int_log: logger = db_int_log, debug_enabled: bool = False) -> DB:  # type: ignore
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
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        return self

    @db_int_log.catch
    async def add_user(self, user_id: int) -> None:
        """Add user to DB"""
        self.db_int_log.debug(f"# Add user {user_id} with 0 violations to DB")
        user_check = await self.get_user(user_id=user_id)
        if not user_check:
            new_user = Users(user_id=user_id, violations = 0)
            self.session.add(new_user)
            self.session.commit()
        else:
            self.db_int_log.debug(f"# User {user_id} already exists in DB")

    @db_int_log.catch
    async def update_user(self, user_id: int, violations: int) -> None:
        """Update user in DB"""
        self.db_int_log.debug(f"# Update user {user_id}")
        user_to_update = self.session.get(Users, user_id)
        if user_to_update:
            user_to_update.violations = violations
            self.session.commit()

    @db_int_log.catch
    async def get_user(self, user_id: int) -> Users | None:
        """Get user from DB"""
        self.db_int_log.debug(f"# Get user {user_id} from DB")
        # user_check = self.session.query(Users).filter_by(user_id = user_id)
        user_check = self.session.get(Users, user_id)
        if user_check:
            self.db_int_log.debug(f"# DB data: {user_check}")
            return user_check
        self.db_int_log.debug("# No such user")
        return None

    @db_int_log.catch
    async def remove_user(self, user_id: int) -> None:
        """Remove user from DB"""
        self.db_int_log.debug(f"# Remove user {user_id} from DB")
        user_check = await self.get_user(user_id=user_id)
        if user_check:
            removed_user = self.session.get(Users, user_id)
            self.session.delete(removed_user)
            self.session.commit()

    @db_int_log.catch
    async def increase_violations(self, user_id: int) -> None:
        """Increase user violations to 1"""
        self.db_int_log.debug(f"# Increase user {user_id} violations")
        user_check = await self.get_user(user_id=user_id)
        if user_check:
            await self.update_user(user_id=user_id, violations=user_check.violations + 1)
            await self.get_user(user_id=user_id)
