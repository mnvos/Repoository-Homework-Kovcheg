import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CallbackContext, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters,
)
from bot.knowledge import KnowledgeBase
from bot.calculators import get_kuendigung_handler, get_urlaub_handler, get_bruttonetto_handler
from bot.llm import ask_llm, build_kb_summary

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

STRINGS = {
    "ru": {
        "lang_chosen": "Выбран язык: 🇷🇺 Русский",
        "welcome": (
            "Привет! Я внутренний помощник *LK HR Assistant*.\n\n"
            "Помогу с вопросами по оформлению, больничным, отпускам и другим HR-процессам.\n\n"
            "Напиши вопрос или воспользуйся командами:\n"
            "/topics — список тем\n"
            "/kuendigung — калькулятор Kündigungsfrist\n"
            "/urlaub — калькулятор отпуска\n"
            "/bruttonetto — Brutto-Netto 2026\n"
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
    },
}


def _lang(context: CallbackContext) -> str:
    return context.user_data.get("lang", "de")


def _t(context: CallbackContext, key: str) -> str:
    return STRINGS[_lang(context)][key]


def _lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang:de"),
    ]])


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


async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(_t(context, "help"), parse_mode="Markdown")


async def topics_command(update: Update, context: CallbackContext) -> None:
    kb: KnowledgeBase = context.application.bot_data["knowledge"]
    await update.message.reply_text(_t(context, "topics_header") + kb.topic_titles())


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


async def handle_text(update: Update, context: CallbackContext) -> None:
    kb: KnowledgeBase = context.application.bot_data["knowledge"]
    query = update.message.text.strip()
    lang = _lang(context)

    # Приветствия
    if _is_greeting(query, lang):
        await update.message.reply_text(_t(context, "greeting"))
        return

    # "Что ты умеешь?"
    if _is_capabilities_query(query, lang):
        await update.message.reply_text(_t(context, "capabilities"))
        return

    kb_match = kb.search(query)

    if not LLM_ENABLED:
        # Режим без LLM — только KB
        if not kb_match:
            await update.message.reply_text(_t(context, "not_found"))
            return
        await update.message.reply_markdown_v2(kb.question_summary(kb_match))
        return

    # Режим с LLM
    thinking_text = "⏳ Обрабатываю запрос..." if lang == "ru" else "⏳ Verarbeite Anfrage..."
    thinking_msg = await update.message.reply_text(thinking_text)

    try:
        if kb_match:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ask_llm(query, lang, kb_entry=kb_match)
            )
        else:
            kb_summary = build_kb_summary(kb.export_data())
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ask_llm(query, lang, kb_summary=kb_summary)
            )
        await thinking_msg.edit_text(response)
    except Exception as e:
        logger.error("LLM error: %s", e, exc_info=True)
        await thinking_msg.delete()
        if kb_match:
            await update.message.reply_markdown_v2(kb.question_summary(kb_match))
        else:
            err_msg = f"{_t(context, 'llm_error')}\n\n[debug] {type(e).__name__}: {str(e)[:200]}"
            await update.message.reply_text(err_msg)


# ── App builder ───────────────────────────────────────────────────────────────

def build_application(token: str, knowledge_path: str) -> Application:
    kb = KnowledgeBase(knowledge_path)
    app = Application.builder().token(token).build()
    app.bot_data["knowledge"] = kb

    # Калькуляторы (ConversationHandler — первыми)
    app.add_handler(get_kuendigung_handler())
    app.add_handler(get_urlaub_handler())
    app.add_handler(get_bruttonetto_handler())

    # Выбор языка
    app.add_handler(CallbackQueryHandler(language_callback, pattern=r"^lang:"))

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("topics", topics_command))

    # Свободный текст (последним)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return app
