import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

# vacation-5: Elternzeit
topics_map['vacation']['questions'].append({
    "id": "vacation-5",
    "title": "Elternzeit — Anspruch, Antrag, Kuendigungsschutz",
    "patterns": [
        "elternzeit", "elternzeit beantragen", "elternzeit antrag", "elternzeit kuendigungsschutz",
        "elterngeld", "elternzeit teilzeit", "elternzeit rueckkehr",
        "декретный отпуск", "отпуск по уходу за ребёнком", "elternzeit frist",
        "родительский отпуск", "elternzeit 3 jahre"
    ],
    "keywords": [
        "elternzeit", "elterngeld", "kuendigungsschutz", "teilzeit elternzeit",
        "3 jahre", "7 wochen", "13 wochen", "rueckkehr"
    ],
    "answer": (
        "*Elternzeit — Kurzinfo*\n\n"
        "*Anspruch:* Bis zu 3 Jahre Elternzeit pro Kind. Kann von Mutter und/oder Vater genommen werden.\n\n"
        "*Kuendigungsschutz:* Waehrend der gesamten Elternzeit besteht Kuendigungsschutz.\n\n"
        "*Teilzeit moeglich:* Bis zu 32 Stunden/Woche waehrend der Elternzeit.\n\n"
        "*Antrag — Fristen (schriftlich):*\n"
        "- Elternzeit bis zum 3. Geburtstag des Kindes: Antrag spaetestens 7 Wochen vorher\n"
        "- Elternzeit zwischen 3. und 8. Geburtstag: Antrag spaetestens 13 Wochen vorher\n\n"
        "*Gehalt:* Grundsaetzlich kein Gehaltsanspruch waehrend der Elternzeit. "
        "Elterngeld kann beim zustaendigen Amt beantragt werden.\n\n"
        "*Rueckkehr:* Nach der Elternzeit besteht Anspruch auf Rueckkehr zu einer "
        "gleichwertigen Beschaeftigung gemaess Arbeitsvertrag."
    ),
    "checklist": [
        "Schriftlichen Elternzeitantrag rechtzeitig erhalten (7 bzw. 13 Wochen Frist beachten)",
        "Elternzeitbeginn und -ende in Personalakte und Urlaubssystem eintragen",
        "Kuendigungsschutz waehrend Elternzeit beachten — keine ordentliche Kuendigung moeglich",
        "Bei Teilzeit waehrend Elternzeit: max. 32 Stunden/Woche, schriftliche Vereinbarung",
        "Resturlaub vor Elternzeit dokumentieren (Uebertrag nach Elternzeit)",
        "Rueckkehr: gleichwertige Stelle sicherstellen"
    ]
})

data['meta']['version'] = "0.14"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.14")
for t in data['topics']:
    q = len(t.get('questions', []))
    if q:
        print(f"  {t['id']}: {q} вопросов")
