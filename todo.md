### ToDo List
#### Common
- Review todo list :)
- Make instructions for installation and usage;
- Make requirements.txt;
- Make project description;
- Comment all;
#### Bugs to fix
* There are none for now;
#### Telegram interactivity
* Make menu button in Telegram to download bot logs;
    + Button - done;
    + Callback - no;
- Fix callbacks for current menu;
#### Important improvements
- Line 108 in vk_api should be fixed;
- Add chat ID of new message to log and use it for notifications;
- Send to Telegram only Warnings and higher. Replace levels of according alerts;
- Verify params from file;
- Change suspicious words check procedure, too many false cases (send warning to Tlg?);
- Make processing for telegram messages;
- Refactor main cycle for VK moderator;
- Refactor VK errors processing, especially for VK failure;
#### Possible improvements
* Autorestart bots with params.json changes;
    + This should follow after params verifying;
- Add logging with JSON;
- All bots in one chat;
- Add flag to log for new message if there was attachment;
#### Tests and researches
- Try to replace my own VK API module with https://vk-api.readthedocs.io/en/latest/index.html Pypi module;
- Add comment remove function to VK API;
- Try to use regexes for different susp/curse words;
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
