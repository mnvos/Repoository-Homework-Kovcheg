import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

topics_map['vacation']['questions'].append({
    "id": "vacation-6",
    "title": "Mutterschutz — Fristen, Kuendigungsschutz, Mutterschaftsgeld",
    "patterns": [
        "mutterschutz", "schwangerschaft arbeit", "mutterschaftsgeld", "mutterschutzfrist",
        "schwangere kuendigungsschutz", "schutzfrist geburt", "mutterschutz melden",
        "декретный отпуск беременность", "охрана материнства", "декрет до родов",
        "беременность уведомить работодателя", "пособие по беременности"
    ],
    "keywords": [
        "mutterschutz", "schwangerschaft", "mutterschaftsgeld", "kuendigungsschutz",
        "6 wochen", "8 wochen", "12 wochen", "geburt", "fruehgeburt"
    ],
    "answer": (
        "*Mutterschutz — Kurzinfo*\n\n"
        "*Schutzfristen:*\n"
        "- 6 Wochen vor dem voraussichtlichen Geburtstermin: Beschaeftigungsverbot (auf Wunsch der AN aufhebbar)\n"
        "- 8 Wochen nach der Geburt: absolutes Beschaeftigungsverbot\n"
        "- Bei Frueh- oder Mehrlingsgeburten: Schutzfrist nach Geburt verlaengert sich auf 12 Wochen\n\n"
        "*Kuendigungsschutz:* Besonderer Kuendigungsschutz waehrend der gesamten Schwangerschaft "
        "und bis 4 Monate nach der Entbindung.\n\n"
        "*Taetigkeitsverbote:* Schwangere duerfen keine Taetigkeiten ausueben, die ihre Gesundheit "
        "oder die des Kindes gefaehrden (Gefaehrdungsbeurteilung fuer schwangere AN erforderlich).\n\n"
        "*Verguetung waehrend Mutterschutz:*\n"
        "- Mutterschaftsgeld: zahlt die Krankenkasse (max. 13 EUR/Tag)\n"
        "- AG-Zuschuss: Arbeitgeber zahlt die Differenz zum bisherigen Nettogehalt\n"
        "- Ergebnis: Nettogehalt bleibt weitgehend gesichert\n\n"
        "*Meldepflicht:* Schwangerschaft sollte dem Arbeitgeber moeglichst frueh mitgeteilt werden, "
        "damit Schutzvorschriften umgesetzt werden koennen."
    ),
    "checklist": [
        "Schwangerschaftsmeldung entgegennehmen und vertraulich behandeln (DSGVO)",
        "Gefaehrdungsbeurteilung fuer den Arbeitsplatz der Schwangeren erstellen",
        "Schutzfristen im System eintragen: -6 Wochen vor ET, +8/12 Wochen nach Geburt",
        "Kuendigungsschutz beachten: gilt ab Bekanntgabe bis 4 Monate nach Geburt",
        "AG-Zuschuss berechnen und mit Gehaltsabrechnung auszahlen",
        "Krankenversicherung der AN ueber Mutterschaftsgeld informieren lassen"
    ]
})

data['meta']['version'] = "0.15"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.15")
for t in data['topics']:
    q = len(t.get('questions', []))
    if q:
        print(f"  {t['id']}: {q} вопросов")
