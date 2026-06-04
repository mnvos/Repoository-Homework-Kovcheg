import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

topics_map['auslaender']['questions'].append({
    "id": "auslaender-2",
    "title": "Checkliste Aufenthaltstitel — Pruefung vor Arbeitsaufnahme",
    "patterns": [
        "checkliste aufenthaltstitel", "aufenthaltstitel vor arbeitsaufnahme",
        "aufenthaltstitel pruefen checkliste", "nebenbestimmungen aufenthaltstitel",
        "beschaeftigungsumfang erlaubt", "aufenthaltstitel kopie personalakte",
        "wiedervorlage aufenthaltstitel ablauf", "чеклист вид на жительство",
        "проверить внж до начала работы", "ограничения внж разрешение"
    ],
    "keywords": [
        "aufenthaltstitel", "checkliste", "nebenbestimmungen", "beschaeftigungsumfang",
        "wiedervorlage", "personalakte", "gueltigkeitsdatum", "verlaengerungspflicht"
    ],
    "answer": (
        "*Checkliste Aufenthaltstitel — LK Bauservice (vor Arbeitsaufnahme)*\n\n"
        "*Vor Arbeitsaufnahme zwingend pruefen:*\n"
        "- Gueltiger Aufenthaltstitel vorhanden?\n"
        "- Originaldokument eingesehen\n"
        "- Kopie fuer Personalakte erstellt\n"
        "- Name stimmt mit Ausweisdokument ueberein\n"
        "- Gueltigkeit geprueft\n"
        "- Nebenbestimmungen geprueft (Einschraenkungen auf Branche, Stunden, Region)\n"
        "- Beschaeftigung grundsaetzlich erlaubt?\n"
        "- Beschaeftigungsumfang (Stunden) erlaubt?\n"
        "- Befristung dokumentiert\n"
        "- Wiedervorlage vor Ablauf eingerichtet\n\n"
        "*Dokumentation in Personalakte:*\n"
        "- Kopie Aufenthaltstitel\n"
        "- Kopie Reisepass\n"
        "- Ablaufdatum im Kalender hinterlegt\n"
        "- Mitarbeiter ueber Verlaengerungspflicht informiert\n\n"
        "Ohne gueltigen Aufenthaltstitel und erforderliche Arbeitserlaubnis "
        "darf keine Beschaeftigung erfolgen."
    ),
    "checklist": [
        "Original Aufenthaltstitel einsehen und Kopie erstellen",
        "Name mit Reisepass abgleichen",
        "Nebenbestimmungen lesen: Branche, Stundenzahl, Region eingeschraenkt?",
        "Beschaeftigung UND Beschaeftigungsumfang erlaubt?",
        "Ablaufdatum dokumentieren und Wiedervorlage setzen (4-6 Wochen vorher)",
        "Reisepasskopie zur Personalakte",
        "Mitarbeiter informieren: Verlaengerung rechtzeitig beantragen",
        "Kein Arbeitsbeginn ohne gueltigen Titel"
    ]
})

data['meta']['version'] = "0.25"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.25")
for t in data['topics']:
    q = len(t.get('questions', []))
    if q:
        print(f"  {t['id']}: {q} вопросов")
