# Reviewed: May 03, 2024


class VK:
    class vk_longpoll:
        wait = 25
    class vk_api:
        api_key = "VK_API_KEY"
        api_url = "https://api.vk.com/method/"
        group_id = 0
        delete_for_all = 1
        version = "5.199"

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
        log_chat_id = "000000"   # Your Telegram ID to get messages from Moderator Bot.
        api_url = "https://api.telegram.org/botTLG_KEY/sendMessage"

    # # # Messages for Telegram Chat.
    # Variables member_name and cause_name are internal Telegram API return values.
    # cause_name is in admin actions.
    # member_name are both in admin and user actions.
    greeting_msg = "К нам присоединяется member_name.\nДобро пожаловать!"
    ban_msg = "Администратор cause_name вышвыривает member_name. Земля ему стекловатой."
    clear_msg = "Администратор cause_name убирает из подписчиков 'Удалённый аккаунт'."
    leave_msg = "member_name покинул канал. Удачи!"
    # admin_ids are for personal IDs of the Telegram Chat to split users and Admins in script logic.
    admin_ids = ["0000"]
    log_path = "/var/log/moderator_bot/tlg_moderator.log"
    service_name = "tlg_moderator"

class Logs:
    longpoll_log = "/var/log/moderator_bot/longpoll.log"
    filter_log = "/var/log/moderator_bot/filter.log"
    processing_log = "/var/log/moderator_bot/processing.log"

class Words_DB:
    class blacklists:
        regex_list = [
            "(?:без|бес|в|во|воз|вос|возо|вз|вс|вы|до|за|из|ис|изо|на|наи|недо|над|надо|не|низ|нис|низо|о|об|обо|обез|обес|от|ото|па|пра|по|под|подо|пере|пре|пред|предо|при|про|раз|рас|разо|с|со|су|через|черес|чрез|а|ана|анти|архи|гипер|гипо|де|дез|дис|ин|интер|инфра|квази|кило|контр|макро|микро|мега|мата|мульти|орто|пан|пара|пост|прото|ре|суб|супер|транс|ультра|зкстра|экс|у|(?<=\\s))[ъь]?(?:[pп][иёе][zзsсc][dд]|[eе][лl][dд]|[еёeiи][бb])([а-яА-Я]{0,})?",
            "([а-яА-Я]{0,})?[xх][уy][йиеяюil]([а-яА-Я]{0,})?",
            "([а-яА-Я]{0,})?([пnp][e3е][dд]|[пnp][iий][dд]|[pпn][iий][nhн][dд]|[пpn][e3е][nhн][dд])(?:[o0о][prр]|[o0о][scс]|[iий][kк]|[e3е][kк]|[e3е][prр]|[iий][prр]|[a4а][prр])([а-яА-Я]{0,})?",
            "([а-яА-Я]{0,})?(?:[б6]|[пpn])ля([тt]|[дd])(?:ов|ь|и|ск|з|ок)([а-яА-Я]{0,})?",
            "([а-яА-Я]{0,})?([пpn][iий][3зz][dд]|[пpn][iий][scс][dд]|[пpn][e3е][3зz][dд]|[пpn][e3е][scс][dд])([а-яА-Я]{0,})?",
            "[сc]{1,}([cц])?у([kк]|[hч4])",
            "([а-яА-Я]{0,})(?:[кkxх][a4а][кkxх]|[кkxх][o0о][кkxх])[ло](?:[аоуыля]|лы)([а-яА-Я]{0,})?",
            "([mм][o0о][cц][kк]|[mм][a4а][cц][kк])[a4а][l1л]"
        ]
        spam_list = [
            "@all","@online","@все","alfa","bit.do","bit.ly","bitly.com","cashback","clck.ru","click","cutt","decordar.ru","gclnk.com","goo.su",
            "guest.link","ify.ac","lnnk","ls.gd","nyшkuнc","nyшkuнс","ok.me","page.link","rebrandly","shorturl.cool","shrt-l.ink","t.me","th.link",
            "tiktok","tinyurl","u.to","vk.cc","vk.me","xxxsports.ru","yurist-forum","пyшкинc","пушкинс","belea.link","tumblr.com","TG","what's","app",
            "whats"
        ]
        curses_list = [
            "калмунисты","кацап","коммуняки","конченный","конченый","коцап","кремлебот","монолитовцы","бля",
            "рашка","русни","русню","русня","украм","укронацисты","укры","фашист","чмо","залуп","нацист"
        ]
        suspicious_points_limit = 2
        suspicious_list = [
            "avito","whatsapp","авито","аккаунт","акци","аренд","бесплатн","ваканс","вакансия","ватсап","вацап","вотсап",
            "воцап","выплат","гривен","гривна","доллар","доставка","доход","евро","заказ","заработок","интернет","кешбек","клиент",
            "компьютер","куплю","курьер","кэшбек","кэшбэк","менеджер","оплата","опрос","партнер","пиши","подписывайтесь","подпишись","подпишитесь",
            "подработ","подробности","покупк","приз","продам","регистратор","розыгрыш","рубл","самокат","скупаю","скидка","слабонерв","телеграм",
            "телефон","халяв","ценам","заработ","мелстрой","сертификат","хомячки","топовый","https","маркет","промоакц","лохотрон","купон","канцтовар",
            "инста","инсте","инсту","ивент","эльдорад","промик","comedy","тнт","деньг","бонус","wb","wildberr","вайлбер","вайлдбер","валбер","валдбер",
            "валбир","comedy"
        ]
    whitelist = [
        "блямб","блях","бляш","влюб","греб","дуб","заглуб","истреб","канальн","колеб","обляп","оглоб","озлоб","оскорб","пособ","потреб",
        "радиоактив","раздроб","расслаб","углуб","укрыт","виробл","розробл","чмок","вопрос","призм","полторашк","пасиб","пасип","себе","себя",
        "нибудь","ибо"
    ]