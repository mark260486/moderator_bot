# -*- coding: utf-8 -*-
# Reviewed: July 25, 2025
from __future__ import annotations


class VK_config:
    """Configuration for VK integration."""

    # https://dev.vk.com/en/api/bots-long-poll/getting-started
    class Longpoll:
        wait: int = 25
        errors_limit: int = 3
        wait_period: int = 10

    class API:
        api_key: str = (
            "VK_API_KEY"
        )
        api_url: str = "https://api.vk.com/method/"
        group_id: int = 0
        delete_for_all: int = 1
        version: str = "5.199"

    chats: dict[str, str] = {
        "2000000001": "Main chat",
    }
    log_path: str = "/var/log/moderator_bot/vk_moderator.log"
    service_name: str = "vk_moderator"
    check_delay: int = 10
    messages_search_count: int = 3
    public_name = "Самый лучший паблик"
