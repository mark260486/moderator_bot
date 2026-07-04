# -*- coding: utf-8 -*-
# Reviewed: June 20, 2026
from __future__ import annotations

import re
import string
import requests
from bs4 import BeautifulSoup
from loguru import logger
from difflib import get_close_matches
from typing import Dict, Optional
from faq.faq_defs import FaqDef
from config.tlg import Telegram

DEFINITIONS = FaqDef.DEFINITIONS

def _normalize(text: str) -> str:
    text = text.lower().strip()
    # remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # collapse spaces
    text = re.sub(r"\s+", " ", text)
    return text


# Automatically build the alias -> key mapping
_ALIAS_MAP: Dict[str, str] = {}
for key, rec in DEFINITIONS.items():
    for a in rec.get("aliases", []):
        _ALIAS_MAP[_normalize(a)] = key


_PATTERN = re.compile(r"^(?:что(?:\s+(?:такое|за))|кто\s+такой|кто\s+такая)\s+(.+)$", re.I)


def extract_term(question: str) -> Optional[str]:
    q = question.strip()
    # remove trailing question mark and similar
    q = q.rstrip("?！？. ")
    m = _PATTERN.match(q)
    if m:
        term = m.group(1)
        term = term.strip().strip("\'\"")
        return term
    return None


def get_local_definition(question: str) -> Optional[str]:
    """
    Attempt to recognize the question and return the answer.
    Returns the answer string or None if not found.
    """
    norm_q = _normalize(question)

    # 1) extract a term from typical patterns
    term = extract_term(question)
    print(f"# Extracted term: '{term}' from question: '{norm_q}'")
    if term:
        norm_term = _normalize(term)
        key = _ALIAS_MAP.get(norm_term)
        if key:
            print(f"# Found definition for key: '{key}'")
            rec = DEFINITIONS[key]
            return rec.get("answer")

    # 2) if the question is a short term
    if norm_q in _ALIAS_MAP:
        print(f"# Exact match found in a short term: '{norm_q}'")
        rec = DEFINITIONS[_ALIAS_MAP[norm_q]]
        return rec.get("answer")

    # 3) fuzzy search by aliases
    candidates = get_close_matches(norm_q, list(_ALIAS_MAP.keys()), n=1, cutoff=0.9)
    if candidates:
        print(f"# Fuzzy match found: '{candidates[0]}'")
        rec = DEFINITIONS[_ALIAS_MAP[candidates[0]]]
        return rec.get("answer")

    return None


def get_remote_definition(question: str) -> Optional[str]:
    """
    Attempt to recognize the question and return the answer.
    Returns the answer string or None if not found.
    """
    norm_q = _normalize(question)
    term = extract_term(question)
    logger.debug(f"# Extracted term: '{term}' from question: '{norm_q}'")
    if not term:
        logger.debug(f"# No term extracted from question: '{norm_q}'")
        return None

    try:
        rs = requests.get(Telegram.FAQ.remote_faq_url, timeout=5)
        rs.raise_for_status()
    except requests.RequestException:
        return None

    root = BeautifulSoup(rs.content, "html.parser")
    target_div = root.find("div", class_="article_view")
    if not target_div:
        return None

    text = target_div.get_text(strip=True)
    text = text.replace("— ", " — ")
    text = text.replace("- ", " - ")
    text = text.replace(";", ";\n")

    pattern = re.compile(rf"^{re.escape(term)}.+", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)

    if match:
        return match.group().strip()

    return None


__all__ = ["DEFINITIONS", "get_local_definition", "get_remote_definition", "extract_term"]
