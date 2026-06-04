import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

topics_map['vacation']['questions'].append({
    "id": "vacation-8",
    "title": "Mutterschutzvorschriften — Arbeitszeiten, verbotene Taetigkeiten, Beschaeftigungsverbote",
    "patterns": [
        "mutterschutz arbeitszeit", "mutterschutz taetigkeitsverbot", "beschaeftigungsverbot schwanger",
        "mutterschutz nachtarbeit", "schwangere heben tragen", "mutterschutz gefaehrdung",
        "mutterschutz baustelle", "schwangere arbeitszeit regelung",
        "запрет работ беременная", "беременная ночная смена", "беременная тяжёлые работы",
        "запрет деятельности беременность"
    ],
    "keywords": [
        "mutterschutz", "beschaeftigungsverbot", "taetigkeitsverbot", "arbeitszeit schwanger",
        "nachtarbeit", "heben tragen", "gefaehrdungsbeurteilung", "8,5 stunden"
    ],
    "answer": (
        "*Mutterschutzvorschriften — Arbeitszeiten, Taetigkeiten, Verbote*\n\n"
        "*Arbeitszeiten:*\n"
        "- Max. 8,5 Stunden taeglich / 90 Stunden in einer Doppelwoche\n"
        "- Keine Beschaeftigung zwischen 20:00 und 06:00 Uhr (Ausnahmen sehr begrenzt)\n"
        "- Keine Sonn- und Feiertagsarbeit ohne ausdrueckliche Zustimmung + Behoerdenvoraussetzungen\n"
        "- Ausreichende Ruhepausen sicherstellen\n\n"
        "*Unzulaessige Taetigkeiten:*\n"
        "- Schwere koerperliche Arbeiten\n"
        "- Regelmaessiges Heben, Tragen, Bewegen schwerer Lasten\n"
        "- Taetigkeiten mit erhoehter Unfallgefahr (z.B. Absturzgefahr — relevant auf Baustelle)\n"
        "- Arbeiten mit gesundheitsgefaehrdenden Stoffen, Strahlung, Laerm, Erschuetterungen, biologischen Arbeitsstoffen\n"
        "- Akkord-, Fliessbandarbeit oder sonstige Arbeit mit vorgeschriebenem Tempo\n\n"
        "*Beschaeftigungsverbote:*\n"
        "- 6 Wochen vor Geburt: Beschaeftigung nur auf ausdruecklichen Wunsch der Schwangeren\n"
        "- 8 Wochen nach Geburt: absolutes Beschaeftigungsverbot\n"
        "- 12 Wochen nach Geburt: bei Frueh-/Mehrlingsgeburt oder Kind mit Behinderung\n"
        "- Individuelles aerztliches Beschaeftigungsverbot: jederzeit moeglich bei Gesundheitsgefaehrdung\n\n"
        "*Pflichten des Arbeitgebers:*\n"
        "1. Gefaehrdungsbeurteilung durchfuehren / anpassen\n"
        "2. Arbeitsplatz anpassen oder andere geeignete Taetigkeit anbieten\n"
        "3. Erst wenn beides nicht moeglich: betriebliches Beschaeftigungsverbot aussprechen\n"
        "4. Arbeitsschutzsbehoerde ueber Schwangerschaft informieren"
    ),
    "checklist": [
        "Arbeitszeit pruefen: max. 8,5h/Tag, kein Nachtdienst 20-6 Uhr",
        "Baustellen-Taetigkeiten sofort pruefen: Heben/Tragen, Absturz, Laerm, Chemikalien",
        "Gefaehrdungsbeurteilung anpassen und dokumentieren",
        "Alternativen Arbeitsplatz / andere Taetigkeit anbieten bevor Verbot ausgesprochen wird",
        "Betriebliches Beschaeftigungsverbot nur als letztes Mittel",
        "Arbeitsschutzsbehoerde (Gewerbeaufsichtsamt NI) informieren"
    ]
})

data['meta']['version'] = "0.17"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.17")
for t in data['topics']:
    q = len(t.get('questions', []))
    if q:
        print(f"  {t['id']}: {q} вопросов")
