import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

# onboarding-13: Mitführungspflicht Ausweispapiere (SchwarzArbG)
topics_map['onboarding']['questions'].append({
    "id": "onboarding-13",
    "title": "Mitfuehrungspflicht von Ausweispapieren auf der Baustelle (SchwarzArbG)",
    "patterns": [
        "ausweis baustelle", "personalausweis mitfuehren", "pass baustelle",
        "mitfuehrungspflicht ausweis", "zoll kontrolle baustelle", "schwarzarbeitsgesetz ausweis",
        "schwarzarbeit kontrolle", "удостоверение личности стройка", "паспорт на стройке",
        "контроль таможня", "обязанность носить паспорт"
    ],
    "keywords": [
        "ausweis", "mitfuehrungspflicht", "baustelle", "zollverwaltung", "pass",
        "schwarzarbeit", "ordnungswidrigkeit", "5000 euro", "personalausweis"
    ],
    "answer": (
        "*Mitfuehrungspflicht von Ausweispapieren (§ 2a SchwarzArbG)*\n\n"
        "Alle gewerblichen Arbeitnehmer im Baugewerbe sind gesetzlich verpflichtet, "
        "waehrend der Beschaeftigung jederzeit mitzufuehren:\n"
        "- Personalausweis, oder\n"
        "- Reisepass, oder\n"
        "- Entsprechenden Ausweis- oder Passersatz\n\n"
        "Die Pflicht gilt auf dem Betriebsgelaende (Werkstatt, Bauhof, Buero), "
        "auf Baustellen und an staendig wechselnden Arbeitsstellen.\n\n"
        "*Vorlage:* Auf Verlangen der Behoerden der Zollverwaltung ist der Ausweis vorzulegen.\n\n"
        "*Folgen bei Verstoss:*\n"
        "Ordnungswidrigkeit des Arbeitnehmers — Busssgeld bis zu 5.000 EUR. "
        "Das Busssgeld traegt der Arbeitnehmer, nicht der Arbeitgeber.\n\n"
        "*Pflicht des Arbeitgebers:*\n"
        "- AN schriftlich auf die Mitfuehrungspflicht hinweisen (Hinweisformular unterschreiben lassen)\n"
        "- Kopie des Hinweises zur Personalakte nehmen\n"
        "- Bei Kontrolle durch Zoll: Hinweisdokument auf Verlangen vorlegen"
    ),
    "checklist": [
        "Hinweisformular 'Mitfuehrungspflicht Ausweispapiere' vom AN unterschreiben lassen",
        "Kopie des unterzeichneten Hinweises zur Personalakte nehmen",
        "AN muendlich informieren: Ausweis immer bei der Arbeit dabei haben",
        "Bei Zollkontrolle: Hinweisdokument aus Personalakte vorzeigen koennen"
    ]
})

data['meta']['version'] = "0.11"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.11")
for t in data['topics']:
    q = len(t.get('questions', []))
    if q:
        print(f"  {t['id']}: {q} вопросов")
