import os
import asyncio
import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CallbackContext, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters,
)
from bot.knowledge import KnowledgeBase
from bot.calculators import get_kuendigung_handler, get_urlaub_handler, get_bruttonetto_handler
from bot.llm import ask_llm, build_kb_summary
from bot.admin import get_admin_handlers

logger = logging.getLogger(__name__)
LLM_ENABLED = bool(os.getenv("GROQ_API_KEY"))

# ── Тексты на двух языках ────────────────────────────────────────────────────

_GREETINGS = {
    "ru": {"привет", "здравствуй", "здравствуйте", "хай", "hi", "hello", "добрый день", "добрый вечер", "добрый утро"},
    "de": {"hallo", "hi", "guten tag", "guten morgen", "guten abend", "hey", "servus", "moin"},
}

_CAPABILITIES_TRIGGERS = {
    "ru": {"что ты умеешь", "что умеешь", "что ты можешь", "помоги", "как пользоваться", "что делаешь"},
    "de": {"was kannst du", "was machst du", "hilf mir", "wie benutze ich", "wie funktionierst du"},
}

# Фразы, которые должны перенаправлять на конкретный калькулятор
_CALC_TRIGGERS = {
    "bruttonetto": {
        "ru": ["нетто", "нетто зарплат", "брутто нетто", "зарплата на руки", "сколько получу", "сколько останется",
               "налог с зарплаты", "подоходный налог", "steuerklasse", "lohnsteuer", "kalkulier", "посчитай зарплату",
               "посчитаем зарплату", "посчитаем нетто", "калькулятор зарплат", "калькулятор"],
        "de": ["netto", "brutto netto", "lohnsteuer", "steuerklasse", "nettogehalt", "was bleibt", "rechner gehalt"],
    },
    "kuendigung": {
        "ru": ["срок увольнения", "срок уведомления", "kündigungsfrist", "когда уволиться", "сколько отрабатывать",
               "отработка", "калькулятор увольнения", "уволить", "уволиться"],
        "de": ["kündigungsfrist", "wie lange kündigung", "kündigungsrechner", "probezeit kündigung"],
    },
    "urlaub": {
        "ru": ["остаток отпуска", "сколько отпуска", "дней отпуска осталось", "калькулятор отпуска",
               "resturlaub", "посчитай отпуск"],
        "de": ["resturlaub", "urlaubsrechner", "wie viel urlaub", "urlaubstage berechnen"],
    },
}

STRINGS = {
    "ru": {
        "lang_chosen": "Выбран язык: Русский",
        "welcome": (
            "Привет! Я внутренний помощник *LK HR Assistant*.\n\n"
            "Помогу с вопросами по оформлению, больничным, отпускам и другим HR-процессам.\n\n"
            "Напиши вопрос или воспользуйся командами:\n"
            "/topics — список тем\n"
            "/kuendigung — калькулятор Kündigungsfrist\n"
            "/urlaub — калькулятор отпуска\n"
            "/bruttonetto — Brutto-Netto 2026\n"
            "/profil — моя должность и стаж\n"
            "/help — справка\n"
            "/language — сменить язык"
        ),
        "help": (
            "*LK HR Assistant — Справка*\n\n"
            "Отвечаю на HR-вопросы сотрудников и отдела кадров.\n\n"
            "*Команды:*\n"
            "/start — приветствие\n"
            "/topics — список тем базы знаний\n"
            "/language — сменить язык\n\n"
            "*Калькуляторы:*\n"
            "/kuendigung — Kündigungsfrist (§ 622 BGB)\n"
            "/urlaub — остаток отпуска\n"
            "/bruttonetto — Brutto-Netto 2026 (Niedersachsen)\n\n"
            "/cancel — отменить калькулятор\n\n"
            "Пример: «Krankmeldung — что делать?»"
        ),
        "topics_header": "Доступные темы:\n",
        "not_found": (
            "Ничего не нашёл по этому запросу.\n\n"
            "Попробуй сформулировать иначе или обратись в отдел кадров.\n\n"
            "Калькуляторы: /kuendigung /urlaub /bruttonetto"
        ),
        "greeting": (
            "Привет! Я внутренний HR-помощник LK Bauservice.\n\n"
            "Задай вопрос по теме: оформление, больничный, отпуск, увольнение, BRTV, SOKA-BAU и др.\n\n"
            "Или воспользуйся: /topics /kuendigung /urlaub /bruttonetto"
        ),
        "capabilities": (
            "Я отвечаю на HR-вопросы сотрудников LK Bauservice:\n\n"
            "• Оформление на работу\n"
            "• Больничный (Krankmeldung)\n"
            "• Отпуск (Urlaub, SOKA-BAU)\n"
            "• Увольнение (Kündigung, Aufhebungsvertrag)\n"
            "• Тарифный договор BRTV\n"
            "• Иностранные сотрудники\n"
            "• AGG, DSGVO, Mindestlohn\n\n"
            "Калькуляторы: /kuendigung /urlaub /bruttonetto\n"
            "Темы: /topics"
        ),
        "llm_error": (
            "Произошла ошибка при обработке запроса.\n\n"
            "Попробуй переформулировать или обратись в отдел кадров."
        ),
        "calc_bruttonetto": (
            "Да, у меня есть калькулятор зарплаты!\n\n"
            "Введи команду /bruttonetto — я спрошу твой Brutto-Gehalt и Steuerklasse, "
            "и рассчитаю сколько ты получишь на руки (Netto) по ставкам 2026 года."
        ),
        "calc_kuendigung": (
            "Да, у меня есть калькулятор Kündigungsfrist!\n\n"
            "Введи команду /kuendigung — я рассчитаю срок уведомления об увольнении "
            "по § 622 BGB или BRTV в зависимости от стажа."
        ),
        "calc_urlaub": (
            "Да, у меня есть калькулятор отпуска!\n\n"
            "Введи команду /urlaub — я помогу рассчитать остаток отпуска (Resturlaub) "
            "с учётом частичной занятости и даты начала работы."
        ),
    },
    "de": {
        "lang_chosen": "Sprache gewählt: 🇩🇪 Deutsch",
        "welcome": (
            "Hallo! Ich bin der interne Assistent *LK HR Assistant*.\n\n"
            "Ich helfe bei Fragen rund um Einstellung, Krankmeldung, Urlaub und andere HR-Prozesse.\n\n"
            "Stell eine Frage oder nutze die Befehle:\n"
            "/topics — Themenliste\n"
            "/kuendigung — Kündigungsfrist-Rechner\n"
            "/urlaub — Urlaubsrechner\n"
            "/bruttonetto — Brutto-Netto 2026\n"
            "/help — Hilfe\n"
            "/language — Sprache wechseln"
        ),
        "help": (
            "*LK HR Assistant — Hilfe*\n\n"
            "Ich beantworte HR-Fragen für Mitarbeiter und Personalabteilung.\n\n"
            "*Befehle:*\n"
            "/start — Begrüßung\n"
            "/topics — Themen der Wissensdatenbank\n"
            "/language — Sprache wechseln\n\n"
            "*Rechner:*\n"
            "/kuendigung — Kündigungsfrist (§ 622 BGB)\n"
            "/urlaub — Urlaubsanspruch und Resturlaub\n"
            "/bruttonetto — Brutto-Netto 2026 (Niedersachsen)\n\n"
            "/cancel — Rechner abbrechen\n\n"
            "Beispiel: \"Was tun bei Krankmeldung?\""
        ),
        "topics_header": "Verfügbare Themen:\n",
        "not_found": (
            "Ich konnte keine passende Antwort finden.\n\n"
            "Bitte die Frage anders formulieren oder die HR-Abteilung kontaktieren.\n\n"
            "Rechner: /kuendigung /urlaub /bruttonetto"
        ),
        "greeting": (
            "Hallo! Ich bin der interne HR-Assistent der LK Bauservice.\n\n"
            "Stell eine Frage zu: Einstellung, Krankmeldung, Urlaub, Kündigung, BRTV, SOKA-BAU usw.\n\n"
            "Oder nutze: /topics /kuendigung /urlaub /bruttonetto"
        ),
        "capabilities": (
            "Ich beantworte HR-Fragen der LK Bauservice Mitarbeiter:\n\n"
            "• Einstellung / Onboarding\n"
            "• Krankmeldung (Krankheit, eAU)\n"
            "• Urlaub (SOKA-BAU, Resturlaub)\n"
            "• Kündigung / Aufhebungsvertrag\n"
            "• Tarifvertrag BRTV\n"
            "• Ausländische Mitarbeiter\n"
            "• AGG, DSGVO, Mindestlohn\n\n"
            "Rechner: /kuendigung /urlaub /bruttonetto\n"
            "Themen: /topics"
        ),
        "llm_error": (
            "Bei der Verarbeitung ist ein Fehler aufgetreten.\n\n"
            "Bitte die Frage anders formulieren oder die HR-Abteilung kontaktieren."
        ),
        "calc_bruttonetto": (
            "Ja, ich habe einen Gehaltsrechner!\n\n"
            "Nutze den Befehl /bruttonetto — ich frage nach deinem Brutto-Gehalt und "
            "deiner Steuerklasse und berechne dein Netto nach den Werten von 2026."
        ),
        "calc_kuendigung": (
            "Ja, ich habe einen Kündigungsfrist-Rechner!\n\n"
            "Nutze den Befehl /kuendigung — ich berechne die Kündigungsfrist nach "
            "§ 622 BGB oder BRTV je nach Betriebszugehörigkeit."
        ),
        "calc_urlaub": (
            "Ja, ich habe einen Urlaubsrechner!\n\n"
            "Nutze den Befehl /urlaub — ich berechne den Resturlaub unter "
            "Berücksichtigung von Teilzeit und Eintrittsdatum."
        ),
    },
}


def _lang(context: CallbackContext, text: str = "") -> str:
    stored = context.user_data.get("lang", "de")
    if not text:
        return stored
    has_cyrillic = any("Ѐ" <= ch <= "ӿ" for ch in text)
    has_latin = any("a" <= ch.lower() <= "z" for ch in text)
    if has_cyrillic:
        context.user_data["lang"] = "ru"
        return "ru"
    if has_latin:
        context.user_data["lang"] = "de"
        return "de"
    return stored


def _t(context: CallbackContext, key: str) -> str:
    return STRINGS[_lang(context)][key]


def _lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("RU Русский", callback_data="lang:ru"),
        InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang:de"),
    ]])


def _main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    if lang == "ru":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Моя зарплата",      callback_data="menu:salary"),
             InlineKeyboardButton("🏖️ Мой отпуск",        callback_data="menu:vacation")],
            [InlineKeyboardButton("🤒 Я заболел",          callback_data="menu:sick"),
             InlineKeyboardButton("⏰ Мои часы",           callback_data="menu:hours")],
            [InlineKeyboardButton("📄 Мои документы",      callback_data="menu:docs"),
             InlineKeyboardButton("👷 Aufenthaltstitel",   callback_data="menu:aufenthalt")],
            [InlineKeyboardButton("🏗️ Трудовое право",     callback_data="menu:labor"),
             InlineKeyboardButton("📞 Связаться с HR",     callback_data="menu:hr")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Mein Gehalt",        callback_data="menu:salary"),
             InlineKeyboardButton("🏖️ Mein Urlaub",        callback_data="menu:vacation")],
            [InlineKeyboardButton("🤒 Ich bin krank",      callback_data="menu:sick"),
             InlineKeyboardButton("⏰ Meine Stunden",      callback_data="menu:hours")],
            [InlineKeyboardButton("📄 Meine Dokumente",    callback_data="menu:docs"),
             InlineKeyboardButton("👷 Aufenthaltstitel",   callback_data="menu:aufenthalt")],
            [InlineKeyboardButton("🏗️ Arbeitsrecht",       callback_data="menu:labor"),
             InlineKeyboardButton("📞 HR kontaktieren",    callback_data="menu:hr")],
        ])


# Ответы главного меню
_MENU_RESPONSES = {
    "salary": {
        "ru": (
            "💰 *Моя зарплата*\n\n"
            "Выбери тему или задай вопрос свободным текстом:\n\n"
            "• *Когда зарплата?* — напиши «когда будет зарплата»\n"
            "• *Почему меньше?* — напиши «почему зарплата меньше»\n"
            "• *Где Lohnabrechnung?* — напиши «где lohnabrechnung»\n"
            "• *Steuerklasse?* — напиши «какая у меня steuerklasse»\n"
            "• *Vorschuss?* — напиши «хочу аванс»\n"
            "• *Расчёт нетто* — /bruttonetto"
        ),
        "de": (
            "💰 *Mein Gehalt*\n\n"
            "Wähle ein Thema oder stell eine Frage:\n\n"
            "• *Wann kommt das Gehalt?* — schreib «wann gehalt»\n"
            "• *Warum weniger?* — schreib «warum weniger gehalt»\n"
            "• *Lohnabrechnung?* — schreib «wo ist lohnabrechnung»\n"
            "• *Steuerklasse?* — schreib «welche steuerklasse»\n"
            "• *Vorschuss?* — schreib «vorschuss beantragen»\n"
            "• *Netto berechnen* — /bruttonetto"
        ),
    },
    "vacation": {
        "ru": (
            "🏖️ *Мой отпуск*\n\n"
            "• *Остаток дней* — /urlaub (калькулятор)\n"
            "• *Сколько положено?* — напиши «сколько дней отпуска»\n"
            "• *Как подать заявку?* — напиши «как взять отпуск»\n"
            "• *SOKA-BAU?* — напиши «soka bau отпуск»\n\n"
            "📄 Актуальный Resturlaub всегда в твоём *Lohnabrechnung*."
        ),
        "de": (
            "🏖️ *Mein Urlaub*\n\n"
            "• *Resturlaub berechnen* — /urlaub (Rechner)\n"
            "• *Urlaubsanspruch?* — schreib «urlaubsanspruch»\n"
            "• *Urlaub beantragen?* — schreib «urlaubsantrag»\n"
            "• *SOKA-BAU?* — schreib «soka bau urlaub»\n\n"
            "📄 Den aktuellen Resturlaub findest du in deiner *Lohnabrechnung*."
        ),
    },
    "sick": {
        "ru": (
            "🤒 *Я заболел — что делать?*\n\n"
            "1. *Сразу сообщи* руководителю о болезни — до начала рабочего дня\n"
            "2. *С 1-го дня болезни* — оформи Krankmeldung у врача\n"
            "3. *До конца 2-го дня болезни* — врач обязан отправить eAU (электронную Krankmeldung) напрямую в Krankenkasse и работодателю\n"
            "4. Если болезнь продолжается — сообщай руководителю каждый день\n\n"
            "❓ Подробнее — напиши «krankmeldung» или «больничный»"
        ),
        "de": (
            "🤒 *Ich bin krank — was tun?*\n\n"
            "1. *Sofort* den Vorgesetzten informieren — vor Arbeitsbeginn\n"
            "2. *Ab dem 1. Krankheitstag* — Krankmeldung beim Arzt holen\n"
            "3. *Bis Ende des 2. Krankheitstages* — der Arzt sendet die eAU direkt an Krankenkasse und Arbeitgeber\n"
            "4. Bei Verlängerung — täglich den Vorgesetzten informieren\n\n"
            "❓ Mehr Infos — schreib «krankmeldung» oder «krank»"
        ),
    },
    "hours": {
        "ru": (
            "⏰ *Мои рабочие часы (BRTV)*\n\n"
            "Для сотрудников стройки (Gewerbliche) по BRTV:\n\n"
            "• *Летний период* (Sommer): 41 час в неделю\n"
            "• *Зимний период* (Winter): 38 часов в неделю\n"
            "• *Überstunden* — 10% включены в зарплату по умолчанию\n"
            "• *Zuschläge* за работу в воскресенье, праздники и ночью\n\n"
            "❓ Подробнее — напиши «рабочее время» или «arbeitszeit»"
        ),
        "de": (
            "⏰ *Meine Arbeitsstunden (BRTV)*\n\n"
            "Für gewerbliche Mitarbeiter nach BRTV:\n\n"
            "• *Sommerperiode*: 41 Stunden/Woche\n"
            "• *Winterperiode*: 38 Stunden/Woche\n"
            "• *Überstunden* — 10% sind im Lohn pauschal eingeschlossen\n"
            "• *Zuschläge* für Sonn-, Feiertags- und Nachtarbeit\n\n"
            "❓ Mehr Infos — schreib «arbeitszeit» oder «überstunden»"
        ),
    },
    "docs": {
        "ru": (
            "📄 *Мои документы*\n\n"
            "Какой документ тебе нужен?\n\n"
            "• *Lohnabrechnung* — напиши «где lohnabrechnung»\n"
            "• *Kopie Arbeitsvertrag* — напиши «копия договора»\n"
            "• *Arbeitsbescheinigung* (для Jobcenter) — напиши «arbeitsbescheinigung»\n"
            "• *Urlaubsbescheinigung* — напиши «urlaubsbescheinigung»\n"
            "• *Справка о доходах* — напиши «справка о доходах»\n\n"
            "Все запросы — через HR LK Bauservice (лично или email)"
        ),
        "de": (
            "📄 *Meine Dokumente*\n\n"
            "Welches Dokument brauchst du?\n\n"
            "• *Lohnabrechnung* — schreib «wo ist lohnabrechnung»\n"
            "• *Kopie Arbeitsvertrag* — schreib «kopie arbeitsvertrag»\n"
            "• *Arbeitsbescheinigung* (Jobcenter) — schreib «arbeitsbescheinigung»\n"
            "• *Urlaubsbescheinigung* — schreib «urlaubsbescheinigung»\n"
            "• *Einkommensbescheinigung* — schreib «einkommensbescheinigung»\n\n"
            "Alle Anfragen — über HR LK Bauservice (persönlich oder per E-Mail)"
        ),
    },
    "aufenthalt": {
        "ru": (
            "👷 *Aufenthaltstitel — вид на жительство*\n\n"
            "Напиши свой вопрос, например:\n\n"
            "• «документы иностранца»\n"
            "• «aufenthaltserlaubnis»\n"
            "• «работа без ЕС паспорта»\n"
            "• «что делать если остановил zoll»\n\n"
            "❓ Или задай вопрос свободным текстом"
        ),
        "de": (
            "👷 *Aufenthaltstitel*\n\n"
            "Stell deine Frage, zum Beispiel:\n\n"
            "• «aufenthaltserlaubnis»\n"
            "• «arbeitserlaubnis nicht-EU»\n"
            "• «was tun bei zollkontrolle»\n\n"
            "❓ Oder stell eine Frage im Freitext"
        ),
    },
    "labor": {
        "ru": (
            "🏗️ *Вопрос по трудовому праву*\n\n"
            "Задай вопрос текстом — отвечу на основе BRTV, BGB и документов LK Bauservice.\n\n"
            "Примеры:\n"
            "• «Какой срок увольнения?» → /kuendigung\n"
            "• «Что такое Ausschlussfrist?»\n"
            "• «Mindestlohn на стройке»\n"
            "• «Kündigungsschutz при беременности»"
        ),
        "de": (
            "🏗️ *Frage zum Arbeitsrecht*\n\n"
            "Stell deine Frage — ich antworte auf Basis von BRTV, BGB und LK Bauservice Dokumenten.\n\n"
            "Beispiele:\n"
            "• «Kündigungsfrist?» → /kuendigung\n"
            "• «Was ist Ausschlussfrist?»\n"
            "• «Mindestlohn Bau»\n"
            "• «Kündigungsschutz bei Schwangerschaft»"
        ),
    },
    "hr": {
        "ru": (
            "📞 *Контакты отдела кадров LK Bauservice*\n\n"
            "🏢 Peiner Straße 237, 38229 Salzgitter\n\n"
            "👩‍💼 *Яна* — Руководитель отдела персонала\n"
            "📱 [+49 151 7062 4923](tel:+4915170624923)\n"
            "✉️ y\\.tsopa@lk\\-bauservice\\.de\n\n"
            "👩‍💼 *Любовь* — Администратор кадрового учёта\n"
            "📱 [+49 160 9844 5830](tel:+4916098445830)\n"
            "✉️ personal2@lk\\-bauservice\\.de"
        ),
        "de": (
            "📞 *HR-Kontakte LK Bauservice*\n\n"
            "🏢 Peiner Straße 237, 38229 Salzgitter\n\n"
            "👩‍💼 *Jana* — Leiterin Personalwesen\n"
            "📱 [+49 151 7062 4923](tel:+4915170624923)\n"
            "✉️ y\\.tsopa@lk\\-bauservice\\.de\n\n"
            "👩‍💼 *Lyubov* — Sachbearbeiterin Personalverwaltung\n"
            "📱 [+49 160 9844 5830](tel:+4916098445830)\n"
            "✉️ personal2@lk\\-bauservice\\.de"
        ),
    },
}


# ── Профиль сотрудника ────────────────────────────────────────────────────────

_PROFILE_TYPES = {
    "gewerblich": {"ru": "👷 Рабочий на стройке (Gewerbliche)", "de": "👷 Gewerblicher Mitarbeiter (Baustelle)"},
    "kaufmaennisch": {"ru": "🗂 Административный (Kaufmännische)", "de": "🗂 Kaufmännischer Mitarbeiter (Büro)"},
}

_PROFILE_TENURES = {
    "new":    {"ru": "Менее 6 месяцев",  "de": "Weniger als 6 Monate"},
    "mid":    {"ru": "6 мес. — 2 года",  "de": "6 Monate – 2 Jahre"},
    "senior": {"ru": "Более 2 лет",      "de": "Mehr als 2 Jahre"},
}


def _profile_type_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(_PROFILE_TYPES["gewerblich"][lang],    callback_data="profile:type:gewerblich")],
        [InlineKeyboardButton(_PROFILE_TYPES["kaufmaennisch"][lang], callback_data="profile:type:kaufmaennisch")],
    ])


def _profile_tenure_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(_PROFILE_TENURES["new"][lang],    callback_data="profile:tenure:new")],
        [InlineKeyboardButton(_PROFILE_TENURES["mid"][lang],    callback_data="profile:tenure:mid")],
        [InlineKeyboardButton(_PROFILE_TENURES["senior"][lang], callback_data="profile:tenure:senior")],
    ])


def _get_profile(context: CallbackContext) -> dict:
    return context.user_data.get("profile", {})


def _profile_summary(context: CallbackContext) -> str:
    """Human-readable one-line profile for debug/display."""
    p = _get_profile(context)
    lang = _lang(context)
    ptype = _PROFILE_TYPES.get(p.get("type", ""), {}).get(lang, "?")
    tenure = _PROFILE_TENURES.get(p.get("tenure", ""), {}).get(lang, "?")
    return f"{ptype} · {tenure}"


async def _ask_profile_type(message, lang: str) -> None:
    prompt = (
        "Чтобы давать точные ответы, мне нужно знать немного о тебе.\n\n"
        "*Кто ты по должности?*"
        if lang == "ru" else
        "Um genaue Antworten zu geben, brauche ich ein paar Infos.\n\n"
        "*Was ist deine Stelle?*"
    )
    await message.reply_text(prompt, parse_mode="Markdown",
                             reply_markup=_profile_type_keyboard(lang))


async def profile_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    parts = query.data.split(":")  # profile:type:gewerblich  or  profile:tenure:new

    if parts[1] == "type":
        context.user_data.setdefault("profile", {})["type"] = parts[2]
        label = _PROFILE_TYPES[parts[2]][lang]
        tenure_prompt = (
            f"Отлично, *{label}*.\n\nКак давно ты работаешь в LK Bauservice?"
            if lang == "ru" else
            f"Super, *{label}*.\n\nWie lange arbeitest du schon bei LK Bauservice?"
        )
        await query.edit_message_text(tenure_prompt, parse_mode="Markdown",
                                      reply_markup=_profile_tenure_keyboard(lang))

    elif parts[1] == "tenure":
        context.user_data.setdefault("profile", {})["tenure"] = parts[2]
        p = _get_profile(context)
        ptype_label  = _PROFILE_TYPES.get(p.get("type", ""), {}).get(lang, "")
        tenure_label = _PROFILE_TENURES[parts[2]][lang]
        confirm = (
            f"✅ Профиль сохранён:\n*{ptype_label}* · *{tenure_label}*\n\n"
            "Теперь я буду давать ответы с учётом твоей должности и стажа.\n"
            "Изменить можно командой /profil."
            if lang == "ru" else
            f"✅ Profil gespeichert:\n*{ptype_label}* · *{tenure_label}*\n\n"
            "Ich beantworte jetzt Fragen passend zu deiner Stelle und Betriebszugehörigkeit.\n"
            "Ändern mit /profil."
        )
        await query.edit_message_text(confirm, parse_mode="Markdown")
        await query.message.reply_text(
            "Выбери раздел:" if lang == "ru" else "Wähle einen Bereich:",
            reply_markup=_main_menu_keyboard(lang),
        )

    elif parts[1] == "edit":
        await query.edit_message_text(
            "Кто ты по должности?" if lang == "ru" else "Was ist deine Stelle?",
            reply_markup=_profile_type_keyboard(lang),
        )


# ── Handlers ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Выберите язык / Bitte Sprache wählen:",
        reply_markup=_lang_keyboard(),
    )


async def language_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Выберите язык / Bitte Sprache wählen:",
        reply_markup=_lang_keyboard(),
    )


async def language_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    lang = query.data.split(":")[1]
    context.user_data["lang"] = lang
    await query.edit_message_text(STRINGS[lang]["lang_chosen"])
    await query.message.reply_text(STRINGS[lang]["welcome"], parse_mode="Markdown")
    # Если профиль ещё не заполнен — спрашиваем
    if not _get_profile(context).get("type"):
        await _ask_profile_type(query.message, lang)
    else:
        await query.message.reply_text(
            "Выбери раздел:" if lang == "ru" else "Wähle einen Bereich:",
            reply_markup=_main_menu_keyboard(lang),
        )


async def profil_command(update: Update, context: CallbackContext) -> None:
    lang = _lang(context)
    p = _get_profile(context)
    if p.get("type") and p.get("tenure"):
        current = (
            f"Твой текущий профиль:\n*{_profile_summary(context)}*\n\nИзменить:"
            if lang == "ru" else
            f"Dein aktuelles Profil:\n*{_profile_summary(context)}*\n\nÄndern:"
        )
        await update.message.reply_text(
            current, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "✏️ Изменить профиль" if lang == "ru" else "✏️ Profil ändern",
                    callback_data="profile:edit:start"
                )
            ]])
        )
    else:
        await _ask_profile_type(update.message, lang)


async def menu_command(update: Update, context: CallbackContext) -> None:
    lang = _lang(context)
    prompt = "Выбери раздел:" if lang == "ru" else "Wähle einen Bereich:"
    await update.message.reply_text(prompt, reply_markup=_main_menu_keyboard(lang))


async def menu_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    key = query.data.split(":")[1]
    response = _MENU_RESPONSES.get(key, {}).get(lang, "")
    if response:
        await query.message.reply_text(response, parse_mode="Markdown")


async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(_t(context, "help"), parse_mode="Markdown")


# ── /topics — 5 групп ────────────────────────────────────────────────────────

_TOPIC_GROUPS = [
    {
        "id": "grp_salary",
        "title": {"ru": "💰 Зарплата и выплаты",        "de": "💰 Gehalt & Zahlungen"},
        "topic_ids": ["salary", "baulohn", "lohnabrechnung_erklaerung"],
    },
    {
        "id": "grp_docs",
        "title": {"ru": "📄 Оформление и документы",     "de": "📄 Einstellung & Dokumente"},
        "topic_ids": ["onboarding", "documents", "auslaender", "dsgvo", "referral"],
    },
    {
        "id": "grp_time",
        "title": {"ru": "🏖️ Отпуск и рабочее время",    "de": "🏖️ Urlaub & Arbeitszeit"},
        "topic_ids": ["vacation", "brtv", "soka_bau", "zvk_tarifrente"],
    },
    {
        "id": "grp_health",
        "title": {"ru": "🤒 Больничный и страховки",     "de": "🤒 Krankmeldung & Versicherung"},
        "topic_ids": ["sick_leave", "krankenkassen", "bg_bau", "accidents"],
    },
    {
        "id": "grp_law",
        "title": {"ru": "⚖️ Право, семья и стройка",    "de": "⚖️ Recht, Familie & Bau"},
        "topic_ids": ["termination", "agg", "ausbildungsverguetung",
                      "zoll", "kindergeld", "familie_soziales"],
    },
]


def _groups_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(g["title"][lang], callback_data=f"tgrp:{g['id']}")]
        for g in _TOPIC_GROUPS
    ])


def _group_questions_keyboard(kb: KnowledgeBase, group_id: str, lang: str) -> InlineKeyboardMarkup:
    group = next((g for g in _TOPIC_GROUPS if g["id"] == group_id), None)
    if not group:
        return InlineKeyboardMarkup([])
    buttons = []
    for tid in group["topic_ids"]:
        topic = kb.get_topic(tid)
        if not topic:
            continue
        for q in topic.get("questions", []):
            title = q.get("title", q["id"])
            buttons.append([InlineKeyboardButton(title[:60], callback_data=f"qid:{q['id']}")])
    back_label = "◀️ Назад к разделам" if lang == "ru" else "◀️ Zurück zu Gruppen"
    buttons.append([InlineKeyboardButton(back_label, callback_data="topics:back")])
    return InlineKeyboardMarkup(buttons)


async def topics_command(update: Update, context: CallbackContext) -> None:
    lang = _lang(context)
    header = "Выбери раздел:" if lang == "ru" else "Wähle einen Bereich:"
    await update.message.reply_text(header, reply_markup=_groups_keyboard(lang))


async def topics_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    kb: KnowledgeBase = context.application.bot_data["knowledge"]
    lang = _lang(context)

    # Назад к группам
    if query.data == "topics:back":
        header = "Выбери раздел:" if lang == "ru" else "Wähle einen Bereich:"
        await query.edit_message_text(header, reply_markup=_groups_keyboard(lang))
        return

    # Клик на группу → список всех вопросов группы
    if query.data.startswith("tgrp:"):
        group_id = query.data.split(":", 1)[1]
        group = next((g for g in _TOPIC_GROUPS if g["id"] == group_id), None)
        if not group:
            return
        header = f"*{group['title'][lang]}*\n\n"
        header += "Выбери вопрос:" if lang == "ru" else "Wähle eine Frage:"
        await query.edit_message_text(
            header, parse_mode="Markdown",
            reply_markup=_group_questions_keyboard(kb, group_id, lang),
        )
        return

    # Клик на вопрос → ответ
    if query.data.startswith("qid:"):
        qid = query.data.split(":", 1)[1]
        q = kb.get_question_by_id(qid)
        if not q:
            return
        lines = [f"*{q.get('title', '')}*\n"]
        if q.get("answer"):
            lines.append(q["answer"])
        checklist = q.get("checklist", [])
        if checklist:
            lines.append("\n*Чек-лист:*" if lang == "ru" else "\n*Checkliste:*")
            lines.extend(f"✅ {c}" for c in checklist)
        review = q.get("review", "")
        if review:
            lines.append(f"\n⚠️ _{review}_")
        text = "\n".join(lines)
        if len(text) > 4000:
            text = text[:3997] + "..."
        # Найти группу вопроса для кнопки "назад"
        parent_group = next(
            (g["id"] for g in _TOPIC_GROUPS
             if any(qid.startswith(tid) or
                    any(qq.get("id") == qid
                        for qq in (kb.get_topic(tid) or {}).get("questions", []))
                    for tid in g["topic_ids"])),
            None,
        )
        back_row = []
        if parent_group:
            back_label = "◀️ Назад к вопросам" if lang == "ru" else "◀️ Zurück zu Fragen"
            back_row.append(InlineKeyboardButton(back_label, callback_data=f"tgrp:{parent_group}"))
        back_row.append(InlineKeyboardButton("🏠 Разделы" if lang == "ru" else "🏠 Gruppen",
                                             callback_data="topics:back"))
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup([back_row]))


def _is_greeting(text: str, lang: str) -> bool:
    t = text.lower().strip()
    all_greetings: set = set()
    for g in _GREETINGS.values():
        all_greetings.update(g)
    return t in all_greetings


def _is_capabilities_query(text: str, lang: str) -> bool:
    t = text.lower().strip()
    all_triggers: set = set()
    for triggers in _CAPABILITIES_TRIGGERS.values():
        all_triggers.update(triggers)
    return any(t == c or t.startswith(c) for c in all_triggers)


def _detect_calc_trigger(text: str) -> Optional[str]:
    """Return calculator key ('bruttonetto'/'kuendigung'/'urlaub') if text matches, else None."""
    t = text.lower()
    for calc_key, langs in _CALC_TRIGGERS.items():
        for triggers in langs.values():
            if any(kw in t for kw in triggers):
                return calc_key
    return None


def _feedback_keyboard(question: str, lang: str) -> InlineKeyboardMarkup:
    # Encode question snippet in callback (max 64 bytes total)
    snippet = question[:20].replace(":", "").replace("|", "")
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("👍", callback_data=f"fb:up:{snippet}"),
        InlineKeyboardButton("👎", callback_data=f"fb:down:{snippet}"),
    ]])


async def feedback_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":", 2)   # fb : up/down : snippet
    vote = parts[1]
    question_snippet = parts[2] if len(parts) > 2 else ""
    lang = _lang(context)

    if vote == "up":
        logger.info("FEEDBACK +1 | user=%s | q=%r", query.from_user.id, question_snippet)
        thanks = "👍 Спасибо, рад помочь!" if lang == "ru" else "👍 Danke, gerne!"
    else:
        logger.info("FEEDBACK -1 | user=%s | q=%r", query.from_user.id, question_snippet)
        thanks = "👎 Понял, постараюсь лучше. Обратись в HR если нужна точная информация." if lang == "ru" else "👎 Verstanden. Bitte wende dich an HR für genaue Informationen."

    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(thanks)


async def handle_text(update: Update, context: CallbackContext) -> None:
    kb: KnowledgeBase = context.application.bot_data["knowledge"]
    query = update.message.text.strip()
    lang = _lang(context, query)

    # Приветствия
    if _is_greeting(query, lang):
        await update.message.reply_text(_t(context, "greeting"))
        await update.message.reply_text(
            "Выбери раздел:" if lang == "ru" else "Wähle einen Bereich:",
            reply_markup=_main_menu_keyboard(lang),
        )
        return

    # "Что ты умеешь?"
    if _is_capabilities_query(query, lang):
        await update.message.reply_text(_t(context, "capabilities"))
        return

    # Вопросы про калькуляторы → сразу подсказываем команду
    calc_key = _detect_calc_trigger(query)
    if calc_key:
        await update.message.reply_text(_t(context, f"calc_{calc_key}"))
        return

    kb_match = kb.search(query)

    if not LLM_ENABLED:
        if not kb_match:
            await update.message.reply_text(_t(context, "not_found"))
            return
        await update.message.reply_markdown_v2(
            kb.question_summary(kb_match),
            reply_markup=_feedback_keyboard(query, lang),
        )
        return

    # Режим с LLM
    thinking_text = "⏳ Обрабатываю запрос..." if lang == "ru" else "⏳ Verarbeite Anfrage..."
    thinking_msg = await update.message.reply_text(thinking_text)

    profile = _get_profile(context)
    try:
        if kb_match:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ask_llm(query, lang, kb_entry=kb_match, profile=profile)
            )
        else:
            kb_summary = build_kb_summary(kb.export_data())
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ask_llm(query, lang, kb_summary=kb_summary, profile=profile)
            )
        await thinking_msg.edit_text(response, reply_markup=_feedback_keyboard(query, lang))
    except Exception as e:
        logger.error("LLM error: %s", e, exc_info=True)
        await thinking_msg.delete()
        if kb_match:
            await update.message.reply_markdown_v2(
                kb.question_summary(kb_match),
                reply_markup=_feedback_keyboard(query, lang),
            )
        else:
            await update.message.reply_text(_t(context, "llm_error"))


# ── App builder ───────────────────────────────────────────────────────────────

def build_application(token: str, knowledge_path: str) -> Application:
    kb = KnowledgeBase(knowledge_path)
    app = Application.builder().token(token).build()
    app.bot_data["knowledge"] = kb

    # Калькуляторы и admin KB (ConversationHandler — первыми)
    app.add_handler(get_kuendigung_handler())
    app.add_handler(get_urlaub_handler())
    app.add_handler(get_bruttonetto_handler())
    for h in get_admin_handlers():
        app.add_handler(h)

    # Выбор языка и главное меню (callbacks)
    app.add_handler(CallbackQueryHandler(language_callback, pattern=r"^lang:"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r"^menu:"))
    app.add_handler(CallbackQueryHandler(topics_callback, pattern=r"^(tgrp:|qid:|topics:back)"))
    app.add_handler(CallbackQueryHandler(profile_callback, pattern=r"^profile:"))
    app.add_handler(CallbackQueryHandler(feedback_callback, pattern=r"^fb:"))

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("profil", profil_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("topics", topics_command))

    # Свободный текст (последним)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return app
