### Simple VK/Telegram public bot for chat moderation
---

This set of scripts can strictly moderate VK/Telegram messages in both chats and comments. It doesn't designated to work with Telegram channels having multiple chats. Instructions will follow soon.

---

### ToDo List

#### Common

- Review todo list :)
- Make instructions for installation and usage;
- Make requirements.txt;
- Make project description;
- Comment all;

#### Bugs to fix

- Get "Message was removed" even if it's not;

#### Important improvements

- Add automatical service restart if there were Errors in logs;
- Add chat ID of new message to log and use it for notifications;
- Verify params from file;
- Change suspicious words check procedure, too many false cases (send warning to Tlg?);
- Make processing for telegram messages;
- Refactor main cycle for VK moderator;
- Refactor VK errors processing, especially for VK failure;
- Refactor config;

#### Possible improvements

* Autorestart bots with config.json changes;
    + This should follow after params verifying;
- Add logging with JSON;
- All bots in one chat;
- Add flag to log for new message if there was attachment;

#### Telegram interactivity

* Make menu button in Telegram to download bot logs;
    + Button - done;
    + Callback - no;
- Fix callbacks for current menu;

#### Tests and researches

* Try to replace my own VK API module with https://vk-api.readthedocs.io/en/latest/index.html Pypi module;
    + Playing with VK Wave module;
- Add comment remove function to VK API;
- Try to use regexes for different susp/curse words;
- Make different wait periods for different errors at VK API request;
* Make tests about user kick;
    + Message about kick - need to fix;
    + Can kicked user return? - Yes, by admin invitation;
* Create database for bad users;
    + find the simplest lightweight DB to work with;
    + find the Python library to work with DB;
    + implement class/functions to work with DB;
    + implement limit to removed messages to get banned;
    + implement Telegram menu buttons to work with DB;
- Maybe it is worth to make all bot async.
