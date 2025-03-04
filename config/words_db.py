# -*- coding: utf-8 -*-
# Reviewed: March 03, 2025
from __future__ import annotations


class Words_DB:
    class blacklists():
        """Blacklists for filtering words and phrases."""
        abc: dict[str, str] = {
            'а': '[a4а@αᴀ🅐ᗩ₳𝙰]', 'б': '[6бҕb６]', 'в': '[вvɓbw]', 'г': '[гgr]', 'д': '[d∂д]', 'е': '[e℮ᴇ3еiи]', 'ж': '[жҗ]',
            'з': '[3зz]', 'и': '[iи1йыu]', 'й': '[iи1йыu]', 'к': '[кҡkxх]', 'л': '[l1л]', 'м': '[mмʍ]', 'н': '[nhн]',
            'о': '[o0оọσõｏ🅞Øᴏ𝐎]', 'п': '[пnpρ]', 'р': '[pᴩrрρ]', 'с': '[сcċцs]', 'т': '[тt𝗧τm]', 'у': '[yуẏuʏ]', 'ф': '[фf]',
            'х': '[xх]', 'ц': '[cц]', 'ч': '[hч4]', 'ш': '[ш]', 'щ': '[щ]', 'ь': '[bьъ]', 'ы': '[iи1йыu]',
            'ъ': '[bъь]', 'э': '[e3еiи]', 'ю': '[ю]', 'я': '[я]'
        }
        regex_list: list[str] = [
            f"(?:без|бес|в|во|воз|вос|возо|вз|вс|вы|до|за|из|ис|изо|на|наи|недо|над|надо|не|низ|нис|низо|о|об|обо|обез|обес|от|ото|па|пра|по|под|подо|пере|пре|пред|предо|при|про|раз|рас|разо|со|су|через|черес|чрез|а|ана|анти|архи|гипер|гипо|де|дез|дис|ин|интер|инфра|квази|кило|контр|макро|микро|мега|мата|мульти|орто|пан|пара|пост|прото|ре|ъ|е|суб|супер|транс|ультра|зкстра|экс|у| |^|(?<=\s))[ъь]?(?:[pп][иёе][zзsсc]{abc['д']}|[eе][лl]{abc['д']}|[еёeiи][бb])",
            f"{abc['х']}{abc['у']}[йиеяюil]",
            f"(?:{abc['п']}{abc['е']}{abc['д']}|{abc['п']}{abc['и']}{abc['д']})(?:{abc['о']}|{abc['а']}|{abc['е']}){abc['р']}",
            f"(?:{abc['б']}|{abc['п']})ля(?:{abc['т']}|{abc['д']})(?:ов|ь|и|ск|з|ок)",
            f"{abc['п']}(?:{abc['е']}|{abc['и']}){abc['н']}{abc['д']}{abc['о']}(?:{abc['с']}|{abc['з']})",
            f"{abc['с']}+[cц]?{abc['у']}(?:к|{abc['ч']})",
            f"(?:{abc['к']}{abc['а']}{abc['к']}|{abc['к']}{abc['о']}{abc['к']})[ло](?:[аоуыля]|лы)",
            f"({abc['м']}{abc['о']}[cц][kк]|{abc['м']}{abc['а']}[cц][kк]){abc['а']}[l1л]",
            f"{abc['п']}({abc['и']}|{abc['е']}){abc['з']}{abc['д']}",
        ]
        spam_list: list[str] = [
            "@all", "@online", "@все", "bit.do", "bit.ly", "bitly.com", "cashback", "clck.ru", "click", "cutt",
            "decordar.ru", "gclnk.com", "goo.su", "guest.link", "ify.ac", "lnnk", "ls.gd", "nyшkuнc", "nyшkuнс", "ok.me",
            "page.link", "rebrandly", "shorturl.cool", "shrt-l.ink", "t.me", "th.link", "tiktok", "tinyurl", "u.to",
            "vk.cc", "vk.me", "xxxsports.ru", "yurist-forum", "пyшкинc", "пушкинс", "belea.link", "tumblr.com",
            "TG", "telegra.ph"]
        curses_list: list[str] = [
            "калмунисты", "кацап", "коммуняки", "конченный", "конченый", "коцап", "кремлебот", "монолитовцы",
            "рашка", "русн", "украм", "укронацисты", "укры", "фашист", "чмо", "залуп", "нацист", "лярв", "муд",
            "пенис", "бля"]
        suspicious_points_limit: int = 2
        suspisious_regex: list[str] = [
            f"{abc['а']}{abc['к']}{abc['ц']}{abc['и']}",
            f"{abc['м']}{abc['а']}{abc['р']}{abc['к']}{abc['е']}{abc['т']}",
            f"{abc['к']}{abc['у']}{abc['п']}{abc['о']}{abc['н']}",
            f"{abc['п']}{abc['р']}{abc['и']}{abc['з']}",
            f"{abc['с']}{abc['к']}{abc['и']}{abc['д']}{abc['к']}",
            f"{abc['и']}{abc['н']}{abc['с']}{abc['т']}({abc['а']}|{abc['о']}|{abc['у']}|{abc['е']}|{abc['и']})",
            f"{abc['р']}{abc['у']}{abc['б']}{abc['л']}",
            f"{abc['д']}{abc['о']}{abc['л']}+{abc['а']}{abc['р']}",
            f"{abc['г']}{abc['р']}{abc['н']}",
            f"{abc['з']}{abc['а']}{abc['р']}({abc['а']}|{abc['о']}){abc['б']}{abc['о']}{abc['т']}",
            f"{abc['в']}h?(?:{abc['а']}|{abc['о']})(?:[cц]|ts|тс){abc['а']}{abc['п']}+",
            f"{abc['а']}{abc['в']}{abc['и']}{abc['т']}{abc['о']}",
            f"{abc['т']}{abc['е']}{abc['л']}{abc['е']}{abc['г']}",
            f"{abc['в']}{abc['о']}{abc['д']}{abc['и']}{abc['т']}{abc['е']}{abc['л']}",
            f"{abc['в']}{abc['о']}{abc['з']}{abc['н']}{abc['а']}{abc['г']}{abc['р']}",
        ]
        suspicious_list: list[str] = [
            "аккаунт", "аренд", "бесплатн", "ваканс", "удален", "личн",
            "выплат", "гривен", "гривн", "доставка", "доход", "евро", "заказ",
            "интернет", "кешбек", "клиент", "куплю", "курьер", "кэшбек", "кэшбэк", "менеджер", "оплата",
            "партнер", "пиши", "подписывайтесь", "подпишись", "подпишитесь", "подработ", "подробности",
            "покупк", "продам", "регистратор", "розыгрыш", "самокат", "скупаю", "скидк", "слабонерв",
            "телефон", "халяв", "ценам", "мелстрой", "сертификат", "хомячки", "топовый", "маркет",
            "лохотрон", "купон", "канцтовар", "ивент", "эльдорад", "промик",
            "comedy", "тнт", "деньг", "бонус", "wb", "wildberr", "вайлбер", "вайлдбер", "валбер", "валдбер", "валбир",
            "промокод", "конкурс", "допомогт", "кошт", "картк", "доньк", "операці", "органів", "допомог",
            "интим", "онлифанс", "котик", "антибіот", "пассив", "гибдд", "@", "калым", "амбиц", "₽", "\$", "€", "грн", "дoхiд"]

    class whitelists:
        """Whitelists for filtering words and phrases."""
        exclusions: list[str] = [
            "блямб", "блях", "бляш", "влюб", "греб", "дуб", "заглуб", "истреб", "канальн", "колеб", "веб", "обляп", "оглоб", "перпендик",
            "озлоб", "оскорб", "пособ", "потреб", "радиоактив", "раздроб", "слаб", "углуб", "укрыт", "виробл", "наибол", "сухогруз",
            "розробл", "чмок", "вопрос", "призм", "полторашк", "себ", "себя", "нибудь", "ибо", "корабл", "каприз", "сухп", "засуха",
            "ибк", "вибр", "реакц", "реакт", "призв", "призн", "мудр", "рубл", "плох", "атракц", "аттракц", "судоход", "подоход", "сиби"]
