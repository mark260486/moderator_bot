# -*- coding: utf-8 -*-
# Reviewed: January 23, 2025
from __future__ import annotations


class Telegram:
    class tlg_api:
        api_key = "000000:API_KEY_000"
        # Your Telegram ID to get messages from Moderator Bot.
        log_chat_id = "000000"
        api_url = "https://api.telegram.org/botTLG_KEY/sendMessage"

    # # # Messages for Telegram Chat.
    # Variables member_name and cause_name are internal Telegram API return values.
    # cause_name is in admin actions.
    # member_name are both in admin and user actions.
    greeting_msg = "К нам присоединяется member_name.\nДобро пожаловать!"
    ban_msg = "Администратор cause_name вышвыривает member_name. Земля ему стекловатой."
    clear_msg = (
        "Администратор cause_name убирает из подписчиков 'Удалённый аккаунт'."
    )
    leave_msg = "member_name покинул(а) чат. Удачи!"
    mute_msg = "member_name заболевает молчанкой."
    unmute_msg_is_member = "member_name вылечивается от молчанки."
    unmute_msg_was_member = (
        "member_name вылечивается от молчанки и покидает чат."
    )

    # # # Telegram DB for restricted users
    tlg_db_path = "/home/my_user/telegram.db"

    class captcha:
        # This params are designated for chat Captcha
        enabled = True              # Not implemented yet
        timeout_enabled = True      # Not implemented yet. Will be there timeout for user's answer to captcha
        question_enabled = True     # Not implemented yet. If True: answer must question with text, else: just a button to click
        timeout = 30
        question = "`В каком году произошла авария на Чернобыльской АЭС?`"
        answer = ["1986"]
        message = f"Привет, member_name! Мы хотим проверить, что ты не бот. Пожалуйста, ответь на контрольный вопрос за {timeout} секунд:\n{question}"
        temp_message = f"Привет, member_name!\nПожалуйста, подтверди, что ты человек, в течение {timeout} секунд."
        temp_button = "Да, я человек"
        timeout_message = f"Увы, member_name, {timeout} секунд прошло, ты не успел :("

    class channel_forward:
        # This params are designated for Telegram chats with topics
        enabled = True
        # This is your Chat ID
        forum_id = 000
        # This is your Topic ID
        thread_id = 000

    log_path = "/home/mark/moderator_bot/logs/tlg_moderator.log"
    # log_path = "/var/log/moderator_bot/tlg_moderator.log"
    service_name = "tlg_moderator"
    # This is the limit for scam messages consisting of Telegram premium emoji
    emoji_length_limit = 10
