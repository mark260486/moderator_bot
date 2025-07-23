# -*- coding: utf-8 -*-
# Reviewed: July 23, 2025
from __future__ import annotations

import re

from loguru import logger
from loguru import logger as filter_log
from dataclasses import dataclass

from config.logs import Logs
from config.words_db import Words_DB
from config.tlg import Telegram


@dataclass
class Result:
    # Result = 0 - false
    # Result = 1 - true
    # Result = 2 - suspicious

    result: int = 0
    text: str = ""
    case_description: str = ""

    def reset_results(self):
        self.result = 0
        self.text = ""
        self.case_description = ""


class Filter:
    # To avoid async __init__
    @classmethod
    async def create(cls, filter_log: logger = filter_log, debug_enabled: bool = False) -> Filter:  # type: ignore
        """
        Filter class init

        :type aux: ``auxiliary``
        :param aux: Auxiliary class instance.

        :type filter_log: ``logger``
        :param filter_log: Logger instance.

        :type debug_enabled: ``bool``
        :param debug_enabled: Boolean to switch on and off debugging. False by default.

        :return: Returns the class instance.
        """

        self = cls()
        if filter_log is None:
            if debug_enabled:
                filter_log.add(
                    Logs.filter_log,
                    level="DEBUG",
                    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
                )
                filter_log.debug("# Filter class will run in Debug mode.")
            else:
                filter_log.add(
                    Logs.filter_log,
                    level="INFO",
                    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
                )
            self.filter_log = filter_log
        else:
            self.filter_log = filter_log
        self.is_member = True
        self.result_test = Result()
        await self.reset_results()
        return self

    @filter_log.catch
    async def reset_results(self) -> None:
        """
        Filter class method to reset filter results before every check.
        """
        self.result = {"result": 0, "text": "", "case": ""}
        self.result_test.reset_results()
        self.discovered_words = []

    # Message filter. Returns dict with result and text
    @filter_log.catch
    async def filter_response(
        self,
        text: str,
        username: str,
        attachments: str,
        is_member: bool,
    ) -> dict:
        """
        Filter class method to filter provided text and/or attachments.

        :type text: ``str``
        :param text: Text to check.

        :type username: ``str``
        :param username: Username to check.

        :type attachments: ``str``
        :param attachments: Attachments to check.

        :type is_member: ``bool``
        :param is_member: Is user member of the public.

        :return: Returns the result as dictionary.
        :rtype: ``dict``
        """

        self.filter_log.debug(
            "================ Filter response ==================",
        )
        self.filter_log.debug("# Filtering response")
        # Set is_member
        if is_member is not None:
            self.is_member = is_member
        # Attachments checks
        check_attachments_result = await self.check_attachments(
            attachments, username
        )
        if check_attachments_result:
            if check_attachments_result["result"] > 0:
                return check_attachments_result

        # Text check
        check_text_result = await self.check_text(text, username)
        if check_text_result:
            if check_text_result["result"] > 0:
                return check_text_result

        self.result["result"] = 0
        self.result_test.result = 0
        return self.result

    # Check of attachments for links and bad things in repost/reply
    @filter_log.catch
    async def check_attachments(self, attachments: str, username: str) -> dict:
        """
        Filter class method to check attachments.

        :type attachments: ``str``
        :param attachments: Attachments to check.

        :type username: ``str``
        :param username: Username to check.

        :return: Returns the result as dictionary.
        :rtype: ``dict``
        """

        await self.reset_results()
        for attachment in attachments:
            self.filter_log.debug(
                f"# Checking attachment of type {attachment['type']}",
            )
            # Links
            if attachment["type"] == "link":
                for item in Words_DB.blacklists.spam_list:
                    if item in attachment["link"]["url"].lower().replace(
                        " ", ""
                    ):
                        msg = f"Forbidden '{item.replace('.', '[.]')}' from spam list was found in attachment!"
                        self.filter_log.debug(f"# {msg}")
                        self.result["result"] = 1
                        self.result["text"] = msg
                        self.result["case"] = (
                            "подозрительная ссылка, спам, реклама."
                        )
                        return self.result
            # Repost content and Repost comment content
            if (
                attachment["type"] == "wall"
                or attachment["type"] == "wall_reply"
            ):
                key = attachment["type"]
                check_wall_result = await self.check_text(
                    attachment[key]["text"],
                    username,
                )
                if check_wall_result:
                    check_wall_result["case"] += " Вложение."
                    return check_wall_result
        self.result["result"] = 0
        return self.result

    @filter_log.catch
    async def check_text(self, text_to_check: str, username: str) -> dict:
        """
        Filter class method to check text.

        :type text_to_check: ``str``
        :param text_to_check: Text to check.

        :type username: ``str``
        :param username: Username to check.

        :return: Returns the result as dictionary.
        :rtype: ``dict``
        """

        await self.reset_results()
        self.filter_log.debug(f"# # Checking text: {text_to_check}")

        # Spam list check
        spam_list_check = await self.check_for_links(text_to_check)
        if spam_list_check["result"] == 1:
            return spam_list_check

        # Check if message contains mishmash and user name is in English
        if await self.check_for_english(
            text_to_check
        ) and await self.check_for_english(
            username,
        ):
            msg = f"{username} with {text_to_check} was caught."
            self.result["result"] = 2
            self.result["text"] = msg
            self.result["case"] = (
                "сообщение на латинице, имя пользователя на латинице, вероятно, бот."
            )

        # Check for phone numbers
        if await self.check_for_phone(text_to_check):
            msg = f"{username} with {text_to_check} was caught."
            self.result["result"] = 2
            self.result["text"] = msg
            self.result["case"] = "номер телефона в тексте, вероятно, бот."

        # Check for bank card numbers
        if await self.check_for_card(text_to_check):
            msg = f"{username} with {text_to_check} was caught."
            self.result["result"] = 2
            self.result["text"] = msg
            self.result["case"] = "номер банковской карточки в тексте, вероятно, бот."

        # Check if message contains mishmash
        if await self.check_for_english(text_to_check):
            msg = f"{username} with {text_to_check} was caught."
            self.result["result"] = 2
            self.result["text"] = msg
            self.result["case"] = "сообщение на латинице, вероятно, бот."

        # Curses list check
        curses_list_check = await self.check_for_curses(text_to_check)
        if curses_list_check["result"] >= 1:
            return curses_list_check
        elif self.result["result"] == 2:
            return self.result

        # Suspicious words check
        # If we have more than X words - kill it
        suspicious_check_result = await self.check_for_suspicious_words(
            text_to_check
        )
        if suspicious_check_result["result"] > 0:
            return suspicious_check_result

        # Check for scam messages consisting of Telegram prem emoji
        non_text_check_result = await self.check_for_non_text(
            text_to_check = text_to_check
        )
        if non_text_check_result:
            msg = f"{username} with {text_to_check} was caught."
            self.result["result"] = 2
            self.result["text"] = msg
            self.result["case"] = "сообщение, состоящее из эмодзи. Вероятно, бот."
            return self.result

        # If user send a picture and user name is in English - warn me
        # if user_check != [] and attachment_flag:
        #     return False, f"# {username} with attachment was caught"
        self.result["result"] = 0
        return self.result

    @filter_log.catch
    async def check_for_english(self, text_to_check: str) -> bool:
        """
        Filter class method to check text for containing Latinic.

        :type text_to_check: ``str``
        :param text_to_check: Text to check.

        :return: Returns the result as boolean.
        :rtype: ``bool``
        """

        await self.reset_results()
        self.filter_log.debug("# Checking for english")
        if text_to_check:
            text_check = re.findall(r'[A-Za-z].+', text_to_check, re.UNICODE)
            if text_check:
                return True
        else:
            self.filter_log.debug("# Text is None")
        return False

    @filter_log.catch
    async def check_for_suspicious_words(self, text_to_check: str) -> dict:
        """
        Filter class method to check text for suspicious words from according list.

        :type text_to_check: ``str``
        :param text_to_check: Text to check.

        :return: Returns the result as dict.
        :rtype: ``dict``
        """

        await self.reset_results()
        if text_to_check:
            self.filter_log.debug("# # Checking for suspicious words")
            # If we have more than X words - kill it
            max_points = Words_DB.blacklists.suspicious_points_limit
            text_to_check = text_to_check.replace("ё", "е").replace("\n", " ").lower()

            await self.regex_check_findall(Words_DB.blacklists.suspicious_regex, text_to_check=text_to_check)
            if self.discovered_words == []:
                await self.word_check(Words_DB.blacklists.suspicious_list, text_to_check=text_to_check)

            result_len = 0
            if self.discovered_words != []:
                result_len = len(self.discovered_words)
                if not self.is_member:
                    result_len += 1

                if result_len >= max_points:
                    msg = f"Suspicious '{self.discovered_words}' was found.\nMore than {max_points} suspicious words were found."
                    self.filter_log.debug(f"# {msg}")
                    self.result["result"] = 1
                    self.result["text"] = msg
                    self.result["case"] = (
                        "подозрительный набор слов, спам, реклама."
                    )
                    return self.result

                if result_len > 0 and result_len < max_points:
                    if self.discovered_words != []:
                        msg = f"Limit of {max_points} is not exceeded."
                    else:
                        msg = f"Suspicious '{self.discovered_words}' was found. Limit of {max_points} is not exceeded."
                    self.filter_log.debug(f"# {msg}")
                    self.result["result"] = 2
                    self.result["text"] = msg
                    self.result["case"] = (
                        "недостаточно подозрительных слов для удаления сообщения."
                    )
                    return self.result
        else:
            self.filter_log.debug("# Text is None")
        self.result["result"] = 0
        return self.result

    @filter_log.catch
    async def check_for_links(self, text_to_check: str) -> dict:
        """
        Filter class method to check text for links from Spam list.

        :type text_to_check: ``str``
        :param text_to_check: Text to check.

        :return: Returns the result as dictionary.
        :rtype: ``dict``
        """

        await self.reset_results()
        self.filter_log.debug("# Checking for links")
        if text_to_check:
            for item in Words_DB.blacklists.spam_list:
                if item in text_to_check.lower().replace(" ", ""):
                    msg = f"Forbidden '{item.replace('.', '[.]')}' from spam list was found."
                    self.filter_log.debug(f"# {msg}")
                    self.result["result"] = 1
                    self.result["text"] = msg
                    self.result["case"] = "подозрительная ссылка, реклама."
                    return self.result
            self.result["result"] = 0
        else:
            self.filter_log.debug("# Text is None")
        return self.result

    @filter_log.catch
    async def check_for_curses(self, text_to_check: str) -> dict:
        """
        Filter class method to check text for Curses from according list.

        :type text_to_check: ``str``
        :param text_to_check: Text to check.

        :return: Returns the result as dictionary.
        :rtype: ``dict``
        """

        if text_to_check:
            await self.reset_results()
            self.filter_log.debug("# # Checking for curses")
            text_to_check = text_to_check.replace("ё", "е").replace("\n", " ").lower()
            self.filter_log.debug(f"# Text after replacement: {text_to_check}")

            await self.regex_check_findall(Words_DB.blacklists.regex_list, text_to_check=text_to_check)
            if self.discovered_words == []:
                await self.word_check(Words_DB.blacklists.curses_list, text_to_check=text_to_check)

            if self.discovered_words != []:
                msg = f"Forbidden '{self.discovered_words}' from curses list was found."
                self.filter_log.debug(f"# {msg}")
                self.result["result"] = 1
                self.result["text"] = msg
                self.result["case"] = "нецензурные выражения."
                return self.result
        else:
            self.filter_log.debug("# Text is None")
        self.result["result"] = 0
        return self.result

    @filter_log.catch
    async def check_for_whitelist(self, text_to_check: str):
        """
        Filter class method to verify possible false cases of Curses check.

        :type text_to_check: ``str``
        :param text_to_check: Text to check.

        :return: Returns the result as boolean.
        :rtype: ``bool``
        """

        self.filter_log.debug(f"# Checking for whitelist: {text_to_check}")
        if text_to_check:
            for item in Words_DB.whitelists.exclusions:
                pattern = r"(\b\S*%s\S*\b)" % item
                match = re.findall(pattern, text_to_check, re.UNICODE)
                if match:
                    self.filter_log.debug(
                        f"# Whitelist '{item}' was found in '{match}', passing...",
                    )
                    return True
        else:
            self.filter_log.debug("# Text is None")
        self.filter_log.debug("# No whitelist items found")
        return False

    @filter_log.catch
    async def check_for_phone(self, text_to_check: str):
        """
        Filter class method to check text for Phone numbers.

        :type text_to_check: ``str``
        :param text_to_check: Text to check.

        :return: Returns the result as Regex match group or None.
        """

        await self.reset_results()
        self.filter_log.debug("# Checking for phones")
        if text_to_check:
            pattern = (
                r"\+?[0-9]{1}[ ‑\-]?\d{3}[ ‑\-]?\d{3}[ ‑\-]?\d{2}[ ‑\-]?\d{2}"
            )
            match = re.search(pattern, text_to_check)
            if match:
                return match.group()
        else:
            self.filter_log.debug("# Text is None")
        return None

    @filter_log.catch
    async def check_for_card(self, text_to_check: str):
        """
        Filter class method to check text for Bank card numbers - 16 digits.

        :type text_to_check: ``str``
        :param text_to_check: Text to check.

        :return: Returns the result as Regex match group or None.
        """

        await self.reset_results()
        self.filter_log.debug("# Checking for Bank cards")
        if text_to_check:
            pattern = (
                r"\b\d{16}\b"
            )
            match = re.search(pattern, text_to_check)
            if match:
                return match.group()
        else:
            self.filter_log.debug("# Text is None")
        return None

    @filter_log.catch
    async def check_for_non_text(self, text_to_check: str) -> bool:
        """
        Filter class method to check text consisting of emoji packs by Telegram prem.

        :type text_to_check: ``str``
        :param text_to_check: Text to check.

        :return: Returns the result as boolean.
        :rtype: ``bool``
        """

        await self.reset_results()
        self.filter_log.debug("# Checking for emoji scam")
        if text_to_check:
            text_check = re.search(r'[а-яa-z0-9]+', text_to_check, re.UNICODE)
            self.filter_log.debug(f"# Text is {text_check}")
            # if text_check:
            #     if len(text_check) > Telegram.emoji_length_limit:
            #         return True
        else:
            self.filter_log.debug("# Text is None")
        return False

    @filter_log.catch
    async def regex_check_match(self, regex_list, text_to_check: str):
        self.filter_log.debug("# Checking with regex list")
        for regex in regex_list:
            match = re.match(f'\\b\\w*{regex}\\w*\\b', text_to_check, re.UNICODE)
            if match is not None:
                self.filter_log.debug(f"# Regex matches: {match.group()}")
                if not await self.check_for_whitelist(match.group()):
                    self.discovered_words.append(match.group())
                    self.filter_log.debug(f"# Regex results: {self.discovered_words}")
                    return

    @filter_log.catch
    async def regex_check_findall(self, regex_list, text_to_check: str):
        self.filter_log.debug("# Checking with regex list")
        for regex in regex_list:
            matches = re.findall(f'\\b\\w*{regex}\\w*\\b', text_to_check, re.UNICODE)
            if matches:
                self.filter_log.debug(f"# Regex matches: {matches}")
                self.filter_log.debug(f"# Regex: {regex}")
                for match in matches:
                    if not await self.check_for_whitelist(match):
                        self.discovered_words.append(match)
                self.filter_log.debug(f"# Regex results: {self.discovered_words}")
                return

    @filter_log.catch
    async def word_check(self, blacklist, text_to_check):
        self.filter_log.debug("# Checking with words list")
        for item in blacklist:
            # Search all occurences in the text
            matches = re.findall(f'\\w*{item}\\w*', text_to_check, re.UNICODE)
            if matches:
                self.filter_log.debug(f"# Words matches: {matches}")
                # If there any - check whitelist for every cursed word we did found
                self.filter_log.debug(f"# Word check results: {matches}")
                for match in matches:
                    if not await self.check_for_whitelist(match):
                        self.discovered_words += matches
                        self.filter_log.debug(f"# Words results: {self.discovered_words}")
