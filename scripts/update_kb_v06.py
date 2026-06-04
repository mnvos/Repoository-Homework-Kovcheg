import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

# sick_leave-3: Entgeltfortzahlung
topics_map['sick_leave']['questions'].append({
    "id": "sick_leave-3",
    "title": "Entgeltfortzahlung im Krankheitsfall",
    "patterns": ["entgeltfortzahlung","lohnfortzahlung","krank bezahlt","6 wochen","entgfg",
                 "кто платит при болезни","зарплата при болезни","оплата больничного"],
    "keywords": ["entgeltfortzahlung","lohnfortzahlung","krank","6 wochen","entgfg"],
    "answer": (
        "*Entgeltfortzahlung im Krankheitsfall (§ 3 EntgFG)*\n\n"
        "Der Arbeitgeber zahlt bei Arbeitsunfähigkeit *bis zu 6 Wochen* das volle Gehalt weiter.\n\n"
        "*Voraussetzungen:* Beschäftigung seit mind. 4 Wochen. Keine Selbstverschuldung.\n\n"
        "*Pflichten des AN:* Erkrankung unverzüglich melden. Ab 2. Kalendertag: AU-Bescheinigung.\n\n"
        "*Nach 6 Wochen:* Krankenkasse zahlt Krankengeld (ca. 70% Brutto, max. 90% Netto) "
        "bis zu 78 Wochen innerhalb von 3 Jahren bei gleicher Erkrankung."
    ),
    "checklist": [
        "Krankmeldung am 1. Fehltag telefonisch mitteilen",
        "Ab 2. Kalendertag: eAU einreichen",
        "Nach 6 Wochen: Krankengeld durch Krankenkasse"
    ]
})

# baulohn-2: Mindestlohn
topics_map['baulohn']['questions'].append({
    "id": "baulohn-2",
    "title": "Mindestlohn 2026",
    "patterns": ["mindestlohn","минимальная зарплата","gesetzlicher mindestlohn","13,90","14,60"],
    "keywords": ["mindestlohn","13,90","14,60","stundenlohn"],
    "answer": (
        "*Gesetzlicher Mindestlohn (MiLoG)*\n\n"
        "Aktuell: *13,90 EUR brutto/Stunde*\n"
        "Ab 01.01.2027: *14,60 EUR brutto/Stunde*\n\n"
        "Fuer gewerbliche AN im Baugewerbe gilt der tarifliche Mindestlohn (BRTV/VTV) "
        "und liegt i.d.R. darueber.\n\n"
        "Unterschreitung: Ordnungswidrigkeit, Busssgeld bis 500.000 EUR."
    )
})

# soka_bau-2: Urlaubsberechnung Teilzeit/Elternzeit
topics_map['soka_bau']['questions'].append({
    "id": "soka_bau-2",
    "title": "SOKA-BAU Urlaubsberechnung - Teilzeit, Elternzeit, Weiterbildung",
    "patterns": ["soka urlaub berechnung","urlaubstage teilzeit soka","soka teilzeit",
                 "elternzeit urlaub soka","meisterschule urlaub","weiterbildung urlaub",
                 "расчёт отпуска сока","отпуск при неполной занятости"],
    "keywords": ["soka","urlaub","teilzeit","elternzeit","weiterbildung","meisterschule","30 tage"],
    "answer": (
        "*SOKA-BAU Urlaubsberechnung (gewerbliche AN)*\n\n"
        "Grundanspruch: 30 Arbeitstage/Jahr (Vollzeit). Schwerbehinderte: 35 Tage.\n\n"
        "*Teilzeit-Formel:*\n"
        "(Arbeitstage/Woche / 5) x 30 = Beschaeftigungstage/Monat\n"
        "Beispiele: 3 Tage/Wo = 18 Tage, 3,5 Tage/Wo = 21 Tage\n\n"
        "24.12. und 31.12.: arbeitsfreie, unbezahlte Tage. AG/AN koennen je 1 Urlaubstag einsetzen.\n\n"
        "*Elternzeit:* Ansprueche verfallen nicht. Resturlaub -> Uebertrag ins Folgejahr.\n\n"
        "*Meisterschule (ruhendes AV):* Kein Abgeltungsanspruch. Resturlaub -> Uebertrag Folgejahr. "
        "Bei Verfall: Entschaedigungsanspruch ggue. SOKA-BAU."
    ),
    "checklist": [
        "Wochenstunden pruefen und Teilzeit-Formel anwenden",
        "Bei Elternzeit: Resturlaub dokumentieren",
        "Fuer 24.12./31.12.: Einigung mit AN",
        "Bei Meisterschule: SOKA-BAU ueber Ruhen informieren"
    ]
})

# soka_bau-3: Berufsbildung
topics_map['soka_bau']['questions'].append({
    "id": "soka_bau-3",
    "title": "SOKA-BAU Berufsbildungsverfahren - Beitraege und Erstattungen fuer Azubis",
    "patterns": ["soka ausbildung","berufsbildung soka","azubi soka","ausbildungskosten erstattung",
                 "ueberbetriebliche ausbildung","возмещение обучения сока","взносы за учеников"],
    "keywords": ["berufsbildung","ausbildung","azubi","erstattung","soka","1,9"],
    "answer": (
        "*SOKA-BAU Berufsbildungsverfahren*\n\n"
        "Beitrag: 1,9% des Bruttolohns aller gewerblichen AN (ab 01.07.2025; vorher 2,2%)\n\n"
        "Azubi-Anmeldung: einmalig mit Ausbildungsvertrag bei SOKA-BAU.\n\n"
        "Erstattung Ausbildungsverguetung:\n"
        "- 1. Lehrjahr: 10 Monate erstattet\n"
        "- 2. Lehrjahr: 6 Monate erstattet\n"
        "- 3. Lehrjahr: 1 Monat erstattet\n\n"
        "Zusaetzlich: ueberbetriebliche Ausbildungskosten (Tagewerke + Internatsunterbringung) grossteils erstattet."
    ),
    "checklist": [
        "Ausbildungsvertrag bei SOKA-BAU anmelden",
        "Bruttoloeohne korrekt melden (1,9%)",
        "Erstattungsantraege nach Lehrjahr stellen"
    ]
})

# bg_bau-2: Unfallanzeige
topics_map['bg_bau']['questions'].append({
    "id": "bg_bau-2",
    "title": "Arbeitsunfall - Unfallanzeige, Meldepflichten, Erste Hilfe",
    "patterns": ["unfallanzeige","arbeitsunfall melden","unfallmeldung","erste hilfe baustelle",
                 "meldepflicht unfall","сообщить о несчастном случае","производственная травма","первая помощь"],
    "keywords": ["unfall","unfallanzeige","meldepflicht","erste hilfe","durchgangsarzt","d-arzt","dguv"],
    "answer": (
        "*Arbeitsunfall - Meldepflichten und Erste Hilfe*\n\n"
        "Meldepflichten:\n"
        "- Jeder Unfall sofort dem Arbeitgeber melden\n"
        "- AU > 3 Tage oder Tod: Unfallanzeige BG BAU binnen 3 Tagen\n"
        "- Massenunfall: Sofortmeldung\n"
        "- Meldeweg: DGUV-Portal oder Post\n\n"
        "Erste-Hilfe-Schritte:\n"
        "1. Schwere Verletzung: Notruf 112\n"
        "2. Ersthelfer informieren\n"
        "3. Erste Hilfe im Verbandbuch dokumentieren\n"
        "4. D-Arzt aufsuchen (nicht Hausarzt)\n"
        "5. Arzt ueber Arbeitsunfall informieren (Abrechnung ueber BG BAU)\n"
        "6. HR / Fuehrungskraft sofort informieren\n\n"
        "Herzinfarkt im Buero ohne aeussere Ursache = kein Arbeitsunfall."
    ),
    "checklist": [
        "Notruf 112 bei schweren Verletzungen",
        "Unfall sofort HR melden",
        "Verbandbuch ausfuellen",
        "D-Arzt aufsuchen (nicht Hausarzt)",
        "Unfallanzeige BG BAU innerhalb 3 Tagen (AU > 3 Tage)"
    ]
})

# Neue Themen
new_topics = [
    {
        "id": "agg",
        "title": "AGG - Gleichbehandlung / Diskriminierungsschutz",
        "questions": [{
            "id": "agg-1",
            "title": "AGG - Diskriminierungsschutz im Arbeitsverhaltnis",
            "patterns": ["agg","diskriminierung","gleichbehandlung","benachteiligung",
                         "allgemeines gleichbehandlungsgesetz","дискриминация","равное обращение"],
            "keywords": ["agg","diskriminierung","benachteiligung","gleichbehandlung",
                         "geschlecht","religion","alter","behinderung","rasse"],
            "answer": (
                "*Allgemeines Gleichbehandlungsgesetz (AGG)*\n\n"
                "Verbietet Benachteiligungen im Arbeitsverhaeltnis aufgrund von:\n"
                "- Rasse und ethnische Herkunft\n"
                "- Geschlecht\n"
                "- Religion oder Weltanschauung\n"
                "- Behinderung\n"
                "- Alter\n"
                "- Sexuelle Identitaet\n\n"
                "Geltungsbereich: Bewerbung, Einstellung, Arbeitsbedingungen, Befoerderung, Kuendigung.\n\n"
                "Beschwerderecht: AN kann sich ohne Nachteile an HR wenden.\n\n"
                "Frist: Schadensersatzansprueche innerhalb 2 Monate (§ 15 Abs. 4 AGG).\n\n"
                "Diskriminierende Stellenausschreibungen (z.B. 'jung und dynamisch') sind unzulaessig."
            ),
            "checklist": [
                "Stellenausschreibungen auf diskriminierende Formulierungen pruefen",
                "Keine Fragen zu Alter/Herkunft/Familienplanung im Vorstellungsgespraech",
                "AGG-Beschwerden dokumentieren",
                "Reaktionsfrist: 2 Monate"
            ]
        }]
    },
    {
        "id": "ausbildungsverguetung",
        "title": "Ausbildungsverguetungen im Baugewerbe",
        "questions": [{
            "id": "ausbildung-1",
            "title": "Ausbildungsverguetungen im Baugewerbe - aktuelle Betraege",
            "patterns": ["ausbildungsverguetung","ausbildungsgehalt","azubi gehalt",
                         "lehrlingsvergutung","зарплата ученика","lehrjahr verguetung"],
            "keywords": ["ausbildung","azubi","lehrjahr","verguetung","gewerblich","kaufmaennisch","feuerungstechnik"],
            "answer": (
                "*Ausbildungsverguetungen Baugewerbe (tariflich)*\n\n"
                "Gewerbliche Ausbildung:\n"
                "- 1. Lehrjahr: 1.122 EUR\n"
                "- 2. Lehrjahr: 1.351 EUR\n"
                "- 3. Lehrjahr: 1.610 EUR\n"
                "- 4. Lehrjahr: 1.714 EUR\n\n"
                "Feuerungstechnik:\n"
                "- 1. Lehrjahr: 1.122 EUR\n"
                "- 2. Lehrjahr: 1.395 EUR\n"
                "- 3. Lehrjahr: 1.719 EUR\n\n"
                "Kaufmaennisch / Technisch:\n"
                "- 1. Lehrjahr: 1.122 EUR\n"
                "- 2. Lehrjahr: 1.247 EUR\n"
                "- 3. Lehrjahr: 1.507 EUR\n\n"
                "Teil der Kosten wird ueber SOKA-BAU Berufsbildungsverfahren erstattet."
            )
        }]
    },
    {
        "id": "zvk_tarifrente",
        "title": "ZVK - Tarifrente Bau (Betriebliche Altersvorsorge)",
        "questions": [{
            "id": "zvk-1",
            "title": "ZVK / Tarifrente Bau - betriebliche Altersvorsorge",
            "patterns": ["zvk","tarifrente","betriebliche altersvorsorge bau","tza bau",
                         "altersvorsorge baugewerbe","пенсия строители","bav bau"],
            "keywords": ["zvk","tarifrente","altersvorsorge","tza","rente","3,2","betriebsrente"],
            "answer": (
                "*ZVK - Tarifrente Bau*\n\n"
                "Verwaltet durch ZVK der SOKA-BAU. Rechtsgrundlage: TZA Bau 2018 (allgemeinverbindlich).\n\n"
                "Finanzierung: ausschliesslich durch Arbeitgeber, kein AN-Beitrag.\n\n"
                "Beitragssaetze ab 01.07.2025:\n"
                "- Gewerbliche AN West: 3,2% des Bruttolohns\n"
                "- Gewerbliche AN Ost: 1,7% des Bruttolohns\n"
                "- Angestellte West: 42,50 EUR/Monat\n"
                "- Auszubildende: 20,00 EUR/Monat (bundesweit)\n\n"
                "Leistungen:\n"
                "- Lebenslange Altersrente oder Kapitalabfindung\n"
                "- Erwerbsminderungsrente\n"
                "- Hinterbliebenenrente\n\n"
                "Abrechnung monatlich ueber SOKA-BAU-Portal."
            ),
            "checklist": [
                "Beitragssatz: West 3,2% / Ost 1,7% (gewerblich)",
                "Angestellte: 42,50 EUR/Monat",
                "Azubis: 20,00 EUR/Monat",
                "Abrechnung ueber SOKA-BAU-Portal"
            ]
        }]
    },
    {
        "id": "dsgvo",
        "title": "DSGVO im Arbeitsverhaeltnis / Datenschutz",
        "questions": [{
            "id": "dsgvo-1",
            "title": "DSGVO im Arbeitsverhaeltnis - Bewerberdaten, Personalakte, Aufbewahrungsfristen",
            "patterns": ["dsgvo","datenschutz","personalakte einsicht","bewerberdaten loeschen",
                         "aufbewahrungsfrist personalakte","bdsg","защита данных","личное дело","сроки хранения"],
            "keywords": ["dsgvo","datenschutz","personalakte","aufbewahrung","bewerber","loeschung","bdsg"],
            "answer": (
                "*DSGVO im Arbeitsverhaeltnis - § 26 BDSG*\n\n"
                "Bewerberdaten:\n"
                "- Nur erforderliche Daten erheben\n"
                "- Loeschung nach 6 Monaten (AGG-Frist)\n"
                "- Talent-Pool: nur mit Einwilligung (12-24 Monate)\n\n"
                "Personalakte:\n"
                "- Zugriff: nur HR und direkte Vorgesetzte\n"
                "- AN hat Recht auf Einsicht, Auskunft, Loeschung unrechtmaessiger Daten\n"
                "- AG darf keine Diagnose erfragen\n\n"
                "Aufbewahrungsfristen:\n"
                "- Bewerbungsunterlagen: 6 Monate\n"
                "- Lohnsteuerunterlagen: 6 Jahre\n"
                "- Sozialversicherungsdokumente: 5 Jahre\n"
                "- Arbeitsvertraege / Kuendigungen: mind. 3 Jahre nach AV-Ende\n\n"
                "Ab 01.01.2027: Entgeltunterlagen muessen elektronisch gefuehrt werden. "
                "Befreiungsantrag bis 31.12.2026 moeglich.\n\n"
                "Beschaeftigtendatengesetz (BeschDG) nach Koalitionsbruch 2024 gescheitert."
            ),
            "checklist": [
                "Bewerberdaten nach 6 Monaten loeschen",
                "Personalakten: Zugriffsrechte beschraenken",
                "Keine Diagnosen aufbewahren",
                "Bis 31.12.2026: Befreiungsantrag fuer Entgeltunterlagen pruefen"
            ]
        }]
    }
]

data['topics'].extend(new_topics)
data['meta']['version'] = "0.6"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.6")
for t in data['topics']:
    print(f"  {t['id']}: {len(t.get('questions',[]))} вопросов")
