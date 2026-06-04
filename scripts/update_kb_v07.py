import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

# vacation-3: Политика отпусков LK Bauservice (виды, правила)
topics_map['vacation']['questions'].append({
    "id": "vacation-3",
    "title": "Urlaubsarten und Sonderurlaub — LK Bauservice Urlaubspolitik",
    "patterns": [
        "urlaubsarten", "sonderurlaub", "zusatzurlaub", "urlaub geburt", "urlaub hochzeit",
        "urlaub umzug", "urlaub kind krank", "urlaub todesfall", "behinderung urlaub",
        "виды отпуска", "дополнительный отпуск", "отпуск свадьба", "отпуск переезд",
        "отпуск рождение ребёнка", "больной ребёнок отпуск"
    ],
    "keywords": [
        "sonderurlaub", "urlaubsarten", "hochzeit", "geburt", "umzug", "todesfall",
        "behinderung", "kind krank", "elternzeit", "виды отпуска"
    ],
    "answer": (
        "*Urlaubspolitik LK Bauservice — Urlaubsarten und Anspruch*\n\n"
        "*Grundurlaub:* Anzahl der Tage individuell im Arbeitsvertrag geregelt.\n\n"
        "*Wartezeit:*\n"
        "Bueroangestellte: nach 3 vollen Beschaeftigungsmonaten (dann 6 Arbeitstage).\n"
        "Gewerbliche AN: anteilig ab dem 1. Monat (2,5 Tage/Monat bei 30 Tagen/Jahr).\n\n"
        "*Sonderurlaub (mit Nachweisen, nach BGB):*\n"
        "- Umzug (betrieblich oder offiziell bedingt): 1 Tag\n"
        "- Weiterbildung zugunsten des Unternehmens: nach Absprache\n"
        "- Mutterschutz / Elternzeit bis 3 Jahre: gesetzlich geregelt\n"
        "- Geburt eines Kindes (Vater): 1 Tag\n"
        "- Heirat (eigene oder naechste Verwandte): 1 Tag\n"
        "- Pflege eines kranken Kindes: bis 10 Arbeitstage/Jahr\n"
        "- Todesfall 1. Grades (Elternteil, Ehepartner, Kind): 1 Tag\n"
        "- Schwerbehinderung: +5 Tage Zusatzurlaub/Jahr\n\n"
        "Sonderurlaub wird nur mit entsprechenden Nachweisdokumenten gewaehrt."
    ),
    "checklist": [
        "Nachweis fuer Sonderurlaub besorgen (Heiratsurkunde, Geburtsschein etc.)",
        "Antrag mindestens 14 Arbeitstage im Voraus stellen",
        "Bei Pflege krankes Kind: Attest des Kinderarztes erforderlich",
        "Schwerbehinderungsausweis kopieren und in Personalakte ablegen"
    ]
})

# vacation-4: Приказ №1 — планирование, маршруты согласования, Resturlaub
topics_map['vacation']['questions'].append({
    "id": "vacation-4",
    "title": "Urlaubsplanung und Genehmigungsprozess — Приказ №1 LK Bauservice",
    "patterns": [
        "urlaubsplanung", "urlaubsantrag genehmigung", "resturlaub", "urlaub beantragen prozess",
        "urlaubsantrag frist", "urlaubsgenehmigung", "план отпуска", "остаток отпуска",
        "заявка на отпуск", "планирование отпуска", "согласование отпуска", "resturlaub verfaellt"
    ],
    "keywords": [
        "urlaubsplanung", "resturlaub", "genehmigung", "urlaubsantrag", "urlaubskalender",
        "25 februar", "14 tage", "75 prozent", "план отпуска", "замещение"
    ],
    "answer": (
        "*Urlaubsplanung LK Bauservice — Приказ Nr. 1 (aktualisiert 22.02.2026)*\n\n"
        "*Jahresplanung:*\n"
        "Alle Mitarbeiter muessen bis 25. Februar mindestens 75% (gerne 100%) "
        "des Jahresurlaubs planen und beim Vorgesetzten einreichen.\n"
        "Antraege nach dem 28. Februar werden nur beruecksichtigt, wenn kein Konflikt mit bereits genehmigten Urlauben besteht.\n\n"
        "*Antrag muss enthalten:*\n"
        "1. Urlaubsbeginn und -ende\n"
        "2. Vertretung (1 Mitarbeiter vertritt max. 1 abwesenden Kollegen)\n\n"
        "*Max. am Stueck:* 10 Arbeitstage. Laenger nur mit Genehmigung der Geschaeftsleitung.\n\n"
        "*Genehmigungsweg:*\n"
        "- Verwaltungsmitarbeiter: Teamleiter -> Abteilungsleiter -> HR-Kадровый учет\n"
        "- Abteilungsleiter: Operativer Direktor -> HR\n"
        "- Gesamtplan: HR erstellt Uebersicht, Operativer Direktor genehmigt schriftlich\n\n"
        "*Resturlaub:*\n"
        "Bueroangestellte: verfaellt am 31. Maerz des Folgejahres.\n"
        "Gewerbliche AN (Baustelle): verfaellt nicht — Resturlaub wird von SOKA-BAU zurueckerstattet.\n\n"
        "*Frist Spontanantrag:* mindestens 14 Arbeitstage vor Urlaubsbeginn. "
        "In Ausnahmefaellen kann der Vorgesetzte auch kuerzere Fristen genehmigen."
    ),
    "checklist": [
        "Bis 25. Februar: mind. 75% Jahresurlaub planen und einreichen",
        "Vertretung im Antrag benennen",
        "Max. 10 Arbeitstage am Stueck (Ausnahmen: Geschaeftsleitung)",
        "Spontanantrag: mind. 14 Arbeitstage vorher",
        "Bueroangestellte: Resturlaub bis 31. Maerz nehmen (sonst verfaellt er)",
        "Gewerbliche AN: Resturlaub laeuft ueber SOKA-BAU weiter"
    ]
})

# Neue Thema: Referral-Programm "Приведи друга"
new_topic = {
    "id": "referral",
    "title": "Reферальная программа — Приведи друга",
    "questions": [{
        "id": "referral-1",
        "title": "Реферальная программа 'Приведи друга' — условия и выплаты",
        "patterns": [
            "referral", "reферальная программа", "приведи друга", "empfehlungsprogramm",
            "mitarbeiter empfehlen", "bonus empfehlung", "freunde empfehlen",
            "бонус за сотрудника", "вознаграждение за рекомендацию", "привести друга"
        ],
        "keywords": [
            "referral", "empfehlung", "реферал", "приведи друга", "500 euro", "800 euro",
            "bonus", "вознаграждение", "ambassador", "амбассадор"
        ],
        "answer": (
            "*Реферальная программа LK Bauservice — 'Приведи друга' (с 01.01.2026)*\n\n"
            "Любой сотрудник может рекомендовать кандидата и получить денежный бонус.\n\n"
            "*Вознаграждение за нового сотрудника — 500 EUR (брутто):*\n"
            "- 100 EUR — после завершения испытательного срока:\n"
            "  * Рабочие специальности: 7-14 дней\n"
            "  * Офис / линейные (водитель, склад): после 1-го месяца\n"
            "- 400 EUR — после достижения дохода 2.700 EUR/мес (ок. 60 дней):\n"
            "  * Офис / линейные: после 2-го месяца работы\n\n"
            "*Вознаграждение за возврат бывшего сотрудника — 800 EUR (брутто):*\n"
            "По 200 EUR в месяц на протяжении 4 месяцев.\n"
            "Если рекомендованный уходит раньше — выплаты прекращаются.\n\n"
            "*Статус Амбассадора:* при привлечении 3+ сотрудников за год — доп. бонус 1.000 EUR.\n\n"
            "*Важно:*\n"
            "- Право на выплату сохраняется даже если рекомендатель уволился\n"
            "- Кандидат не должен быть в базе компании последние 6 месяцев\n"
            "- Программа действует только для рекомендаций с января 2026 года\n"
            "- Бонус выплачивается вместе с ежемесячной зарплатой\n\n"
            "Отказ в выплате: кандидат не завершил испытательный срок, был привлечён обманными обещаниями, или уже был в базе компании."
        ),
        "checklist": [
            "Сообщить имя, телефон и должность кандидата менеджеру по персоналу",
            "Убедиться, что кандидат не был в базе LK последние 6 месяцев",
            "Рекомендации принимаются с 01.01.2026",
            "Отслеживать статус выплат в ежемесячном отчёте HR в корпоративном чате"
        ]
    }]
}

data['topics'].append(new_topic)
data['meta']['version'] = "0.7"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.7")
for t in data['topics']:
    print(f"  {t['id']}: {len(t.get('questions',[]))} вопросов")
