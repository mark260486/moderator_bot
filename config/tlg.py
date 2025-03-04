# -*- coding: utf-8 -*-
# Reviewed: March 04, 2025
from __future__ import annotations


class Telegram:
    class tlg_api:
        api_key = "000000:API_KEY_000"
        log_chat_id: str = "000000"  # Your Telegram ID to get messages from Moderator Bot.
        api_url: str = "https://api.telegram.org/botTLG_KEY/sendMessage"

    class Messages:
        """
        Messages for Telegram Chat.
        Variables member_name and cause_name are internal Telegram API return values.
        cause_name is in admin actions.
        member_name are both in admin and user actions.
        """
        Greeting: str = "К нам присоединяется member_name. Добро пожаловать!"
        Ban: str = "Администратор cause_name вышвыривает member_name. Земля стекловатой."
        Clear: str = "Администратор cause_name убирает из подписчиков 'Удалённый аккаунт'."
        Leave: str = "member_name покинул(а) чат. Удачи!"
        Mute: str = "member_name заболевает молчанкой."
        Unmute_is_member: str = "member_name вылечивается от молчанки."
        Unmute_was_member: str = "member_name вылечивается от молчанки и покидает чат."

    # Telegram DB for restricted users
    tlg_db_path: str = "/home/my_user/telegram.db"

    class Captcha:
        """Parameters for chat Captcha."""
        Enabled: bool = False
        Timeout_enabled: bool = True  # Not implemented yet. Will be there timeout for user's answer to captcha
        Button_enabled: bool = True  # Not implemented yet. The new user must click a button to proceed.
        Question_enabled: bool = True  # Not implemented yet. The new user must answer the security question by sending the answer. Related param: `Question`
        Random_sum_enabled: bool = True  # Not implemented yet. The new user must answer simple random arithmetic task.
        Timeout: int = 30
        Question: str = "`В каком году произошла авария на Чернобыльской АЭС?`"
        Answer: list[str] = ["1986"]
        Message: str = (
            "Привет, member_name! Мы хотим проверить, что ты не бот. "
            f"Пожалуйста, ответь на контрольный вопрос за {Timeout} секунд:\n{Question}"
        )
        temp_message: str = f"Привет, member_name!\nПожалуйста, подтверди, что ты человек, в течение {Timeout} секунд."
        temp_button: str = "Да, я человек"
        Timeout_message: str = f"Увы, member_name, {Timeout} секунд прошло, ты не успел :("

    class Channel_forward:
        """Parameters for Telegram chats with topics."""
        enabled: bool = False
        forum_id: int = -1001436890713  # This is your Chat ID
        thread_id: int = 64392  # This is your Topic ID
        channel_id: int = -1001304165573  # This is your channel ID

    log_path = "/var/log/moderator_bot/tlg_moderator.log"
    service_name: str = "tlg_moderator"
    # This is the limit for scam messages consisting of Telegram premium emoji
    emoji_length_limit: int = 10
