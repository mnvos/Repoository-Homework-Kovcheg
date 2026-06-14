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
from telegram.ext import PicklePersistence, PersistenceInput

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

# Короткие фразы-уточнения — относятся к ПРЕДЫДУЩЕЙ теме, а не новый вопрос.
# Любая другая короткая фраза («Рабочая виза», «zoll») — самостоятельный
# вопрос и НЕ должна склеиваться с last_topic (баг с «склейкой контекста»).
_FOLLOWUP_TRIGGERS = {
    "ru": {"подробнее", "поподробнее", "а сколько", "а как", "а что", "а почему",
           "ещё", "еще", "и что", "продолжи", "дальше", "а если"},
    "de": {"mehr", "genauer", "und wieviel", "und wie", "und was", "und warum",
           "weiter", "mehr infos", "und wenn"},
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
    rows = []
    pair = []
    for g in _TOPIC_GROUPS:
        pair.append(InlineKeyboardButton(g["title"][lang], callback_data=f"tgrp:{g['id']}"))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    hr_label = "📞 Связаться с HR" if lang == "ru" else "📞 HR kontaktieren"
    rows.append([InlineKeyboardButton(hr_label, callback_data="menu:hr")])
    return InlineKeyboardMarkup(rows)


# Контакты HR (используется кнопкой "Связаться с HR")
_HR_CONTACT_RESPONSE = {
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
    if key == "hr":
        response = _HR_CONTACT_RESPONSE.get(lang, "")
        if response:
            await query.message.reply_text(response, parse_mode="Markdown")


async def ask_free_callback(update: Update, context: CallbackContext) -> None:
    """Кнопка «Задать свой вопрос» — сбрасывает контекст темы и просит ввести текст."""
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    # Сброс контекста предыдущей темы — критично, чтобы свободный вопрос
    # не «склеивался» с темой предыдущего меню (см. баг last_topic)
    context.user_data.pop("last_topic", None)
    context.user_data.pop("current_group", None)
    text = (
        "❓ Напиши свой вопрос — отвечу на основе базы знаний LK Bauservice." if lang == "ru"
        else "❓ Schreib deine Frage — ich antworte auf Basis der LK Bauservice Wissensdatenbank."
    )
    await query.message.reply_text(text)


async def forms_callback(update: Update, context: CallbackContext) -> None:
    """Кнопка шаблона документа — отправляет DOCX-бланк как вложение."""
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    form_key = query.data.split(":", 1)[1]
    tpl = _FORM_TEMPLATES.get(form_key)
    if not tpl:
        return

    file_path = tpl["file"]
    if not os.path.exists(file_path):
        logging.warning("Form template not found: %s (cwd=%s)", file_path, os.getcwd())
        text = (
            "⚠️ Файл шаблона временно недоступен. Обратись в отдел кадров." if lang == "ru"
            else "⚠️ Die Vorlage ist momentan nicht verfügbar. Bitte an die Personalabteilung wenden."
        )
        await query.message.reply_text(text)
        return

    caption = tpl["caption"].get(lang, "")
    with open(file_path, "rb") as f:
        await query.message.reply_document(
            document=f,
            filename=tpl["filename"],
            caption=caption,
        )


async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(_t(context, "help"), parse_mode="Markdown")


# ── /topics — 5 групп ────────────────────────────────────────────────────────

_TOPIC_GROUPS = [
    {
        "id": "grp_salary",
        "title": {"ru": "💰 Зарплата и выплаты",        "de": "💰 Gehalt & Zahlungen"},
        "topic_ids": ["salary", "baulohn", "lohnabrechnung_erklaerung"],
        "calculator": "bruttonetto",
    },
    {
        "id": "grp_vacation",
        "title": {"ru": "🏖️ Отпуск",                    "de": "🏖️ Urlaub"},
        "topic_ids": ["vacation", "soka_bau"],
        "calculator": "urlaub",
    },
    {
        "id": "grp_sick",
        "title": {"ru": "🤒 Больничный и страховки",    "de": "🤒 Krankmeldung & Versicherung"},
        "topic_ids": ["sick_leave", "krankenkassen"],
    },
    {
        "id": "grp_hours",
        "title": {"ru": "⏰ Рабочее время (BRTV)",      "de": "⏰ Arbeitszeit (BRTV)"},
        "topic_ids": ["brtv"],
    },
    {
        "id": "grp_docs",
        "title": {"ru": "📄 Документы",                 "de": "📄 Dokumente"},
        "topic_ids": ["documents"],
    },
    {
        "id": "grp_onboarding",
        "title": {"ru": "📝 Оформление",                "de": "📝 Einstellung"},
        "topic_ids": ["onboarding"],
    },
    {
        "id": "grp_auslaender",
        "title": {"ru": "👷 Aufenthaltstitel",          "de": "👷 Aufenthaltstitel"},
        "topic_ids": ["auslaender", "zoll"],
    },
    {
        "id": "grp_familie",
        "title": {"ru": "👶 Семья",                     "de": "👶 Familie"},
        "topic_ids": ["kindergeld", "familie_soziales"],
    },
    {
        "id": "grp_law",
        "title": {"ru": "🏗️ Трудовое право",            "de": "🏗️ Arbeitsrecht"},
        "topic_ids": ["termination", "agg", "ausbildungsverguetung",
                      "zvk_tarifrente", "dsgvo", "accidents", "bg_bau"],
        "calculator": "kuendigung",
    },
    {
        "id": "grp_referral",
        "title": {"ru": "🎁 Приведи друга",             "de": "🎁 Mitarbeiter empfehlen"},
        "topic_ids": ["referral"],
    },
    {
        "id": "grp_forms",
        "title": {"ru": "📋 Формуляры",                 "de": "📋 Formulare"},
        "topic_ids": [],
        "forms": ["urlaubsantrag", "kuendigungsschreiben"],
    },
]


# Подпись и подсказка для кнопок калькуляторов внутри подменю групп
_CALC_BUTTON_LABELS = {
    "bruttonetto": {"ru": "🧮 Калькулятор Brutto-Netto", "de": "🧮 Brutto-Netto-Rechner"},
    "urlaub":      {"ru": "🧮 Калькулятор отпуска",      "de": "🧮 Urlaubsrechner"},
    "kuendigung":  {"ru": "🧮 Калькулятор увольнения",   "de": "🧮 Kündigungsfrist-Rechner"},
}


# Скачиваемые шаблоны документов (DOCX), отправляются как вложение
_FORM_TEMPLATES = {
    "urlaubsantrag": {
        "file": "data/templates/urlaubsantrag.docx",
        "filename": "Urlaubsantrag.docx",
        "title": {"ru": "📋 Заявление на отпуск (Urlaubsantrag)",
                  "de": "📋 Urlaubsantrag"},
        "caption": {
            "ru": "Заполни поля от руки или в Word и передай в отдел кадров.",
            "de": "Bitte die Felder handschriftlich oder in Word ausfüllen und an die Personalabteilung weiterleiten.",
        },
    },
    "kuendigungsschreiben": {
        "file": "data/templates/kuendigungsschreiben.docx",
        "filename": "Kuendigungsschreiben.docx",
        "title": {"ru": "📋 Заявление об увольнении (Kündigungsschreiben)",
                  "de": "📋 Kündigungsschreiben"},
        "caption": {
            "ru": "Заявление об увольнении по собственному желанию. Заполни поля и передай в отдел кадров. "
                  "Перед подачей рекомендуем уточнить срок увольнения — /kuendigung.",
            "de": "Eigenkündigung zum nächstmöglichen Termin. Bitte Felder ausfüllen und an die "
                  "Personalabteilung weiterleiten. Kündigungsfrist vorher prüfen — /kuendigung.",
        },
    },
}


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

    # Кнопки скачиваемых шаблонов (DOCX)
    for form_key in group.get("forms", []):
        tpl = _FORM_TEMPLATES.get(form_key)
        if not tpl:
            continue
        label = tpl["title"].get(lang, form_key)
        buttons.append([InlineKeyboardButton(label[:60], callback_data=f"form:{form_key}")])

    # Кнопка калькулятора, если у группы есть привязанный расчёт
    calc_key = group.get("calculator")
    if calc_key:
        calc_label = _CALC_BUTTON_LABELS.get(calc_key, {}).get(lang, calc_key)
        buttons.append([InlineKeyboardButton(calc_label, callback_data=f"calc:{calc_key}")])

    # «Задать свой вопрос» — если нужного вопроса нет в списке
    ask_label = "❓ Задать свой вопрос" if lang == "ru" else "❓ Eigene Frage stellen"
    buttons.append([InlineKeyboardButton(ask_label, callback_data="ask_free")])

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
        context.user_data.pop("current_group", None)
        header = "Выбери раздел:" if lang == "ru" else "Wähle einen Bereich:"
        await query.edit_message_text(header, reply_markup=_groups_keyboard(lang))
        return

    # Клик на группу → список всех вопросов группы
    if query.data.startswith("tgrp:"):
        group_id = query.data.split(":", 1)[1]
        group = next((g for g in _TOPIC_GROUPS if g["id"] == group_id), None)
        if not group:
            return
        # Запоминаем текущую группу — используется для кнопки "назад" у ответа
        # и сбрасываем last_topic, чтобы не «склеивать» с предыдущей темой
        context.user_data["current_group"] = group_id
        context.user_data.pop("last_topic", None)
        header = f"*{group['title'][lang]}*\n\n"
        if not group["topic_ids"] and group.get("forms"):
            header += "Выбери документ:" if lang == "ru" else "Wähle ein Dokument:"
        else:
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

        # Запоминаем тему — чтобы «подробнее»/«а сколько» после клика по кнопке
        # тоже могли уточнить именно этот вопрос (см. _FOLLOWUP_TRIGGERS).
        context.user_data["last_topic"] = q.get("title", qid)

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

        # Группа, из которой пришли — для кнопки "назад"
        parent_group = context.user_data.get("current_group")
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


def _is_followup_query(text: str) -> bool:
    """True, если текст — короткое уточнение к предыдущему ответу
    («подробнее», «а сколько»), а не самостоятельный новый вопрос."""
    t = text.lower().strip()
    all_triggers: set = set()
    for triggers in _FOLLOWUP_TRIGGERS.values():
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

    # Сначала ищем по чистому запросу — короткий запрос («Рабочая виза») может быть
    # самостоятельным вопросом, и склейка с прошлой темой не должна перебивать его.
    kb_match = kb.search(query)

    # Склейку с темой последнего ответа применяем ТОЛЬКО для закрытого списка
    # фраз-уточнений («подробнее», «а сколько») — а не для любой короткой фразы,
    # иначе самостоятельные короткие вопросы («Рабочая виза», «zoll») будут
    # «склеиваться» с предыдущей темой и давать неверный ответ.
    effective_query = query
    if not kb_match and _is_followup_query(query) and context.user_data.get("last_topic"):
        effective_query = f"{context.user_data['last_topic']} — {query}"
        kb_match = kb.search(effective_query)

    # Сохраняем тему если нашли в KB
    if kb_match:
        context.user_data["last_topic"] = kb_match.get("title", query)

    if not LLM_ENABLED:
        if not kb_match:
            await update.message.reply_text(_t(context, "not_found"))
            return
        await update.message.reply_text(
            kb.question_summary(kb_match),
            reply_markup=_feedback_keyboard(query, lang),
        )
        return

    # Режим с LLM
    thinking_text = "⏳ Обрабатываю запрос..." if lang == "ru" else "⏳ Verarbeite Anfrage..."
    thinking_msg = await update.message.reply_text(thinking_text)

    profile = _get_profile(context)
    loop = asyncio.get_running_loop()
    try:
        if kb_match:
            response = await loop.run_in_executor(
                None, lambda: ask_llm(effective_query, lang, kb_entry=kb_match, profile=profile)
            )
        else:
            kb_summary = build_kb_summary(kb.export_data())
            response = await loop.run_in_executor(
                None, lambda: ask_llm(effective_query, lang, kb_summary=kb_summary, profile=profile)
            )
        await thinking_msg.edit_text(response, reply_markup=_feedback_keyboard(query, lang))
    except Exception as e:
        logger.error("LLM error: %s", e, exc_info=True)
        await thinking_msg.delete()
        if kb_match:
            await update.message.reply_text(
                kb.question_summary(kb_match),
                reply_markup=_feedback_keyboard(query, lang),
            )
        else:
            await update.message.reply_text(_t(context, "llm_error"))


# ── App builder ───────────────────────────────────────────────────────────────

def build_application(token: str, knowledge_path: str,
                      persistence_path: str = "./data/bot_persistence") -> Application:
    import pathlib
    pathlib.Path(persistence_path).parent.mkdir(parents=True, exist_ok=True)
    persistence = PicklePersistence(
        filepath=persistence_path,
        store_data=PersistenceInput(bot_data=False),
    )

    kb = KnowledgeBase(knowledge_path)
    app = Application.builder().token(token).persistence(persistence).build()
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
    app.add_handler(CallbackQueryHandler(ask_free_callback, pattern=r"^ask_free$"))
    app.add_handler(CallbackQueryHandler(forms_callback, pattern=r"^form:"))
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
