import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

# Новый вопрос в тему dsgvo: Datenschutzvereinbarung / Verschwiegenheit LK Bauservice
topics_map['dsgvo']['questions'].append({
    "id": "dsgvo-2",
    "title": "Datenschutz- und Geheimhaltungsvereinbarung — Zusatzvertrag LK Bauservice",
    "patterns": [
        "datenschutzvereinbarung", "geheimhaltung", "verschwiegenheit arbeitsvertrag",
        "geschaeftsgeheimnisse", "schweigepflicht mitarbeiter", "zusatzvertrag datenschutz",
        "конфиденциальность сотрудник", "соглашение о неразглашении", "защита коммерческой тайны",
        "мониторинг работы", "наблюдение за сотрудником"
    ],
    "keywords": [
        "datenschutz", "geheimhaltung", "verschwiegenheit", "geschaeftsgeheimnis",
        "geschwiegenheitspflicht", "monitoring", "ueberwachung", "geshgehg"
    ],
    "answer": (
        "*Datenschutz- und Geheimhaltungsvereinbarung (Zusatzvertrag LK Bauservice)*\n\n"
        "*1. Allgemeine Verschwiegenheit (GeschGehG):*\n"
        "AN verpflichtet sich zur Geheimhaltung aller Betriebs- und Geschaeftsgeheimnisse "
        "waehrend und nach dem Arbeitsverhaeltnis. Gilt nicht fuer allgemein zugaengliche Informationen.\n\n"
        "*2. Besondere Geheimhaltungspflichten:*\n"
        "- Gehaltshoehe, Ueberstunden, Urlaubstage, Gratifikationen: nicht gegenueber Dritten\n"
        "- Interne Organisationsstrukturen: nur mit Erlaubnis der Geschaeftsleitung\n"
        "- Vertragspartner, Preise, Preisnachlaesse: vertraulich\n\n"
        "*3. Auskunft gegenueber Behoerden:*\n"
        "Nur schriftlich, mit konkreter Behoerde, Aktenzeichen und Rechtsgrundlage. "
        "Telefonische Auskunft grundsaetzlich verboten — immer schriftliches Ersuchen anfordern.\n\n"
        "*4. Geheimhaltung nach Vertragsende:*\n"
        "Gilt weiterhin fuer: Kundenlisten, Vertraege, Mitarbeitergehaelter, Organisationsstrukturen, Preise.\n\n"
        "*5. Ueberwachung der Arbeitsleistung:*\n"
        "AG darf Servernutzung ueberwachen (Programme, Dauer, Intensitaet). "
        "Direkte Ueberwachung des AN-Rechners: nicht erlaubt.\n"
        "Private Nutzung (E-Mail, surfen, Software) waehrend der Arbeitszeit: nur mit schriftlicher AG-Zustimmung.\n\n"
        "*Rechtsfolgen bei Verstoss:* nach GeschGehG Abschnitt 2 + Schadensersatz vorbehalten."
    ),
    "checklist": [
        "Zusatzvertrag Datenschutz / Geheimhaltung bei Einstellung unterschreiben lassen",
        "Kopie zur Personalakte nehmen",
        "AN auf Verbot telefonischer Behoerdenauskunft hinweisen",
        "Geheimhaltungspflicht gilt auch nach Vertragsende — im Offboarding erinnern",
        "Private Servernutzung nur mit schriftlicher Genehmigung erlauben"
    ]
})

data['meta']['version'] = "0.13"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.13")
for t in data['topics']:
    q = len(t.get('questions', []))
    if q:
        print(f"  {t['id']}: {q} вопросов")
