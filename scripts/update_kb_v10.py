import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

# onboarding-12: Einstellungsbogen gewerbliche AN (§ 2 BRTV)
topics_map['onboarding']['questions'].append({
    "id": "onboarding-12",
    "title": "Einstellungsbogen fuer gewerbliche Arbeitnehmer (§ 2 BRTV)",
    "patterns": [
        "einstellungsbogen", "einstellungsformular", "formular neueinstellung",
        "brtv einstellung", "gewerblicher arbeitnehmer einstellung",
        "анкета при приёме", "бланк оформления", "бланк при трудоустройстве",
        "checkliste einstellung gewerblich"
    ],
    "keywords": [
        "einstellungsbogen", "brtv", "gewerblich", "lohngruppe", "ulak",
        "einstellung formular", "stundenlohn", "aufenthaltstitel einstellung"
    ],
    "answer": (
        "*Einstellungsbogen fuer gewerbliche Arbeitnehmer (Anhang zu § 2 BRTV)*\n\n"
        "Pflichtformular bei Einstellung jedes gewerblichen AN im Baugewerbe.\n\n"
        "*Pflichtangaben im Bogen:*\n"
        "- Persoenliche Daten: Name, Adresse, Geburtsdatum/-ort, Staatsangehoerigkeit\n"
        "- Erlernter Beruf und vorgesehene Taetigkeit\n"
        "- Einstellungstag und Arbeitsbeginn (bei Befristung: Enddatum)\n"
        "- Lohngruppe (LG 1-6 nach BRTV) + Tarif- und vereinbarter Stundenlohn\n"
        "- Bankverbindung (IBAN, BIC), Steuer-ID, Rentenversicherungsnummer\n"
        "- Durchschnittliche Wochenarbeitszeit (§ 3 BRTV)\n"
        "- Ueberstunden: Anordnungsmoeglichkeit (Ja/Nein)\n"
        "- Betriebliche Altersvorsorge: ZVK AG (Tarifrente Bau) — kein Versorgungstraeger noetig\n\n"
        "*Einzureichende Unterlagen (Checkliste):*\n"
        "- Meldeschein / Arbeitnehmerkontoauszug ULAK\n"
        "- Nachweis Krankenkassenzugehoerigkeit\n"
        "- Unterlagen vermoegenswirksame Leistungen\n"
        "- Unterlagen betriebliche Altersversorgung\n"
        "- Schwerbehindertenausweis (falls vorhanden — freiwillig)\n"
        "- Ausbildungs-/Fortbildungsnachweise\n"
        "- Aufenthaltstitel / Arbeitsgenehmigung-EU (nur bei Drittstaatsangehoerigen)\n\n"
        "*Wichtige Hinweise:*\n"
        "- Kuendigung nach § 11 BRTV: 6 Werktage Frist, Schriftform erforderlich\n"
        "- Tarifliche Ausschlussfristen gelten (AN muss darauf hingewiesen werden)\n"
        "- Familienstand und Schwerbehinderung: Angabe freiwillig\n"
        "- ZVK-Tarifrente Bau: Versorgungstraeger muss nicht eingetragen werden (ZVK informiert direkt)"
    ),
    "checklist": [
        "Einstellungsbogen vollstaendig ausfuellen und von beiden Seiten unterschreiben lassen",
        "Lohngruppe (LG 1-6) korrekt festlegen",
        "IBAN, Steuer-ID und RV-Nummer eintragen",
        "ULAK-Meldeschein besorgen und einreichen",
        "Krankenkassennachweis anfordern",
        "Bei Drittstaatsangehoerigen: Aufenthaltstitel pruefen und kopieren",
        "AN auf tarifliche Ausschlussfristen hinweisen (Unterschrift auf Bogen)",
        "Einstellungsbogen zur Personalakte nehmen"
    ]
})

data['meta']['version'] = "0.10"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.10")
for t in data['topics']:
    q = len(t.get('questions', []))
    if q:
        print(f"  {t['id']}: {q} вопросов")
