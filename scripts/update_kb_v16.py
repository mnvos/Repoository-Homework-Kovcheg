import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

topics_map['vacation']['questions'].append({
    "id": "vacation-7",
    "title": "Schwangerschaftsmeldung — HR-Prozess und Pflichtschritte",
    "patterns": [
        "schwangerschaft gemeldet prozess", "schwangere mitarbeiterin was tun",
        "schwangerschaft hr schritte", "mutterschutz checkliste arbeitgeber",
        "aufsichtsbehoerde schwangerschaft", "gefaehrdungsbeurteilung schwanger",
        "беременность сотрудница что делать", "беременность оформление работодатель",
        "шаги при беременности сотрудника", "уведомить надзорный орган беременность"
    ],
    "keywords": [
        "schwangerschaft", "mutterschutz", "gefaehrdungsbeurteilung", "aufsichtsbehoerde",
        "entbindungstermin", "beschaeftigungsverbot", "lohnbuchhaltung"
    ],
    "answer": (
        "*Schwangerschaftsmeldung — Pflichtschritte fuer HR (LK Bauservice)*\n\n"
        "Sobald eine Mitarbeiterin die Schwangerschaft mitteilt, sind folgende Schritte erforderlich:\n\n"
        "1. Schwangerschaft und voraussichtlichen Geburtstermin dokumentieren\n"
        "2. Gefaehrdungsbeurteilung pruefen / aktualisieren und Schutzmassnahmen festlegen\n"
        "3. Zustaendige Aufsichtsbehoerde informieren (in Niedersachsen: Gewerbeaufsichtsamt)\n"
        "4. Mutterschutzvorschriften umsetzen: Arbeitszeiten, Taetigkeiten, Beschaeftigungsverbote\n"
        "5. Lohnbuchhaltung informieren — Mutterschutzfristen und Entgeltabrechnung vorbereiten\n\n"
        "*Erforderliche Unterlagen:*\n"
        "- Schriftliche Mitteilung der Mitarbeiterin ueber die Schwangerschaft\n"
        "- Aerztliche Bescheinigung / Hebammenbestaetigung mit voraussichtlichem Entbindungstermin\n"
        "- Dokumentierte Gefaehrdungsbeurteilung\n"
        "- Bestaetigung der Meldung an die Aufsichtsbehoerde\n\n"
        "Vertraulichkeit: Information ueber Schwangerschaft ist vertraulich — "
        "nur an Personen weitergeben, die sie fuer ihre Arbeit benoetigen."
    ),
    "checklist": [
        "Schwangerschaft + Geburtstermin schriftlich dokumentieren",
        "Gefaehrdungsbeurteilung aktualisieren und Schutzmassnahmen festhalten",
        "Gewerbeaufsichtsamt Niedersachsen informieren",
        "Lohnbuchhaltung ueber Mutterschutzfristen informieren",
        "Beschaeftigungsverbote und Arbeitszeitregelungen sofort umsetzen",
        "Unterlagen zur Personalakte: Mitteilung, ET-Bescheinigung, Gefaehrdungsbeurteilung",
        "Vertraulichkeit wahren — kein Weitergabe ohne Notwendigkeit"
    ]
})

data['meta']['version'] = "0.16"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.16")
for t in data['topics']:
    q = len(t.get('questions', []))
    if q:
        print(f"  {t['id']}: {q} вопросов")
