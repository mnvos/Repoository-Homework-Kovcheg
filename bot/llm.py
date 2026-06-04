import os
from groq import Groq
from typing import Optional

_client: Optional[Groq] = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY не задан в переменных окружения")
        _client = Groq(api_key=api_key)
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

WICHTIG — Umgang mit deutschen Fachbegriffen (gilt besonders bei russischen Antworten):
- Offizielle Dokumentennamen IMMER auf Deutsch: Personalfragebogen, Sozialversicherungsausweis, Aufenthaltserlaubnis, Arbeitserlaubnis, Steuer-ID usw. Niemals ins Russische übersetzen oder transkribieren.
- Rechtliche Begriffe und Paragraphen auf Deutsch behalten: Krankmeldung, Kündigungsfrist, Aufhebungsvertrag, § 622 BGB, BRTV, SOKA-BAU, Mindestlohn, Steuerklasse, Krankenkasse, Lohngruppe usw.
- Institutionen auf Deutsch: Krankenkasse, Finanzamt, Berufsgenossenschaft, SOKA-BAU.
- Bei erstem Vorkommen eines komplexen Begriffs kurze russische Erklärung in Klammern: Krankmeldung (справка о болезни), Aufenthaltserlaubnis (вид на жительство).
- Deutsche Eigennamen, Firmennamen, Abkürzungen nicht übersetzen: LK Bauservice, Baulohn, BRTV, BG Bau, eAU.
- Zahlen und Fristen aus der KB unverändert übernehmen.

Urlaubsabfragen — zusätzliche Pflichthinweise:
- Bei jeder Frage zu Urlaubstagen, Resturlaub oder Urlaubsanspruch: weise den Mitarbeiter darauf hin, seinen aktuellen Resturlaub in der eigenen Gehaltsabrechnung (расчётный листок) zu prüfen — dort ist der aktuelle Stand immer ausgewiesen.
- Bei Unklarheiten in der Gehaltsabrechnung: Mitarbeiter an HR oder Buchhaltung verweisen.
"""


def ask_llm(
    question: str,
    lang: str,
    kb_entry: Optional[dict] = None,
    kb_summary: Optional[str] = None,
) -> str:
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
        user_message = f"{lang_instruction}\n\nKontext aus der Wissensdatenbank:\n{context}\nFrage: {question}"
    elif kb_summary:
        # Compact overview when no direct match found
        user_message = (
            f"{lang_instruction}\n\n"
            f"Die Wissensdatenbank enthält folgende Themen (Kurzübersicht):\n{kb_summary}\n\n"
            f"Frage: {question}\n\n"
            f"Wenn die Antwort nicht eindeutig aus den obigen Themen hervorgeht, "
            f"weise den Nutzer auf /topics oder die HR-Abteilung hin."
        )
    else:
        user_message = f"{lang_instruction}\n\nFrage: {question}"

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


def build_kb_summary(kb_data: dict, max_entries: int = 10) -> str:
    """Build a compact KB summary — at most max_entries questions, 200 chars each."""
    lines = []
    count = 0
    for topic in kb_data.get("topics", []):
        for q in topic.get("questions", []):
            if count >= max_entries:
                break
            title = q.get("title", q["id"])
            answer = q.get("answer", "")
            lines.append(f"- {title}: {answer[:200]}")
            count += 1
        if count >= max_entries:
            break
    return "\n".join(lines)
