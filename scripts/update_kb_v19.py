import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

# Новая тема: иностранные сотрудники
new_topic = {
    "id": "auslaender",
    "title": "Auslaendische Mitarbeiter — Aufenthaltstitel, Arbeitserlaubnis",
    "questions": [
        {
            "id": "auslaender-1",
            "title": "Pruefung Beschaeftigungsvoraussetzungen — Aufenthaltstitel und Arbeitserlaubnis",
            "patterns": [
                "aufenthaltstitel pruefen", "arbeitserlaubnis pruefen", "auslaender einstellung",
                "nicht-eu buerger beschaeftigung", "aufenthaltstitel gueltigkeit",
                "wiedervorlage aufenthaltstitel", "beschaeftigungsvoraussetzungen",
                "проверка вида на жительство", "разрешение на работу проверить",
                "иностранный сотрудник оформление", "срок действия внж"
            ],
            "keywords": [
                "aufenthaltstitel", "arbeitserlaubnis", "auslaender", "nicht-eu",
                "gueltigkeit", "wiedervorlage", "beschaeftigung", "drittstaatsangehoeriger"
            ],
            "answer": (
                "*Pruefung Beschaeftigungsvoraussetzungen bei auslaendischen AN*\n\n"
                "Vor und bei Einstellung zwingend pruefen:\n\n"
                "1. *Identitaet pruefen* — Reisepass oder Personalausweis einsehen und kopieren\n"
                "2. *Aufenthaltstitel pruefen* — Art des Titels und Gueltigkeit dokumentieren\n"
                "3. *Arbeitserlaubnis pruefen* — ist Beschaeftigung erlaubt? "
                "Einschraenkungen (z.B. bestimmte Branche, Stundenzahl) beachten\n"
                "4. *Gueltigkeit dokumentieren* — Ablaufdatum in Personalakte und System eintragen\n"
                "5. *Wiedervorlage einrichten* — bei befristetem Aufenthaltstitel: "
                "Erinnerung vor Ablauf setzen (mind. 4-6 Wochen vorher)\n\n"
                "*EU-Buerger:* Keine gesonderte Arbeitserlaubnis erforderlich — "
                "Personalausweis oder Reisepass genuegt.\n\n"
                "*Nicht-EU-Buerger (Drittstaatsangehoerige):* Aufenthaltstitel mit "
                "Arbeitsgenehmigung zwingend vor Beschaeftigungsbeginn vorlegen. "
                "Ohne gueltigen Titel: Beschaeftigung ist verboten — Busssgeld und Strafverfolgung moeglich.\n\n"
                "*Erlischt der Aufenthaltstitel waehrend der Beschaeftigung:* "
                "AN ist verpflichtet, den AG unverzueglich zu informieren (siehe Arbeitsvertrag § 2)."
            ),
            "checklist": [
                "Reisepass / Ausweis kopieren und zu Personalakte nehmen",
                "Aufenthaltstitel pruefen: Art, Gueltigkeit, Arbeitsgenehmigung",
                "Gueltigkeit im System dokumentieren",
                "Wiedervorlage bei befristeten Titeln einrichten (4-6 Wochen vor Ablauf)",
                "EU-Buerger: kein Sonderdokument noetig — Ausweis genuegt",
                "Nicht-EU: ohne gueltigen Titel keine Beschaeftigung starten",
                "AN auf Meldepflicht bei Aenderung des Aufenthaltsstatus hinweisen"
            ]
        }
    ]
}

data['topics'].append(new_topic)
data['meta']['version'] = "0.19"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.19")
for t in data['topics']:
    q = len(t.get('questions', []))
    if q:
        print(f"  {t['id']}: {q} вопросов")
