# Reviewed: December, 20
# ToDo:
#   - comment all


import re
from loguru import logger


DEBUG_ENABLED = False


class filter:
    def __init__(self, aux, filter_logger = None) -> None:
        self.params = aux.read_params()
        self.aux = aux
        if filter_logger == None:
            if DEBUG_ENABLED:
                logger.add(self.params['filter_log'], level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            else:
                logger.add(self.params['filter_log'], level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
            self.logger = logger
        else:
            self.logger = filter_logger
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
    def filter_response(self, text, username, attachments):
        self.logger.debug("# Filtering response")
        # Attachments checks
        check_attachments_result = self.check_attachments(attachments, username)
        if check_attachments_result['result'] == 1:
            return check_attachments_result

        # Text check
        check_text_result = self.check_text(text, username)
        if check_text_result['result'] == 1:
            return check_text_result

        self.result['result'] = 0
        return self.result


    # Check of attachments for links and bad things in repost/reply
    @logger.catch
    def check_attachments(self, attachments, username):
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
        # Prepare text for further checks
        # Replace ё with e and remove new lines
        text_to_check.replace('ё', 'е')
        text_to_check.replace('\n', ' ')
        # Lower text
        text_to_check = text_to_check.lower()

        self.logger.debug(f"# Checking text: {text_to_check}")
        # Check if message contains mishmash and user name is in English
        # if self.check_for_english(text_to_check) and self.check_for_english(username):
        #     msg = f"{username} with {text_to_check} was catched."
        #     self.logger.debug(f"# {msg}")
        #     self.result['result'] = 1
        #     self.result['text'] = msg
        #     self.result['case'] = "сообщение на латинице, имя пользователя на латинице, реклама."
        #     return self.result

        # Check if message contains mishmash
        # if self.check_for_english(text_to_check):
        #     msg = f"{username} with {text_to_check} was catched."
        #     self.logger.debug(f"# {msg}")
        #     self.result['result'] = 1
        #     self.result['text'] = msg
        #     self.result['case'] = "сообщение на латинице, реклама."
        #     return self.result

        # Spam list check
        spam_list_check = self.check_for_links(text_to_check)
        if spam_list_check['result'] == 1:
            return spam_list_check

        # Replace Latin characters with Cyrillic
        text_to_check = self.aux.lat_to_cyr(text_to_check, self.params['word_db']['dict'])

        # Curses list check
        curses_list_check = self.check_for_curses(text_to_check)
        if curses_list_check['result'] == 1:
            return curses_list_check

        # Suspicious words check
        # If we have more than X words - kill it
        suspicious_check_result = self.check_for_suspicious_words(text_to_check)
        if suspicious_check_result['result'] != 0:
            return suspicious_check_result

        # If user send a picture and user name is in English - warn me
        # if user_check != [] and attachment_flag:
        #     return False, f"# {username} with attachment was catched"
        self.result['result'] = 0
        return self.result


    @logger.catch
    def check_for_english(self, text_to_check):
        self.logger.debug(f"# Checking text for english: {text_to_check}")
        text_check = re.findall("[A-Za-z0-9].+", text_to_check)
        if text_check:
            return True
        return False


    @logger.catch
    def check_for_suspicious_words(self, text_to_check):
        self.logger.debug(f"# Checking text for suspicious words: {text_to_check}")
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
            self.result['case'] = ""
            return self.result
        if len(res) == 0:
            self.result['result'] = 0
            return self.result


    @logger.catch
    def check_for_links(self, text_to_check):
        self.logger.debug(f"# Checking text for links: {text_to_check}")
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
        self.logger.debug(f"# Checking text for curses: {text_to_check}")
        text_to_check.replace('ё', 'е')
        text_to_check.replace('\n', ' ')
        text_to_check = text_to_check.lower()
        res = []
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
        self.logger.debug(f"# Checking text for whitelist: {text_to_check}")
        for item in self.params['word_db']['whitelist']:
            pattern = r'(\b\S*%s\S*\b)' % item
            match = re.findall(pattern, text_to_check)
            if match:
                self.logger.debug(f"# Whitelist '{item}' was found in '{match}', passing...")
                return True
        return False


    @logger.catch
    def check_for_phone(self, text_to_check):
        text = text_to_check.lower()
        pattern = r'\+\d+([!\s\(-_]?)+\d+([!\s\)-_]?)+\d+([ _-]?)+\d+([ _-]?)+\d'
        match = re.search(pattern, text)
        if match:
            return(match.group())
        return None