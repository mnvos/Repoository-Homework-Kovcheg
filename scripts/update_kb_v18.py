import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

topics_map['onboarding']['questions'].append({
    "id": "onboarding-14",
    "title": "Checkliste Neueinstellung — erforderliche Unterlagen vom Mitarbeiter",
    "patterns": [
        "checkliste einstellung", "unterlagen neueinstellung", "dokumente neuer mitarbeiter",
        "was brauche ich bei einstellung", "einstellung unterlagen checkliste",
        "neueinstellung dokumente", "список документов при трудоустройстве",
        "документы новый сотрудник", "чеклист оформление", "что нужно при приёме"
    ],
    "keywords": [
        "checkliste", "neueinstellung", "unterlagen", "steuer-id", "sozialversicherung",
        "krankenkasse", "iban", "ulak", "aufenthaltstitel", "arbeitserlaubnis"
    ],
    "answer": (
        "*Checkliste Neueinstellung — LK Bauservice GmbH*\n\n"
        "*Pflichtunterlagen von jedem neuen Mitarbeiter:*\n"
        "- Personalausweis oder Reisepass\n"
        "- Steuer-Identifikationsnummer (Steuer-ID)\n"
        "- Sozialversicherungsnummer\n"
        "- Mitgliedsbescheinigung der Krankenkasse\n"
        "- Bankverbindung (IBAN)\n"
        "- Aktuelle Anschrift\n"
        "- Telefonnummer\n"
        "- E-Mail-Adresse (falls vorhanden)\n\n"
        "*Zusaetzlich je nach Fall:*\n"
        "- Aufenthaltstitel (bei Nicht-EU-Buerger: zwingend erforderlich)\n"
        "- Arbeitserlaubnis (falls erforderlich)\n"
        "- Nachweise ueber Qualifikationen, Zertifikate oder Fuehrerschein\n"
        "- ULAK-Nummer (falls bereits vorhanden — bei gewerblichen AN Baugewerbe)"
    ),
    "checklist": [
        "Personalausweis / Reisepass kopieren und zur Akte nehmen",
        "Steuer-ID und Sozialversicherungsnummer erfassen",
        "Krankenkassenmitgliedschaft bestaetigt? Bescheinigung einholen",
        "IBAN fuer Gehaltsabrechnung aufnehmen",
        "Nicht-EU-Buerger: Aufenthaltstitel pruefen und kopieren (Pflicht)",
        "Qualifikationsnachweise / Fuehrerschein pruefen falls stellenrelevant",
        "ULAK-Nummer erfassen falls vorhanden (gewerbliche AN)"
    ]
})

data['meta']['version'] = "0.18"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.18")
for t in data['topics']:
    q = len(t.get('questions', []))
    if q:
        print(f"  {t['id']}: {q} вопросов")
