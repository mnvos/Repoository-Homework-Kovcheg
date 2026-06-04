import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

# onboarding-11: Befreiung Rentenversicherungspflicht Minijob
topics_map['onboarding']['questions'].append({
    "id": "onboarding-11",
    "title": "Minijob — Befreiung von der Rentenversicherungspflicht (§ 6 SGB VI)",
    "patterns": [
        "rentenversicherung minijob", "befreiung rentenversicherung", "minijob rente",
        "rentenversicherungspflicht minijob", "geringfügig beschäftigt rente",
        "minijob befreiungsantrag", "освобождение пенсионное страхование мини джоб",
        "мини джоб пенсия", "geringfügige beschäftigung rente"
    ],
    "keywords": [
        "minijob", "rentenversicherung", "befreiung", "geringfügig", "sgb vi",
        "befreiungsantrag", "minijob-zentrale", "pflichtbeitragszeiten"
    ],
    "answer": (
        "*Minijob — Befreiung von der Rentenversicherungspflicht (§ 6 Abs. 1b SGB VI)*\n\n"
        "Minijobber sind grundsaetzlich rentenversicherungspflichtig (Eigenbeitrag ca. 3,6% des Lohns). "
        "Auf Antrag kann der AN sich davon befreien lassen.\n\n"
        "*Befreiungsantrag:*\n"
        "- AN stellt schriftlichen Antrag beim AG (Formular: 'Antrag auf Befreiung von der Rentenversicherungspflicht')\n"
        "- AG nimmt Antrag zu den Entgeltunterlagen (§ 8 Abs. 4a BVV)\n"
        "- Antrag wird NICHT an die Minijob-Zentrale gesendet\n"
        "- Wirksamkeit: ab dem Tag des Eingangs beim AG\n\n"
        "*Wichtige Hinweise an den AN:*\n"
        "- Befreiung gilt fuer ALLE zeitgleich ausgeuebten Minijobs\n"
        "- Antrag ist bindend fuer die Dauer der Beschaeftigung — Ruecknahme nicht moeglich\n"
        "- AN muss alle anderen Minijob-AG ueber den Befreiungsantrag informieren\n"
        "- Verzicht auf Pflichtbeitragszeiten bedeutet geringere spaetere Rentenansprueche\n\n"
        "*Folge der Nicht-Befreiung (Opt-in):*\n"
        "AN zahlt 3,6% Eigenbeitrag, AG zahlt weiterhin pauschalen AG-Anteil (15%). "
        "Dafuer erwirbt AN Pflichtbeitragszeiten fuer die gesetzliche Rente."
    ),
    "checklist": [
        "Befreiungsantrag (Formular) vom AN unterschreiben lassen",
        "Eingangsdatum auf dem Antrag vermerken — ab diesem Tag gilt die Befreiung",
        "Antrag zu den Entgeltunterlagen nehmen (NICHT an Minijob-Zentrale senden)",
        "AN auf Folgen hinweisen: Merkblatt uebergeben und Kenntnisnahme bestaetigen lassen",
        "Lohnabrechnung anpassen: kein Arbeitnehmer-Rentenversicherungsbeitrag mehr"
    ]
})

data['meta']['version'] = "0.9"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.9")
for t in data['topics']:
    q = len(t.get('questions', []))
    if q:
        print(f"  {t['id']}: {q} вопросов")
