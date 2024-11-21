# -*- coding: utf-8 -*-
# Reviewed: November 21, 2024
from __future__ import annotations


class VK:
    # https://dev.vk.com/en/api/bots-long-poll/getting-started
    class vk_longpoll:
        wait = 25

    class vk_api:
        api_key = "VK_API_KEY"
        api_url = "https://api.vk.com/method/"
        group_id = 0
        delete_for_all = 1
        version = "5.236"

    chats = {
        "2000000001": "Main chat",
    }
    log_path = "/var/log/moderator_bot/vk_moderator.log"
    service_name = "vk_moderator"
    errors_limit = 3
    wait_period = 10
    check_delay = 10
    messages_search_count = 3
    public_name = "Самый лучший паблик"


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
    log_path = "/var/log/moderator_bot/tlg_moderator.log"
    service_name = "tlg_moderator"
    captcha_timeout = 20


class Logs:
    longpoll_log = "/var/log/moderator_bot/longpoll.log"
    filter_log = "/var/log/moderator_bot/filter.log"
    processing_log = "/var/log/moderator_bot/processing.log"


class Words_DB:
    class blacklists():
        abc = {
            'а': '[a4а@αᴀ]', 'б': '[6бҕb６]', 'в': '[вvɓbw]', 'г': '[гg]', 'д': '[d∂д]', 'е': '[e℮ᴇ3еiи]', 'ж': '(?:ж|zh)',
            'з': '[3зz]', 'и': '[iи1йыu]', 'й': '[iи1йыu]', 'к': '[кҡkxх]', 'л': '[l1л]', 'м': '[mмʍ]', 'н': '[nhн]',
            'о': '[o0оọσõｏ]', 'п': '[пnpρ]', 'р': '[pᴩrрρ]', 'с': '[сcċцs]', 'т': '[тtτ]', 'у': '[yуẏuʏ]', 'ф': '[фf]',
            'х': '[xх]', 'ц': '[cц]', 'ч': '[hч4]', 'ш': '[ш]', 'щ': '[щ]', 'ь': '[bьъ]', 'ы': '[iи1йыu]',
            'ъ': '[bъь]', 'э': '[e3еiи]', 'ю': '[ю]', 'я': '[я]'
        }
        regex_list = [
            f"(?:без|бес|в|во|воз|вос|возо|вз|вс|вы|до|за|из|ис|изо|на|наи|недо|над|надо|не|низ|нис|низо|о|об|обо|обез|обес|от|ото|па|пра|по|под|подо|пере|пре|пред|предо|при|про|раз|рас|разо|со|су|через|черес|чрез|а|ана|анти|архи|гипер|гипо|де|дез|дис|ин|интер|инфра|квази|кило|контр|макро|микро|мега|мата|мульти|орто|пан|пара|пост|прото|ре|ъ|е|суб|супер|транс|ультра|зкстра|экс|у| |^|(?<=\s))[ъь]?(?:[pп][иёе][zзsсc]{abc['д']}|[eе][лl]{abc['д']}|[еёeiи][бb])",
            f"{abc['х']}{abc['у']}[йиеяюil]",
            f"(?:{abc['п']}{abc['е']}{abc['д']}|{abc['п']}{abc['и']}{abc['д']})(?:{abc['о']}|{abc['а']}|{abc['е']}){abc['р']}",
            f"(?:{abc['б']}|{abc['п']})ля(?:{abc['т']}|{abc['д']})(?:ов|ь|и|ск|з|ок)",
            f"{abc['п']}(?:{abc['е']}|{abc['и']}){abc['н']}{abc['д']}{abc['о']}(?:{abc['с']}|{abc['з']})",
            f"{abc['с']}+[cц]?{abc['у']}(?:{abc['к']}|{abc['ч']})",
            f"(?:{abc['к']}{abc['а']}{abc['к']}|{abc['к']}{abc['о']}{abc['к']})[ло](?:[аоуыля]|лы)",
            f"({abc['м']}{abc['о']}[cц][kк]|{abc['м']}{abc['а']}[cц][kк]){abc['а']}[l1л]",
        ]
        spam_list = [
            "@all", "@online", "@все", "alfa", "bit.do", "bit.ly", "bitly.com", "cashback", "clck.ru", "click", "cutt",
            "decordar.ru", "gclnk.com", "goo.su", "guest.link", "ify.ac", "lnnk", "ls.gd", "nyшkuнc", "nyшkuнс", "ok.me",
            "page.link", "rebrandly", "shorturl.cool", "shrt-l.ink", "t.me", "th.link", "tiktok", "tinyurl", "u.to",
            "vk.cc", "vk.me", "xxxsports.ru", "yurist-forum", "пyшкинc", "пушкинс", "belea.link", "tumblr.com",
            "TG", "telegra.ph"]
        curses_list = [
            "калмунисты", "кацап", "коммуняки", "конченный", "конченый", "коцап", "кремлебот", "монолитовцы",
            "рашка", "русни", "русню", "русня", "украм", "укронацисты", "укры", "фашист", "чмо", "залуп", "нацист", "лярв", "муд",
            "пенис"]
        suspicious_points_limit = 2
        suspisious_regex = [
            f"{abc['а']}{abc['к']}{abc['ц']}{abc['и']}",
            f"{abc['м']}{abc['а']}{abc['р']}{abc['к']}{abc['е']}{abc['т']}",
            f"{abc['к']}{abc['у']}{abc['п']}{abc['о']}{abc['н']}",
            f"{abc['п']}{abc['р']}{abc['и']}{abc['з']}",
            f"{abc['с']}{abc['к']}{abc['и']}{abc['д']}{abc['к']}",
            f"{abc['и']}{abc['н']}{abc['с']}{abc['т']}({abc['а']}|{abc['о']}|{abc['у']}|{abc['е']}|{abc['и']})",
            f"{abc['р']}{abc['у']}{abc['б']}{abc['л']}",
            f"{abc['д']}{abc['о']}{abc['л']}+{abc['а']}{abc['р']}",
            f"{abc['з']}{abc['а']}{abc['р']}({abc['а']}|{abc['о']}){abc['б']}{abc['о']}{abc['т']}",
            f"{abc['в']}h?(?:{abc['а']}|{abc['о']})(?:[cц]|ts|тс){abc['а']}{abc['п']}+",
            f"{abc['а']}{abc['в']}{abc['и']}{abc['т']}{abc['о']}",
            f"{abc['т']}{abc['е']}{abc['л']}{abc['е']}{abc['г']}",
        ]
        suspicious_list = [
            "аккаунт", "аренд", "бесплатн", "ваканс",
            "выплат", "гривен", "гривн", "доставка", "доход", "евро", "заказ",
            "интернет", "кешбек", "клиент", "куплю", "курьер", "кэшбек", "кэшбэк", "менеджер", "оплата",
            "партнер", "пиши", "подписывайтесь", "подпишись", "подпишитесь", "подработ", "подробности",
            "покупк", "продам", "регистратор", "розыгрыш", "самокат", "скупаю", "скидк", "слабонерв",
            "телефон", "халяв", "ценам", "мелстрой", "сертификат", "хомячки", "топовый", "маркет",
            "лохотрон", "купон", "канцтовар", "ивент", "эльдорад", "промик",
            "comedy", "тнт", "деньг", "бонус", "wb", "wildberr", "вайлбер", "вайлдбер", "валбер", "валдбер", "валбир",
            "промокод", "конкурс", "допомогт", "кошт", "картк", "доньк", "операці", "органів", "допомог",
            "интим", "онлифанс", "котик", "антибіотик", "пассив", "гибдд", "@", "калым", "амбиц", "₽", "\$", "€"]

    class whitelists:
        exclusions = [
            "блямб", "блях", "бляш", "влюб", "греб", "дуб", "заглуб", "истреб", "канальн", "колеб", "обляп", "оглоб", "перпендик",
            "озлоб", "оскорб", "пособ", "потреб", "радиоактив", "раздроб", "слаб", "углуб", "укрыт", "виробл", "наибол"
            "розробл", "чмок", "вопрос", "призм", "полторашк", "себ", "себя", "нибудь", "ибо", "корабл",
            "ибк", "вибр", "реакц", "реакт", "призв", "призн", "мудр", "рубл", "плох", "атракц", "аттракц", "судоход", "подоход"]
