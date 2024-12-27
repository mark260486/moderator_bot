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
- Comment all.

#### Known bugs to fix

- Errors processing for VK API requests.

#### Important improvements

- Define parameters we can move from Config file to Arguments;
- Add automatical service restart if there were Errors in logs;
- Verify params from file;
- Refactor VK errors processing, especially for VK failure;
- Check the entire code for the need for the try...except operator;
- Make assertion tests and documenting.

#### Possible improvements

* Autorestart bots with config.py changes;
    + This should follow after params verifying;
- Add logging with JSON;
- Add flag to log for new message if there was attachment.

#### Tests and researches

- Add comment remove function to VK API;
- Make different wait periods for different errors at VK API request;
* Make tests about user kick;
    + Message about kick - need to fix;
    + Can kicked user return? - Yes, by admin invitation;
* Create database for bad users;
    + implement limit to removed messages to get banned;
    + implement Telegram menu buttons to work with DB;
- Implement web UI for bot management;
- Refactor Filter class to count suspicious cases instead of warning and compare that count to some limit.
