# -*- coding: utf-8 -*-
# Reviewed: March 03, 2025
from __future__ import annotations


class VK:
    """Configuration for VK integration."""

    # https://dev.vk.com/en/api/bots-long-poll/getting-started
    class vk_longpoll:
        wait: int = 25

    class vk_api:
        api_key: str = (
            "VK_API_KEY"
        )
        api_url: str = "https://api.vk.com/method/"
        group_id: int = 0
        delete_for_all: int = 1
        version: str = "5.236"

    chats: dict[str, str] = {
        "2000000001": "Main chat",
    }
    log_path: str = "/var/log/moderator_bot/vk_moderator.log"
    service_name: str = "vk_moderator"
    errors_limit: int = 3
    wait_period: int = 10
    check_delay: int = 10
    messages_search_count: int = 3
    public_name = "Самый лучший паблик"
