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

- None for now;

#### Important improvements

- Define parameters we can move from Config file to Arguments;
- Add automatical service restart if there were Errors in logs;
- Add chat ID of new message to log and use it for notifications;
- Verify params from file;
- Change suspicious words check procedure, too many false cases (send warning to Tlg?);
- Refactor VK errors processing, especially for VK failure;

#### Possible improvements

* Autorestart bots with config.py changes;
    + This should follow after params verifying;
- Add logging with JSON;
- Add flag to log for new message if there was attachment;

#### Telegram interactivity

- Do I really need this functions?
* Make menu button in Telegram to download bot logs;
    + Button - done;
    + Callback - no;
- Fix callbacks for current menu;

#### Tests and researches

* Try to replace my own VK API module with https://vk-api.readthedocs.io/en/latest/index.html Pypi module;
    + Playing with VK Wave module - doesn't work with edited messages;
- Add comment remove function to VK API;
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
- Implement web UI for bot management.
