import os
import json
import anthropic
from typing import Optional

_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY не задан в переменных окружения")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


SYSTEM_PROMPT = """Du bist ein interner HR-Assistent der Firma L.K. Bauservice GmbH (Salzgitter, Deutschland).
Du arbeitest ausschließlich auf Basis der bereitgestellten Wissensdatenbank (KB).

Regeln:
- Antworte immer in der Sprache, die der Nutzer gewählt hat (ru = Russisch, de = Deutsch).
- Beantworte nur HR-Fragen (Arbeitsrecht, Verträge, Urlaub, Krankmeldung, BRTV, SOKA-BAU usw.).
- Wenn die Antwort in der KB enthalten ist, nutze sie als Grundlage.
- Erfinde keine Gesetze, Paragraphen oder Zahlen, die nicht in der KB stehen.
- Halte dich kurz und praxisnah. Nutze Aufzählungen.
- Weise bei komplexen Rechtsfragen auf Rücksprache mit Steuerberater/Anwalt hin.
- Antworte NICHT auf Fragen, die nichts mit HR / Arbeitsrecht zu tun haben.
"""


def ask_llm(
    question: str,
    lang: str,
    kb_entry: Optional[dict] = None,
    kb_summary: Optional[str] = None,
) -> str:
    """
    Отправляет вопрос в Claude.
    kb_entry  — найденная запись из KB (если есть)
    kb_summary — краткий дамп всей KB (если kb_entry не найден)
    """
    client = _get_client()

    lang_instruction = "Antworte auf Russisch." if lang == "ru" else "Antworte auf Deutsch."

    if kb_entry:
        context = (
            f"Relevanter KB-Eintrag:\n"
            f"Titel: {kb_entry.get('title', '')}\n"
            f"Antwort: {kb_entry.get('answer', '')}\n"
        )
        checklist = kb_entry.get("checklist", [])
        if checklist:
            context += "Checkliste:\n" + "\n".join(f"- {c}" for c in checklist) + "\n"
    elif kb_summary:
        context = f"Wissensdatenbank (Zusammenfassung):\n{kb_summary}\n"
    else:
        context = ""

    user_message = f"{lang_instruction}\n\nFrage: {question}"
    if context:
        user_message = f"{lang_instruction}\n\nKontext aus der Wissensdatenbank:\n{context}\nFrage: {question}"

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text


def build_kb_summary(kb_data: dict) -> str:
    """Строит краткий текстовый дамп KB для передачи в LLM как контекст."""
    lines = []
    for topic in kb_data.get("topics", []):
        lines.append(f"## {topic.get('title', topic['id'])}")
        for q in topic.get("questions", []):
            lines.append(f"### {q.get('title', q['id'])}")
            answer = q.get("answer", "")
            # Обрезаем длинные ответы чтобы не раздувать контекст
            lines.append(answer[:400] + ("..." if len(answer) > 400 else ""))
    return "\n".join(lines)
