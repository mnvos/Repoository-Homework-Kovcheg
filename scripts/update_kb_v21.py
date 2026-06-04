import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/knowledge_base.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

topics_map = {t['id']: t for t in data['topics']}

topics_map['brtv']['questions'].append({
    "id": "brtv-9",
    "title": "Wer faellt unter den BRTV? Gewerbliche AN vs. kaufmaennische Angestellte",
    "patterns": [
        "wer faellt unter brtv", "brtv anwendbarkeit", "brtv gewerblich oder kaufmaennisch",
        "gilt brtv fuer mich", "brtv buero", "brtv maler elektriker",
        "кто подпадает под brtv", "brtv для каких профессий", "brtv строительные рабочие",
        "офисный сотрудник brtv", "brtv применимость"
    ],
    "keywords": [
        "brtv", "gewerblich", "kaufmaennisch", "angestellte", "maler", "helfer",
        "trockenbauer", "buero", "buchhalter", "tarifvertrag anwendung"
    ],
    "answer": (
        "*Wer faellt unter den BRTV Bau? — LK Bauservice*\n\n"
        "Bei LK Bauservice GmbH werden gewerbliche Mitarbeiter grundsaetzlich nach BRTV Bau behandelt. "
        "Bei Fragen zu Kuendigungsfristen, Urlaub, Schlechtwetterregelungen und tariflichen Anspruechen "
        "ist zunaechst von der Anwendbarkeit des BRTV auszugehen.\n\n"
        "*Typischerweise unter BRTV (gewerbliche AN):*\n"
        "- Maler\n"
        "- Helfer / Bauhelfer\n"
        "- Trockenbauer\n"
        "- Maurer\n"
        "- Fliesenleger\n"
        "- Elektriker auf Baustellen\n"
        "- Sanitaermonteure\n"
        "- Vorarbeiter (je nach Funktion)\n\n"
        "*Typischerweise NICHT unter BRTV (kaufmaennische / leitende AN):*\n"
        "- Bueroangestellte\n"
        "- Personalsachbearbeiter\n"
        "- Buchhalter\n"
        "- Assistenz der Geschaeftsfuehrung\n"
        "- Kaufmaennische Angestellte\n"
        "- Geschaeftsfuehrer\n"
        "- Viele Bauleiter und leitende Angestellte\n\n"
        "Fuer kaufmaennische Angestellte gelten die gesetzlichen Regelungen des BGB und des Arbeitsvertrags."
    ),
    "checklist": [
        "Bei Einstellung: Taetigkeit pruefen — gewerblich (BRTV) oder kaufmaennisch (BGB)?",
        "Einstellungsbogen (§ 2 BRTV) nur bei gewerblichen AN ausfuellen",
        "Kuendigungsfristen: gewerblich nach § 11 BRTV, kaufmaennisch nach § 622 BGB",
        "Urlaub: gewerblich ueber SOKA-BAU (30 Tage), kaufmaennisch nach BUrlG / Vertrag",
        "Im Zweifelsfall: Taetigkeitsbeschreibung und Lohngruppe als Entscheidungsgrundlage"
    ]
})

data['meta']['version'] = "0.21"
data['meta']['updated'] = "2026-06-04"

with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("OK - KB v0.21")
for t in data['topics']:
    q = len(t.get('questions', []))
    if q:
        print(f"  {t['id']}: {q} вопросов")
