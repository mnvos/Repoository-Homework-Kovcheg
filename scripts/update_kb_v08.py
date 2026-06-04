import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

# onboarding-10: Befristeter Arbeitsvertrag + Stundenlohn
topics_map['onboarding']['questions'].append({
    "id": "onboarding-10",
    "title": "Befristeter Arbeitsvertrag mit Stundenlohn — LK Bauservice",
    "patterns": [
        "befristeter vertrag", "befristetes arbeitsverhaltnis", "befristung", "zeitvertrag",
        "stundenlohn vertrag", "срочный договор", "временный контракт", "почасовая оплата",
        "befristet eingestellt", "vertrag befristet"
    ],
    "keywords": [
        "befristet", "stundenlohn", "срочный", "временный", "befristung", "zeitarbeit",
        "probezeit befristet", "ausschlussfrist", "aufenthaltserlaubnis vertrag"
    ],
    "answer": (
        "*Befristeter Arbeitsvertrag mit Stundenlohn — LK Bauservice*\n\n"
        "*Vertragsdauer:* Befristet mit konkretem Enddatum. "
        "Automatischer Uebergang in unbefristetes AV, sobald der AN eine gueltige unbefristete Arbeitserlaubnis vorlegt.\n\n"
        "*Probezeit:* 6 Monate. Waehrend der Probezeit: Kuendigungsfrist 2 Wochen.\n"
        "Nach Probezeit: gesetzliche Kuendigungsfristen (§ 622 BGB).\n\n"
        "*Verguetung:* Stundenlohn — Abrechnung nach tatsaechlich geleisteten Stunden.\n"
        "Ueberstunden bis 10% der monatlichen Stunden sind mit dem Stundenlohn abgegolten.\n\n"
        "*Urlaub:* 24 Werktage/Jahr.\n\n"
        "*Krankmeldung:* AU-Bescheinigung bis Ende des 2. Tages der Arbeitsunfaehigkeit.\n\n"
        "*Ausschlussfrist (§ 10):* Alle Ansprueche aus dem AV muessen innerhalb von 3 Monaten "
        "nach Faelligkeit in Textform geltend gemacht werden, sonst Verfall. "
        "Ausnahme: MiLoG-Ansprueche, vorsaetzliche Pflichtverletzungen.\n\n"
        "*Aufenthaltserlaubnis-Klausel:* Erloeschen der Aufenthaltserlaubnis ist dem AG "
        "unverzueglich mitzuteilen. Bei Verstoß: Schadensersatzansprueche des AG.\n\n"
        "*Gerichtsstand:* Braunschweig.\n"
        "*Schriftformerfordernis:* Alle Aenderungen und Ergaenzungen beduerten der Schriftform."
    ),
    "checklist": [
        "Befristungsgrund und Enddatum klar im Vertrag angeben (TzBfG beachten)",
        "Stundenlohn mind. gesetzlicher Mindestlohn (aktuell 13,90 EUR/Std)",
        "Aufenthaltserlaubnis-Kopie in die Personalakte (bei ausl. AN)",
        "AN informieren: Aenderung Aufenthaltsstatus sofort melden",
        "Bei Verlaengerung: max. 3x befristet ohne Sachgrund (TzBfG § 14 Abs. 2)",
        "Voraussetzungen fuer Auto-Umwandlung in unbefristetes AV klar kommunizieren"
    ]
})

data['meta']['version'] = "0.8"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.8")
for t in data['topics']:
    print(f"  {t['id']}: {len(t.get('questions',[]))} вопросов")
