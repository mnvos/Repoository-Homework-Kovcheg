import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Обновляем baulohn-2 (Mindestlohn) — заменяем на полную версию с таблицей
for topic in data['topics']:
    if topic['id'] == 'baulohn':
        for q in topic['questions']:
            if q['id'] == 'baulohn-2':
                q['title'] = "Mindestlohn im Bauhauptgewerbe — tarifliche Loehne LG 1-4 (ab 01.04.2026)"
                q['patterns'] = [
                    "mindestlohn", "mindestlohn bau", "tariflohn baugewerbe", "lohngruppe mindestlohn",
                    "bauhelfer stundenlohn", "минимальная зарплата строительство",
                    "тарифная ставка строители", "13,90", "15,86", "17,34", "mindestlohn 2026"
                ]
                q['keywords'] = [
                    "mindestlohn", "tariflohn", "lohngruppe", "stundenlohn", "bauhauptgewerbe",
                    "13,90", "15,86", "17,34", "18,49", "20,11", "werker", "bauhelfer"
                ]
                q['answer'] = (
                    "*Mindestlohn im Bauhauptgewerbe — LK Bauservice (ab 01.04.2026)*\n\n"
                    "*Gesetzlicher Mindestlohn (ab 01.01.2026):* 13,90 EUR/Stunde\n"
                    "Ab 01.01.2027: 14,60 EUR/Stunde\n\n"
                    "*Tarifliche Mindestloehne Bauhauptgewerbe (BRTV / TV Lohn Bau) — bundesweit:*\n"
                    "- LG 1 Werker / Bauhelfer: *15,86 EUR*\n"
                    "- Fachwerker: *17,34 EUR*\n"
                    "- Spezialbau-Facharbeiter: *18,49 EUR*\n"
                    "- Vorarbeiter / Polier: *20,11 EUR*\n\n"
                    "Der tarifliche Lohn liegt immer ueber dem gesetzlichen Mindestlohn. "
                    "Fuer gewerbliche AN im Bauhauptgewerbe sind die Tarif-Loehne massgeblich.\n\n"
                    "*FAQ:*\n"
                    "Bauhelfer mit 13,90 EUR? Nein — auch Werker fallen unter Tariflohn (mind. 15,86 EUR).\n"
                    "Gilt fuer Buero? Nein — kaufmaennische AN werden nicht nach Bau-Lohngruppen bezahlt.\n\n"
                    "*Bei jeder Einstellung pruefen:*\n"
                    "Lohngruppe korrekt? Tarifliche Zuschlaege berechnet? Aktuelle Tarife gueltig?"
                )
                q['checklist'] = [
                    "Lohngruppe nach TV Lohn Bau festlegen (LG 1 bis LG 6)",
                    "Vereinbarten Stundenlohn mit Tariflohn vergleichen",
                    "Tarifliche Zuschlaege berechnen (Ueberstunden, Nacht, Sonn-/Feiertag)",
                    "Tarif-Aenderungen regelmaessig pruefen (TV Lohn Bau wird periodisch angepasst)",
                    "Kein Bauhelfer unter 15,86 EUR/Stunde beschaeftigen"
                ]
                break
        break

data['meta']['version'] = "0.24"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.24")
