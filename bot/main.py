import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CallbackContext, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters,
)
from bot.knowledge import KnowledgeBase
from bot.calculators import get_kuendigung_handler, get_urlaub_handler, get_bruttonetto_handler
from bot.llm import ask_llm, build_kb_summary

LLM_ENABLED = bool(os.getenv("GROQ_API_KEY"))

# ── Тексты на двух языках ────────────────────────────────────────────────────

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


async def handle_text(update: Update, context: CallbackContext) -> None:
    kb: KnowledgeBase = context.application.bot_data["knowledge"]
    query = update.message.text.strip()
    lang = _lang(context)
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
            # Нашли в KB — LLM переформулирует/дополняет ответ
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ask_llm(query, lang, kb_entry=kb_match)
            )
        else:
            # Не нашли — LLM отвечает по всей KB как контексту
            kb_summary = build_kb_summary(kb.export_data())
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ask_llm(query, lang, kb_summary=kb_summary)
            )
        await thinking_msg.edit_text(response)
    except Exception as e:
        # Fallback на KB если LLM недоступен
        await thinking_msg.delete()
        if kb_match:
            await update.message.reply_markdown_v2(kb.question_summary(kb_match))
        else:
            await update.message.reply_text(_t(context, "not_found"))


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
