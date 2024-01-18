# Reviewed: January 18, 2024

from telegram import (Update, ChatMember, ChatMemberUpdated)
from telegram.ext import (Updater, CallbackContext, ChatMemberHandler, MessageHandler, Application, filters, ContextTypes)
from telegram.constants import ParseMode
from typing import Optional, Tuple
from loguru import logger
from notifiers.logging import NotificationHandler
import auxiliary
import filter


PARAMS_FILE = "params.json"
DEBUG_ENABLED = False


text = ""
caption = ""
first_name = ""
username = ""
urls = []


aux = auxiliary.auxiliary()
filter = filter.filter(aux)
params = aux.read_params()
log_file = params['TLG']['log_path']
cases_log_file = params['TLG']['cases_log_path']

# Logging params
if DEBUG_ENABLED:
    logger.add(log_file, level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB")
    logger.add(cases_log_file, level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB")
else:
    logger.add(log_file, level="INFO", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB")
    logger.add(cases_log_file, level="DEBUG", format = "{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}", rotation = "10 MB")

# Telegram messages logging
tg_params = {
    'token': params['TLG']['TLG_MOD']['key'],
    'chat_id': params['TLG']['TLG_MOD']['log_chat_id']
}
tg_handler = NotificationHandler("telegram", defaults = tg_params)
logger.add(tg_handler, format = "{message}", level = "INFO")


@logger.catch
def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


@logger.catch
async def greet_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greets new users in chats and announces when someone leaves"""
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()

    if not was_member and is_member:
        msg = f"К нам присоединяется {member_name}. Пожалуйста, изучите наши правила.\nДобро пожаловать!" 
    elif was_member and not is_member:
        if "338817709" in cause_name or "5082983547" in cause_name:
            msg = f"Администратор {cause_name} вышвыривает {member_name}. Земля ему стекловатой."
        else:
            msg = f"{member_name} покинул канал. Удачи!"
    logger.debug(f"Cause name: {cause_name}, member name: {member_name}")
    await context.bot.send_message(params['TLG']['TLG_MOD']['chat_id'], msg, parse_mode = ParseMode.HTML)


@logger.catch
async def moderate_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Moderate message"""
    params = aux.read_params()

    res = update.to_dict()
    logger.debug(f"# Update: {res}")

    # Reset globals for future check
    global text, caption, first_name, username
    text = ""
    caption = ""
    first_name = ""
    username = ""
    urls = []

    message_key = ""
    if "edited_message" in res:
        message_key = "edited_message"
    else:
        message_key = "message"

    if "entities" in res[message_key]:
        for entity in res[message_key]['entities']:
            try:
                urls.append(entity['url'])
            except: None

    if urls != []:
        for url in urls:
            check_url_result = filter.check_for_links(url)
    
        logger.debug(f"# Filter result: {check_url_result}")
        if check_url_result['result'] != 0:
            logger.info(f"Message to remove from {first_name}(@{username})\n'{text.replace('.', '[.]')}'")
            await context.bot.delete_message(chat_id, message_id)
            await context.bot.send_message(
                params['TLG']['TLG_MOD']['chat_id'], 
                f"Сообщение от {first_name}(@{username}) было удалено автоматическим фильтром. Причина: подозрительная ссылка."
                )


    try:
        text = res[message_key]['text']
    except: None
    try:
        caption = res[message_key]['caption']
    except: None
    try:
        first_name = res[message_key]['from']['first_name']
    except: None
    try:
        username = res[message_key]['from']['username']
    except: None

    chat_id = res[message_key]['chat']['id']
    message_id = res[message_key]['message_id']
    logger.debug(f"# Text: {text}, Caption: {caption}, Name: {first_name}, Login: {username}, URLS: {urls}, Chat ID: {chat_id}, Message ID: {message_id}")

    if text != "":
        check_text_result = filter.check_text(text, username)
    if caption != "":
        check_text_result = filter.check_text(caption, username)

    logger.debug(f"# Filter result: {check_text_result}")
    if check_text_result['result'] != 0:
        logger.info(f"Message to remove from {first_name}(@{username}): '{text.replace('.', '[.]')}'")
        reason = check_text_result['case']

        await context.bot.delete_message(chat_id, message_id)
        await context.bot.send_message(params['TLG']['TLG_MOD']['chat_id'], f"Сообщение от {first_name}(@{username}) было удалено автоматическим фильтром. Причина: {reason}")


@logger.catch
def main() -> None:
    """Start the bot."""
    # Read and apply token
    params = aux.read_params()
    app = Application.builder().token(params['TLG']['TLG_MOD']['key']).build()

    logger.info("Telegram moderator bot listener re/starting..")

    # On non command i.e message - moderate message content
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, moderate_message))
    app.add_handler(MessageHandler(filters.ATTACHMENT, moderate_message))

    # Handle members joining/leaving chats.
    app.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))

    # Run the bot until the user presses Ctrl-C
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
