import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

# Обновляем sick_leave-1 — добавляем WhatsApp/SMS и список данных
for q in topics_map['sick_leave']['questions']:
    if q['id'] == 'sick_leave-1':
        q['answer'] = (
            "*Krankmeldung — Pflichten des Mitarbeiters (LK Bauservice)*\n\n"
            "Bei Arbeitsunfaehigkeit unverzueglich (moeglichst vor Arbeitsbeginn) melden "
            "beim Vorgesetzten oder der Personalabteilung.\n\n"
            "*Mitzuteilen:*\n"
            "- Name\n"
            "- Beginn der Arbeitsunfaehigkeit\n"
            "- Voraussichtliche Dauer\n"
            "- Erreichbarkeit fuer Rueckfragen\n\n"
            "*Meldeweg:* Telefonisch, per SMS oder WhatsApp — sofern betrieblich zulaessig und rechtzeitig.\n\n"
            "*AU-Bescheinigung:* Bis Ende des 2. Krankheitstages (LK Bauservice). "
            "AG kann im Einzelfall auch ab dem 1. Tag verlangen.\n\n"
            "*Bei Verlaengerung:* Unverzueglich informieren und Anschlussattest nachreichen."
        )
        break

# sick_leave-5: HR-Prozess eAU, Spezialfaelle, FAQ
topics_map['sick_leave']['questions'].append({
    "id": "sick_leave-5",
    "title": "eAU-Prozess und HR-Aufgaben bei Krankmeldung — LK Bauservice",
    "patterns": [
        "eau prozess hr", "eau abrufen", "krankmeldung hr aufgaben", "eau krankenkasse abruf",
        "privatversichert krankmeldung", "auslaendischer arzt au", "eau nicht vorhanden",
        "eau checkliste personalabteilung", "процесс больничный HR", "электронный больничный процесс"
    ],
    "keywords": [
        "eau", "krankenkasse abruf", "privatversichert", "auslaendischer arzt",
        "lohnprogramm", "fehlzeiten", "wiedervorlage langzeiterkrankung"
    ],
    "answer": (
        "*eAU-Prozess und Aufgaben der Personalabteilung*\n\n"
        "*eAU (gesetzlich Versicherte):*\n"
        "Mitarbeiter gibt keine Papierbescheinigung mehr ab. "
        "HR ruft AU-Daten elektronisch bei der Krankenkasse ab — sobald Arzt die AU festgestellt und gemeldet hat.\n\n"
        "*HR-Checkliste bei Krankmeldung:*\n"
        "1. Krankmeldung dokumentieren\n"
        "2. Vorgesetzten informieren\n"
        "3. Arbeitsunfaehigkeit im Lohnprogramm erfassen\n"
        "4. eAU-Abruf bei der Krankenkasse veranlassen\n"
        "5. Rueckmeldung der Krankenkasse pruefen\n"
        "6. Fehlzeiten dokumentieren\n"
        "7. Lohnabrechnung informieren\n"
        "8. Bei Langzeiterkrankung: Wiedervorlage einrichten\n\n"
        "*Spezialfaelle:*\n"
        "- Keine eAU abrufbar: Mitarbeiter auffordern, Nachweis in Papierform vorzulegen\n"
        "- Privatversicherte: erhalten weiterhin Papierbescheinigung — muss HR vorgelegt werden\n"
        "- Auslaendischer Arzt: AU aus dem Ausland kann anerkannt werden, sofern AU ausreichend nachgewiesen; Einzelfallpruefung erforderlich\n\n"
        "*Haeufige Fragen:*\n"
        "WhatsApp-Krankmeldung OK? Ja, wenn betrieblich zulaessig und rechtzeitig.\n"
        "Papierbescheinigung noetig? Bei gesetzlich Versicherten nein — eAU reicht.\n"
        "Keine eAU? Mitarbeiter kann zur Vorlage eines Nachweises aufgefordert werden.\n"
        "Entgeltfortzahlung endet? Nach 6 Wochen fuer dieselbe Erkrankung."
    ),
    "checklist": [
        "Krankmeldung dokumentieren und Vorgesetzten informieren",
        "Arbeitsunfaehigkeit im Lohnprogramm erfassen",
        "eAU bei Krankenkasse abrufen (gesetzlich Versicherte)",
        "Privatversicherte: Papierbescheinigung einfordern",
        "Keine eAU? Mitarbeiter zur Vorlage auffordern",
        "AU aus Ausland: Einzelfallpruefung durchfuehren",
        "Bei Langzeiterkrankung (> 6 Wochen): Wiedervorlage einrichten"
    ]
})

data['meta']['version'] = "0.23"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.23")
for t in data['topics']:
    q = len(t.get('questions', []))
    if q:
        print(f"  {t['id']}: {q} вопросов")
