import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Обновляем brtv-1 с более полным содержанием
for topic in data['topics']:
    if topic['id'] == 'brtv':
        for q in topic['questions']:
            if q['id'] == 'brtv-1':
                q['title'] = "Kuendigungsfristen BRTV § 11 — Werktage, Tabelle, Schlechtwetter"
                q['patterns'] = [
                    "kuendigung brtv", "kuendigungsfrist baugewerbe", "brtv kuendigungsfrist",
                    "kuendigung gewerblich", "6 werktage kuendigung", "12 werktage kuendigung",
                    "schlechtwetter kuendigung", "увольнение строительные рабочие сроки",
                    "срок уведомления об увольнении строители", "brtv kuendigung probezeit"
                ]
                q['keywords'] = [
                    "kuendigung", "brtv", "werktage", "kuendigungsfrist", "schlechtwetter",
                    "monatsende", "probezeit brtv", "6 werktage", "12 werktage"
                ]
                q['answer'] = (
                    "*Kuendigungsfristen nach BRTV § 11 (gewerbliche AN Baugewerbe)*\n\n"
                    "*Allgemeine Fristen:*\n"
                    "- Bis 6 Monate Betriebszugehoerigkeit: *6 Werktage* (AG und AN)\n"
                    "- Ab 6 Monaten: *12 Werktage* (AG und AN)\n"
                    "Werktage = Mo-Sa. Sonn- und Feiertage zaehlen nicht. "
                    "Kein Monatsende erforderlich.\n\n"
                    "*Verlaengerte Fristen fuer AG (AN bleibt bei 12 Werktagen):*\n"
                    "- ab 3 Jahren: 1 Monat zum Monatsende\n"
                    "- ab 5 Jahren: 2 Monate zum Monatsende\n"
                    "- ab 8 Jahren: 3 Monate zum Monatsende\n"
                    "- ab 10 Jahren: 4 Monate zum Monatsende\n"
                    "- ab 12 Jahren: 5 Monate zum Monatsende\n"
                    "- ab 15 Jahren: 6 Monate zum Monatsende\n"
                    "- ab 20 Jahren: 7 Monate zum Monatsende\n\n"
                    "*Probezeit (erste 6 Monate):* 6 Werktage. "
                    "Keine 2-Wochen-Regelung wie § 622 BGB.\n\n"
                    "*Schriftform:* Kuendigung zwingend schriftlich + eigenhaendig unterschrieben. "
                    "Per E-Mail, WhatsApp, SMS oder Telegram: unwirksam.\n\n"
                    "*Schlechtwetterzeit (01.12. bis 31.03.):* "
                    "Keine Kuendigung wegen schlechter Witterung. "
                    "Stattdessen: Saison-Kurzarbeitergeld (S-KUG).\n\n"
                    "*Beispiele:*\n"
                    "- 4 Monate dabei → 6 Werktage\n"
                    "- 1 Jahr dabei → 12 Werktage\n"
                    "- 7 Jahre: AG kuendigt → 2 Monate zum ME; AN kuendigt → 12 Werktage\n\n"
                    "*Vor jeder Kuendigung bei LK pruefen:*\n"
                    "BRTV anwendbar? KSchG-Schutz? Schwerbehinderung? Schwangerschaft? Elternzeit? "
                    "Bei Unsicherheit: Ruecksprache mit Steuerberater oder Rechtsanwalt."
                )
                q['checklist'] = [
                    "Betriebszugehoerigkeit berechnen und richtige Frist ermitteln",
                    "AN oder AG kuendigt? Frist fuer AG bei > 3 Jahren laenger",
                    "Schriftform + eigenhaendige Unterschrift — kein WhatsApp / E-Mail",
                    "Schlechtwetterzeit 01.12.-31.03.: keine witterungsbedingte Kuendigung",
                    "KSchG pruefen: gilt ab 10 AN und 6 Monaten Betriebszugehoerigkeit",
                    "Schwangerschaft / Elternzeit / Schwerbehinderung: Sonderkuendigungsschutz"
                ]
                break
        break

data['meta']['version'] = "0.22"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.22")
