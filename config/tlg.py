# -*- coding: utf-8 -*-
# Reviewed: January 20, 2024
from __future__ import annotations


class Telegram:
    class tlg_api:
        api_key = "000000:API_KEY_000"
        chat_id = "-000000"  # Telegram Chat to moderate.
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
        timeout = 30
        question = "`В каком году произошла авария на Чернобыльской АЭС?`"
        answer = ["1986"]
        message = f"Привет, member_name! Мы хотим проверить, что ты не бот. Пожалуйста, ответь на контрольный вопрос за {timeout} секунд:\n{question}"
        temp_message = f"Привет, member_name!\nПожалуйста, подтверди, что ты человек, в течение {timeout} секунд."
        temp_button = "Да, я человек"
    log_path = "/var/log/moderator_bot//tlg_moderator.log"
    # log_path = "/var/log/moderator_bot/tlg_moderator.log"
    service_name = "tlg_moderator"
    # This is the limit for scam messages consisting of Telegram premium emoji
    emoji_length_limit = 10
