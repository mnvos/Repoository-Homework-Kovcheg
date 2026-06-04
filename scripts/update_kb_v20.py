import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

topics_map['onboarding']['questions'].append({
    "id": "onboarding-15",
    "title": "Arbeitsvertrag-Checkliste — Unterzeichnung und Personalakte",
    "patterns": [
        "arbeitsvertrag checkliste", "vertrag unterschreiben einstellung",
        "personalakte anlegen", "arbeitsvertrag kopie", "lohnbuchhaltung anmelden",
        "einstellung abschluss checkliste", "vertragsdaten pruefen",
        "чеклист трудовой договор", "личное дело завести", "подписать трудовой договор"
    ],
    "keywords": [
        "arbeitsvertrag", "checkliste", "personalakte", "lohnbuchhaltung",
        "unterschrift", "datenschutz", "einstellungsbogen", "unterweisung"
    ],
    "answer": (
        "*Arbeitsvertrag-Checkliste bei Neueinstellung — LK Bauservice*\n\n"
        "Folgende Schritte sind bei jeder Einstellung abzuschliessen:\n\n"
        "1. Arbeitsvertrag erstellen und Vertragsdaten pruefen\n"
        "2. Mitarbeiter unterschreibt:\n"
        "   - Arbeitsvertrag\n"
        "   - Datenschutz- / Geheimhaltungsvereinbarung\n"
        "   - Unterweisung (Sicherheitsunterweisung)\n"
        "   - Einstellungsbogen (§ 2 BRTV bei gewerblichen AN)\n"
        "   - Hinweis Befreiung von der Rentenversicherungspflicht (bei Minijob)\n"
        "3. Arbeitgeber unterschreibt dieselben Dokumente\n"
        "4. Anmeldeinformationen sofort an die Lohnbuchhalterin weitergeben\n"
        "5. Kopie des Arbeitsvertrags an den Mitarbeiter aushaendigen\n"
        "6. Personalakte anlegen mit allen unterzeichneten Dokumenten"
    ),
    "checklist": [
        "Arbeitsvertrag erstellt und Vertragsdaten (Name, Datum, Lohn, Lohngruppe) geprueft",
        "Alle 5 Dokumente vom AN unterschreiben lassen (AV, Datenschutz, Unterweisung, Einstellungsbogen, RV-Befreiung)",
        "Alle 5 Dokumente vom AG (LK Bauservice) unterschreiben",
        "Anmeldedaten sofort an Lohnbuchhalterin uebergeben",
        "Kopie Arbeitsvertrag an Mitarbeiter aushaendigen",
        "Personalakte anlegen und alle Originale einlegen"
    ]
})

data['meta']['version'] = "0.20"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.20")
for t in data['topics']:
    q = len(t.get('questions', []))
    if q:
        print(f"  {t['id']}: {q} вопросов")
