import json
from pathlib import Path

from bot.knowledge import KnowledgeBase


def test_load_and_search(tmp_path):
    p = tmp_path / "kb.json"
    kb_data = {
        "meta": {"project": "test"},
        "topics": [
            {
                "id": "t1",
                "title": "Test",
                "questions": [
                    {
                        "id": "q1",
                        "title": "Hello",
                        "patterns": ["hello"],
                        "keywords": ["hi"],
                        "answer": "world",
                        "checklist": [],
                        "review": "",
                    }
                ],
            }
        ],
    }
    p.write_text(json.dumps(kb_data, ensure_ascii=False))
    kb = KnowledgeBase(str(p))
    res = kb.search("hello")
    assert res is not None
    assert res["id"] == "q1"


def test_add_update_delete(tmp_path):
    p = tmp_path / "kb.json"
    p.write_text(json.dumps({"meta": {}, "topics": [{"id": "t1", "title": "Test", "questions": []}]}))
    kb = KnowledgeBase(str(p))
    q = kb.add_question("t1", {"title": "New Q", "patterns": ["new"], "keywords": [], "answer": "a", "checklist": [], "review": ""})
    assert "id" in q
    q2 = kb.update_question(q["id"], {"answer": "b"})
    assert q2["answer"] == "b"
    ok = kb.delete_question(q["id"])
    assert ok
