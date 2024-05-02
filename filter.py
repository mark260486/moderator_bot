# Reviewed: April 23, 2024

import re
from loguru import logger
import auxiliary


class filter:
    def __init__(self, aux: auxiliary, filter_logger: logger = None, debug_enabled: bool = False) -> None: # type: ignore
        """
        Filter class init

        :type aux: ``auxiliary``
        :param aux: Auxiliary class instance.

        :type filter_logger: ``logger``
        :param filter_logger: Logger instance.

        :type debug_enabled: ``bool``
        :param debug_enabled: Boolean to switch on and off debugging. False by default.

        :return: Returns the class instance.
        """

        self.params = aux.read_config()
        self.aux = aux
        if filter_logger == None:
            logger.remove()
            if debug_enabled:
                logger.add(self.params['filter_log'], level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            else:
                logger.add(self.params['filter_log'], level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            self.logger = logger
        else:
            self.logger = filter_logger
        self.reset_results()


    @logger.catch
    def reset_results(self):
        """
        Filter class method to reset filter results before every check.
        """
        # Result = 0 - false
        # Result = 1 - true
        # Result = 2 - suspicious
        self.result = {
            'result': 0,
            'text': "",
            'case': ""
        }


    # Message filter. Returns true if message contains anything illegal
    @logger.catch
    def filter_response(self, text: str, username: str, attachments: str) -> dict:
        """
        Filter class method to filter provided text and/or attachments.

        :type text: ``str``
        :param text: Text to check.

        :type username: ``str``
        :param username: Username to check.

        :type attachments: ``str``
        :param attachments: Attachments to check.

        :return: Returns the result as dictionary.
        :rtype: ``dict``
        """

        self.logger.debug(f"================ Filter response ==================")
        self.logger.debug("# Filtering response")
        # Attachments checks
        check_attachments_result = self.check_attachments(attachments, username)
        if check_attachments_result:
            if check_attachments_result['result'] > 0:
                return check_attachments_result

        # Text check
        check_text_result = self.check_text(text, username)
        if check_text_result:
            if check_text_result['result'] > 0:
                return check_text_result

        self.result['result'] = 0
        return self.result


    # Check of attachments for links and bad things in repost/reply
    @logger.catch
    def check_attachments(self, attachments: str, username: str) -> dict:
        """
        Filter class method to check attachments.

        :type attachments: ``str``
        :param attachments: Attachments to check.

        :type username: ``str``
        :param username: Username to check.

        :return: Returns the result as dictionary.
        :rtype: ``dict``
        """

        self.reset_results()
        for attachment in attachments:
            self.logger.debug(f"Checking attachment of type {attachment['type']}")
            # Links
            if attachment['type'] == "link":
                for item in self.params['word_db']['blacklist']['spam_list']:
                    if item in attachment['link']['url'].lower().replace(" ", ""):
                        msg = f"Forbidden '{item.replace('.', '[.]')}' from spam list was found in attachment!"
                        self.logger.debug(f"# {msg}")
                        self.result['result'] = 1
                        self.result['text'] = msg
                        self.result['case'] = "подозрительная ссылка, спам, реклама."
                        return self.result
            # Repost content and Repost comment content
            if attachment['type'] == "wall" or attachment['type'] == "wall_reply":
                key = attachment['type']
                check_wall_result = self.check_text(attachment[key]['text'], username)
                if check_wall_result:
                    check_wall_result['case'] += " Вложение."
                    return check_wall_result
        self.result['result'] = 0
        return self.result


    @logger.catch
    def check_text(self, text_to_check, username):
        self.reset_results()
        self.logger.debug(f"# Checking text: {text_to_check}")

        # Spam list check
        spam_list_check = self.check_for_links(text_to_check)
        if spam_list_check['result'] == 1:
            return spam_list_check

        # Check if message contains mishmash and user name is in English
        if self.check_for_english(text_to_check) and self.check_for_english(username):
            msg = f"{username} with {text_to_check} was catched."
            self.result['result'] = 2
            self.result['text'] = msg
            self.result['case'] = "сообщение на латинице, имя пользователя на латинице, вероятно, бот."

        # Check for phone numbers
        if self.check_for_phone(text_to_check):
            msg = f"{username} with {text_to_check} was catched."
            self.result['result'] = 2
            self.result['text'] = msg
            self.result['case'] = "номер телефона в тексте, вероятно, бот."

        # Check if message contains mishmash
        if self.check_for_english(text_to_check):
            msg = f"{username} with {text_to_check} was catched."
            self.result['result'] = 2
            self.result['text'] = msg
            self.result['case'] = "сообщение на латинице, вероятно, бот."

        # Replace Latin characters with Cyrillic
        # text_to_check = self.aux.lat_to_cyr(text_to_check, self.params['word_db']['dict'])

        # Curses list check
        curses_list_check = self.check_for_curses(text_to_check)
        if curses_list_check['result'] >= 1:
            return curses_list_check
        elif self.result['result'] == 2:
            return self.result

        # Suspicious words check
        # If we have more than X words - kill it
        suspicious_check_result = self.check_for_suspicious_words(text_to_check)
        if suspicious_check_result['result'] > 0:
            return suspicious_check_result

        # If user send a picture and user name is in English - warn me
        # if user_check != [] and attachment_flag:
        #     return False, f"# {username} with attachment was catched"
        self.result['result'] = 0
        return self.result


    @logger.catch
    def check_for_english(self, text_to_check):
        self.reset_results()
        self.logger.debug(f"# Checking text for english")
        text_check = re.findall("[A-Za-z].+", text_to_check)
        if text_check:
            return True
        return False


    @logger.catch
    def check_for_suspicious_words(self, text_to_check):
        self.reset_results()
        self.logger.debug(f"# Checking text for suspicious words")
        # If we have more than X words - kill it
        max_points = self.params['word_db']['blacklist']['suspicious_points_limit']
        res = []
        for item in self.params['word_db']['blacklist']['suspicious_list']:
            pattern = r'(\b\S*%s\S*\b)' % item
            # Search all occurences in the text
            matches = re.findall(pattern, text_to_check.lower())
            if matches:
                # If there any - check whitelist for every cursed word we did found
                for match in matches:
                    if not self.check_for_whitelist(match):
                        res.append(f"{item} in {match}")
        if len(res) >= max_points:
            msg = f"Suspicious '{res}' was found.\nMore than {max_points} suspicious words were found."
            self.logger.debug(f"# {msg}")
            self.result['result'] = 1
            self.result['text'] = msg
            self.result['case'] = "подозрительный набор слов, спам, реклама."
            return self.result
        if len(res) > 0 and len(res) < max_points:
            msg = f"Suspicious '{res}' was found. Limit of {max_points} is not exceeded."
            self.logger.debug(f"# {msg}")
            self.result['result'] = 2
            self.result['text'] = msg
            self.result['case'] = "недостаточно подозрительных слов для удаления сообщения."
            return self.result
        if len(res) == 0:
            self.result['result'] = 0
            return self.result


    @logger.catch
    def check_for_links(self, text_to_check):
        self.reset_results()
        self.logger.debug(f"# Checking text for links")
        for item in self.params['word_db']['blacklist']['spam_list']:
            if item in text_to_check.lower().replace(" ", ""):
                msg = f"Forbidden '{item.replace('.', '[.]')}' from spam list was found."
                self.logger.debug(f"# {msg}")
                self.result['result'] = 1
                self.result['text'] = msg
                self.result['case'] = "подозрительная ссылка, реклама."
                return self.result
        self.result['result'] = 0
        return self.result


    @logger.catch
    def check_for_curses(self, text_to_check):
        self.reset_results()
        self.logger.debug(f"# Checking text for curses")
        text_to_check.replace('ё', 'е')
        text_to_check.replace('\n', ' ')
        text_to_check = text_to_check.lower()
        res = []
        regex_blacklist = self.params['word_db']['blacklist']['regex_list']
        for regex in regex_blacklist:
            matches = re.search(re.compile(regex), text_to_check)
            if matches != None:
                print(f"Group: {matches.group()}")
                print(f"String: {matches.string}")
                print(f"Start/end: {matches.start(), matches.end()}")
                print(f"Word: {text_to_check[matches.start():matches.end()]}")
                print("======================================================")
                if not self.check_for_whitelist(matches.string):
                    res.append(f"{matches.group()} in {matches.string}")
                    self.logger.info(f"Regex results: {res}")

        for item in self.params['word_db']['blacklist']['curses_list']:
            pattern = r'(\b\S*%s\S*\b)' % item
            # Search all occurences in the text
            matches = re.findall(pattern, text_to_check.lower())
            if matches:
                # If there any - check whitelist for every cursed word we did found
                for match in matches:
                    if not self.check_for_whitelist(match):
                        res.append(f"{item} in {match}")

        if res:
            msg = f"Forbidden '{res}' from curses list was found."
            self.logger.debug(f"# {msg}")
            self.result['result'] = 1
            self.result['text'] = msg
            self.result['case'] = "нецензурные выражения."
            return self.result
        self.result['result'] = 0
        return self.result


    @logger.catch
    def check_for_whitelist(self, text_to_check):
        self.reset_results()
        self.logger.debug(f"# Checking text for whitelist")
        for item in self.params['word_db']['whitelist']:
            pattern = r'(\b\S*%s\S*\b)' % item
            match = re.findall(pattern, text_to_check)
            if match:
                self.logger.debug(f"# Whitelist '{item}' was found in '{match}', passing...")
                return True
        return False


    @logger.catch
    def check_for_phone(self, text_to_check):
        self.reset_results()
        self.logger.debug(f"# Checking text for phones")
        pattern = r'\+\d+([!\s\(-_]?)+\d+([!\s\)-_]?)+\d+([ _-]?)+\d+([ _-]?)+\d'
        match = re.search(pattern, text_to_check)
        if match:
            return(match.group())
        return None
