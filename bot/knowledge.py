import json
import re
import sqlite3
import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional


class KnowledgeBase:
    """Knowledge base loader supporting JSON files and SQLite storage.

    Path may be:
    - path to JSON file (default in repository), e.g. './data/knowledge_base.json'
    - path to SQLite file ending with '.db'
    - or URI starting with 'sqlite://' followed by a filesystem path
    """

    def __init__(self, path: str) -> None:
        self.path = Path(path) if not str(path).startswith("sqlite://") else path
        self.conn: Optional[sqlite3.Connection] = None
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        path_str = str(self.path)

        # SQLite URI
        if path_str.startswith("sqlite://") or path_str.endswith(".db"):
            # resolve DB filesystem path
            if path_str.startswith("sqlite://"):
                db_path = path_str.split("sqlite://", 1)[1] or "./data/knowledge_base.db"
            else:
                db_path = path_str

            db_file = Path(db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(str(db_file), check_same_thread=False)
            cur = self.conn.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS kb (id INTEGER PRIMARY KEY, data TEXT NOT NULL)"
            )
            self.conn.commit()

            cur.execute("SELECT data FROM kb WHERE id = 1")
            row = cur.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except Exception:
                    return {"meta": {}, "topics": []}

            # If DB is empty but JSON file exists alongside, import it
            fallback_json = Path("./data/knowledge_base.json")
            if fallback_json.exists():
                with fallback_json.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                cur.execute("INSERT INTO kb (id, data) VALUES (1, ?)", (json.dumps(data, ensure_ascii=False),))
                self.conn.commit()
                return data

            # empty default structure
            empty = {"meta": {"project": "LK HR Assistant", "version": "0.1"}, "topics": []}
            cur.execute("INSERT INTO kb (id, data) VALUES (1, ?)", (json.dumps(empty, ensure_ascii=False),))
            self.conn.commit()
            return empty

        # JSON file fallback
        json_path = Path(path_str)
        if json_path.exists():
            with json_path.open("r", encoding="utf-8") as stream:
                return json.load(stream)

        raise FileNotFoundError(f"Knowledge base file not found: {json_path}")

    def _save(self) -> None:
        """Persist current data back to the SQLite store if used."""
        if self.conn:
            cur = self.conn.cursor()
            cur.execute("UPDATE kb SET data = ? WHERE id = 1", (json.dumps(self.data, ensure_ascii=False),))
            self.conn.commit()

    def save(self) -> None:
        """Persist data to storage (SQLite or JSON file)."""
        # SQLite persistence
        if self.conn:
            return self._save()

        # JSON file persistence
        if isinstance(self.path, Path):
            with self.path.open("w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return

    def get_question(self, question_id: str) -> Optional[Dict[str, Any]]:
        for topic in self.list_topics():
            for question in topic.get("questions", []):
                if question.get("id") == question_id:
                    return {**question, "topic": topic.get("title")}
        return None

    def question_exists(self, question_id: str) -> bool:
        return self.get_question(question_id) is not None

    def add_question(self, topic_id: str, question: Dict[str, Any]) -> Dict[str, Any]:
        existing_id = question.get("id")
        if existing_id and self.question_exists(existing_id):
            raise ValueError(f"Question id already exists: {existing_id}")

        topics = self.list_topics()
        for topic in topics:
            if topic.get("id") == topic_id:
                # generate id if missing or duplicate
                if not question.get("id"):
                    import uuid

                    question["id"] = f"{topic_id}-{uuid.uuid4().hex[:8]}"
                while self.question_exists(question["id"]):
                    import uuid

                    question["id"] = f"{topic_id}-{uuid.uuid4().hex[:8]}"
                topic.setdefault("questions", []).append(question)
                self.save()
                return question
        raise ValueError(f"Topic not found: {topic_id}")

    def update_question(self, question_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if updates.get("id") and updates.get("id") != question_id and self.question_exists(updates.get("id")):
            raise ValueError(f"Question id already exists: {updates.get('id')}")

        for topic in self.list_topics():
            for idx, question in enumerate(topic.get("questions", [])):
                if question.get("id") == question_id:
                    question.update(updates)
                    topic["questions"][idx] = question
                    self.save()
                    return question
        raise ValueError(f"Question not found: {question_id}")

    def delete_question(self, question_id: str) -> bool:
        for topic in self.list_topics():
            for idx, question in enumerate(topic.get("questions", [])):
                if question.get("id") == question_id:
                    del topic["questions"][idx]
                    self.save()
                    return True
        return False

    def list_topics(self) -> List[Dict[str, Any]]:
        return self.data.get("topics", [])

    def topic_titles(self) -> str:
        topics = self.list_topics()
        items = [f"- {topic['title']}" for topic in topics]
        return "\n".join(items) if items else "Темы не найдены."

    def search(self, query: str) -> Optional[Dict[str, Any]]:
        # Normalize query
        query_text = re.sub(r"[^а-яa-z0-9 ]+", " ", query.lower())
        tokens = re.findall(r"[а-яa-z0-9]+", query_text)

        best_match = None
        best_score = 0.0

        for topic in self.list_topics():
            for question in topic.get("questions", []):
                score = 0.0
                patterns = [p.lower() for p in question.get("patterns", [])]
                keywords = [k.lower() for k in question.get("keywords", [])]
                title = question.get("title", "")
                answer = question.get("answer", "")
                text_fields = " ".join([title, answer, " ".join(patterns), " ".join(keywords)]).lower()

                # Exact pattern matches are strong signals
                for pattern in patterns:
                    if pattern in query_text:
                        score += 12

                # Keyword presence gives medium signal
                for keyword in keywords:
                    if keyword in query_text:
                        score += 6

                # Token overlap gives small score
                for token in tokens:
                    if token and token in text_fields:
                        score += 1

                # Fuzzy match title and answer using difflib ratio
                ratio_title = difflib.SequenceMatcher(None, query_text, title.lower()).ratio()
                ratio_answer = difflib.SequenceMatcher(None, query_text, answer.lower()).ratio()
                # Scale ratios to score contribution
                score += ratio_title * 8
                score += ratio_answer * 4

                # Slight boost if topic title contains tokens
                topic_title = topic.get("title", "").lower()
                for token in tokens:
                    if token and token in topic_title:
                        score += 1

                if score > best_score:
                    best_score = score
                    best_match = {**question, "topic": topic["title"], "_score": score}

        # Accept match only if score passes a conservative threshold
        if best_score >= 7.0:
            return best_match
        return None

    def question_summary(self, question: Dict[str, Any]) -> str:
        title = question.get("title", "Ответ HR-ассистента")
        answer = question.get("answer", "Информации недостаточно.")
        checklist = question.get("checklist", [])
        warning = question.get("review", "")

        text = f"*{title}*\n\n{answer}"
        if checklist:
            text += "\n\n*Чек-лист:*\n"
            for item in checklist:
                text += f"- {item}\n"
        if warning:
            text += f"\n⚠️ {warning}"
        return text

    def export_data(self) -> Dict[str, Any]:
        """Return full knowledge base data for export."""
        return self.data

    def replace_data(self, new_data: Dict[str, Any]) -> None:
        """Replace internal knowledge base with provided data and persist changes."""
        # Basic validation
        if not isinstance(new_data, dict) or "topics" not in new_data:
            raise ValueError("Invalid knowledge base structure")
        self.data = new_data
        self.save()
