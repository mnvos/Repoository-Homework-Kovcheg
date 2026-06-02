import asyncio
import json
from types import SimpleNamespace
from pathlib import Path

import pytest

from bot.knowledge import KnowledgeBase
import bot.main as bot_main


class DummyMessage:
    def __init__(self, text: str):
        self.text = text
        self.last_reply = None

    async def reply_text(self, text: str):
        self.last_reply = text

    async def reply_markdown_v2(self, text: str):
        self.last_reply = text


class DummyUpdate:
    def __init__(self, text: str):
        self.message = DummyMessage(text)


class DummyContext:
    def __init__(self, kb: KnowledgeBase):
        self.application = SimpleNamespace(bot_data={"knowledge": kb})


def run_coro(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_start_handler():
    # simple smoke test for /start handler
    update = DummyUpdate("")
    ctx = SimpleNamespace()
    coro = bot_main.start(update, ctx)
    asyncio.get_event_loop().run_until_complete(coro)
    assert "внутренний помощник" in update.message.last_reply.lower()


def test_topics_and_handle_text(tmp_path):
    # Prepare KB file
    kb_path = tmp_path / "kb.json"
    kb_data = {
        "meta": {},
        "topics": [
            {
                "id": "sick_leave",
                "title": "Больничные листы",
                "questions": [
                    {
                        "id": "sl-1",
                        "title": "Что делать при получении Krankmeldung",
                        "patterns": ["больничный", "krankmeldung"],
                        "keywords": ["больничный"],
                        "answer": "Передать в отдел кадров",
                        "checklist": ["Попросить оригинал"],
                        "review": "Если длительный — юрист"
                    }
                ]
            }
        ]
    }
    kb_path.write_text(json.dumps(kb_data, ensure_ascii=False))

    kb = KnowledgeBase(str(kb_path))
    # topics handler
    upd_topics = DummyUpdate("")
    ctx = DummyContext(kb)
    asyncio.get_event_loop().run_until_complete(bot_main.topics_command(upd_topics, ctx))
    assert "бол" in upd_topics.message.last_reply.lower() or "темы" in upd_topics.message.last_reply.lower()

    # handle_text should find the KB entry
    upd_q = DummyUpdate("Что делать с больничным?")
    asyncio.get_event_loop().run_until_complete(bot_main.handle_text(upd_q, ctx))
    assert "чек-лист" in (upd_q.message.last_reply or "").lower() or "передать" in (upd_q.message.last_reply or "").lower()
