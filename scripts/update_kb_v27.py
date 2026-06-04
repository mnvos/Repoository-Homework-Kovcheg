import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

topics_map['auslaender']['questions'].append({
    "id": "auslaender-4",
    "title": "Beschaeftigung von Nicht-EU-Buergern — Pflichtpruefung vor Arbeitsaufnahme",
    "patterns": [
        "nicht-eu buerger einstellung", "drittstaatsangehoeriger beschaeftigung",
        "nicht eu arbeitserlaubnis", "drittland mitarbeiter dokumente",
        "nicht eu aufenthaltstitel bau", "beschaeftigung ohne arbeitserlaubnis",
        "граждане не ес трудоустройство", "гражданин третьей страны оформление",
        "не гражданин ес разрешение на работу", "drittstaaten bau"
    ],
    "keywords": [
        "nicht-eu", "drittstaatsangehoeriger", "arbeitserlaubnis", "aufenthaltstitel",
        "drittland", "reisepass", "beschaeftigung verboten"
    ],
    "answer": (
        "*Beschaeftigung von Nicht-EU-Buergern (Drittstaatsangehoerige) — LK Bauservice*\n\n"
        "*Vor Arbeitsaufnahme zwingend pruefen:*\n"
        "- Reisepass vorhanden und gueltig\n"
        "- Aufenthaltstitel vorhanden und gueltig\n"
        "- Arbeitserlaubnis vorhanden\n"
        "- Beschaeftigung im Baugewerbe erlaubt (Nebenbestimmungen pruefen)\n"
        "- Befristung dokumentiert\n"
        "- Wiedervorlage vor Ablauf eingerichtet\n\n"
        "*Personalakte — erforderliche Dokumente:*\n"
        "- Reisepasskopie\n"
        "- Aufenthaltstitelkopie\n"
        "- Arbeitserlaubniskopie\n"
        "- Aktuelle Anschrift\n"
        "- Steuer-ID\n"
        "- Sozialversicherungsnummer\n"
        "- Krankenkassenzugehoerigkeit\n\n"
        "Beschaeftigung ohne gueltige Arbeitserlaubnis ist unzulaessig. "
        "Mitarbeiter darf erst eingesetzt werden, wenn ALLE Voraussetzungen erfuellt und dokumentiert sind."
    ),
    "checklist": [
        "Reisepass einsehen und kopieren",
        "Aufenthaltstitel pruefen: gueltig, Baugewerbe erlaubt, Nebenbestimmungen",
        "Arbeitserlaubnis pruefen und kopieren",
        "Alle Dokumente in Personalakte",
        "Ablaufdaten dokumentieren und Wiedervorlage setzen",
        "Kein Arbeitsbeginn vor vollstaendiger Dokumentation",
        "AN informieren: Aenderungen im Aufenthaltsstatus sofort melden"
    ]
})

data['meta']['version'] = "0.27"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.27")
