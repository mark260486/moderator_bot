# -*- coding: utf-8 -*-
# Reviewed: December 27, 2024
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
        "2000000001": "Main chat"
    }
    log_path = "/var/log/moderator_bot//vk_moderator.log"
    service_name = "vk_moderator"
    errors_limit = 3
    wait_period = 10
    check_delay = 10
    messages_search_count = 3
    public_name = "Самый лучший паблик"
