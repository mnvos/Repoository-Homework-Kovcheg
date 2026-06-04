import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

topics_map['auslaender']['questions'].append({
    "id": "auslaender-3",
    "title": "Beschaeftigung von EU-Buergern — keine Arbeitserlaubnis erforderlich",
    "patterns": [
        "eu buerger beschaeftigung", "eu buerger einstellung", "eu buerger arbeitserlaubnis",
        "eu mitarbeiter dokumente", "ewr buerger", "eu buerger aufenthaltstitel",
        "граждане ес трудоустройство", "гражданин евросоюза разрешение на работу",
        "ес гражданин нужна ли виза", "eu buerger personalakte"
    ],
    "keywords": [
        "eu", "ewr", "europaeische union", "arbeitserlaubnis", "aufenthaltstitel",
        "eu buerger", "personalausweis eu"
    ],
    "answer": (
        "*Beschaeftigung von EU-Buergern — LK Bauservice*\n\n"
        "Gilt fuer Staatsbuerger der EU-Mitgliedstaaten sowie des EWR (Island, Norwegen, Liechtenstein).\n\n"
        "*Keine besonderen Voraussetzungen:*\n"
        "EU-Buerger benoetigen weder Arbeitserlaubnis noch Aufenthaltstitel. "
        "Die Einstellung erfolgt wie bei deutschen Arbeitnehmern.\n\n"
        "*Erforderliche Unterlagen (wie bei deutschen AN):*\n"
        "- Gueltiger Personalausweis oder Reisepass (Kopie zur Akte)\n"
        "- Deutsche Anschrift\n"
        "- Steuer-ID (vorhanden oder beantragt)\n"
        "- Sozialversicherungsnummer (vorhanden oder beantragt)\n"
        "- Krankenkasse gewaehlt\n\n"
        "*Personalakte:*\n"
        "Ausweiskopie, Steuer-ID, Krankenkasse, Sozialversicherungsdaten, Arbeitsvertrag."
    ),
    "checklist": [
        "Personalausweis oder Reisepass kopieren",
        "Deutsche Anschrift erfassen",
        "Steuer-ID und SV-Nummer aufnehmen (ggf. beantragen lassen)",
        "Krankenkassenwahl bestaetigen",
        "Kein Aufenthaltstitel, keine Arbeitserlaubnis erforderlich",
        "Einstellung wie bei deutschem AN durchfuehren"
    ]
})

data['meta']['version'] = "0.26"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.26")
