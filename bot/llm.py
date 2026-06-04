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
- Wenn die Frage zu kurz oder unklar ist (z.B. nur ein Wort wie "подробнее", "mehr", "weiter"), bitte um Präzisierung: "Bitte formuliere deine Frage genauer. Worüber möchtest du mehr wissen?" (auf Russisch: "Уточни, пожалуйста — о чём именно ты хочешь узнать подробнее?"). Erfinde KEINE Antwort auf Basis des Profils allein.
- Antworte STRIKT zum Thema der gestellten Frage. Wenn die Frage über Krankmeldung ist, antworte NUR über Krankmeldung — nicht über Urlaub, Kündigung oder andere Themen.

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


def _profile_context(profile: dict, lang: str) -> str:
    if not profile:
        return ""
    ptype = profile.get("type", "")
    tenure = profile.get("tenure", "")

    type_map = {
        "gewerblich":    {"ru": "Gewerbliche Mitarbeiter (рабочий на стройке)", "de": "Gewerblicher Mitarbeiter (Baustelle)"},
        "kaufmaennisch": {"ru": "Kaufmännische Mitarbeiter (административный сотрудник)", "de": "Kaufmännischer Mitarbeiter (Büro)"},
    }
    tenure_map = {
        "new":    {"ru": "менее 6 месяцев", "de": "weniger als 6 Monate"},
        "mid":    {"ru": "6 месяцев – 2 года", "de": "6 Monate – 2 Jahre"},
        "senior": {"ru": "более 2 лет", "de": "mehr als 2 Jahre"},
    }

    ptype_str  = type_map.get(ptype, {}).get(lang, ptype)
    tenure_str = tenure_map.get(tenure, {}).get(lang, tenure)

    if lang == "ru":
        return (
            f"\nПрофиль сотрудника: {ptype_str}, стаж в LK Bauservice: {tenure_str}.\n"
            "Учитывай это при ответе:\n"
            "- Если Gewerbliche: применяй правила BRTV (отпуск 30 дней, Kündigungsfrist §11 BRTV, SOKA-BAU, Urlaubskonto через ULAK).\n"
            "- Если Kaufmännische: применяй правила BGB (§622, §4 BUrlG), пропорциональный отпуск, Resturlaub в верхнем блоке Lohnabrechnung.\n"
            "- Если стаж менее 6 месяцев: обязательно упомяни Probezeit и особые условия (сокращённый Kündigungsfrist, пропорциональный отпуск).\n"
            "- Если стаж более 2 лет: учитывай накопленный Urlaubsanspruch и удлинённые Kündigungsfristen.\n"
        )
    else:
        return (
            f"\nMitarbeiterprofil: {ptype_str}, Betriebszugehörigkeit bei LK Bauservice: {tenure_str}.\n"
            "Beachte bei der Antwort:\n"
            "- Gewerbliche: BRTV-Regeln (Urlaub 30 Tage, §11 BRTV Kündigungsfrist, SOKA-BAU, ULAK).\n"
            "- Kaufmännische: BGB-Regeln (§622, §4 BUrlG), anteiliger Urlaub, Resturlaub oben rechts in Lohnabrechnung.\n"
            "- Weniger als 6 Monate: Probezeit erwähnen, verkürzte Kündigungsfrist, anteiliger Urlaub.\n"
            "- Mehr als 2 Jahre: verlängerte Kündigungsfristen und aufgelaufener Urlaubsanspruch.\n"
        )


def ask_llm(
    question: str,
    lang: str,
    kb_entry: Optional[dict] = None,
    kb_summary: Optional[str] = None,
    profile: Optional[dict] = None,
) -> str:
    client = _get_client()

    lang_instruction = "Antworte auf Russisch." if lang == "ru" else "Antworte auf Deutsch."
    profile_ctx = _profile_context(profile or {}, lang)

    if kb_entry:
        context = (
            f"Relevanter KB-Eintrag:\n"
            f"Titel: {kb_entry.get('title', '')}\n"
            f"Antwort: {kb_entry.get('answer', '')}\n"
        )
        checklist = kb_entry.get("checklist", [])
        if checklist:
            context += "Checkliste:\n" + "\n".join(f"- {c}" for c in checklist) + "\n"
        user_message = f"{lang_instruction}{profile_ctx}\nKontext aus der Wissensdatenbank:\n{context}\nFrage: {question}"
    elif kb_summary:
        user_message = (
            f"{lang_instruction}{profile_ctx}\n"
            f"Die Wissensdatenbank enthält folgende Themen (Kurzübersicht):\n{kb_summary}\n\n"
            f"Frage: {question}\n\n"
            f"Wenn die Antwort nicht eindeutig aus den obigen Themen hervorgeht, "
            f"weise den Nutzer auf /topics oder die HR-Abteilung hin."
        )
    else:
        user_message = f"{lang_instruction}{profile_ctx}\nFrage: {question}"

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
