import os
from telegram import Update
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, filters
from bot.knowledge import KnowledgeBase
from bot.calculators import get_kuendigung_handler, get_urlaub_handler, get_bruttonetto_handler


def build_application(token: str, knowledge_path: str) -> Application:
    kb = KnowledgeBase(knowledge_path)
    application = Application.builder().token(token).build()
    application.bot_data["knowledge"] = kb

    # Kalkulatoren zuerst (ConversationHandler hat Vorrang)
    application.add_handler(get_kuendigung_handler())
    application.add_handler(get_urlaub_handler())
    application.add_handler(get_bruttonetto_handler())

    # Standard-Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("topics", topics_command))

    # Freitext-Suche (muss als letztes stehen)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return application


async def start(update: Update, context: CallbackContext) -> None:
    text = (
        "Привет! Я внутренний помощник *LK HR Assistant*.\n\n"
        "Я помогу с вопросами по оформлению, больничным, отпускам и другим HR-процессам.\n\n"
        "Напиши вопрос или воспользуйся командами:\n"
        "/topics — список тем базы знаний\n"
        "/kuendigung — калькулятор Kündigungsfrist (§ 622 BGB)\n"
        "/urlaub — калькулятор остатка отпуска\n"
        "/bruttonetto — Brutto-Netto-Rechner 2026 (Niedersachsen)\n"
        "/help — подробная справка"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def help_command(update: Update, context: CallbackContext) -> None:
    text = (
        "Я отвечаю на типовые HR-вопросы сотрудников и отдела кадров.\n\n"
        "*Команды:*\n"
        "/start — приветствие\n"
        "/help — эта подсказка\n"
        "/topics — список доступных тем\n\n"
        "*Калькуляторы:*\n"
        "/kuendigung — Kündigungsfrist nach § 622 BGB\n"
        "  → Probezeit, Betriebszugehörigkeit, letzter Arbeitstag\n"
        "/urlaub — Urlaubsrechner\n"
        "  → Jahresanspruch, Teilzeit, Resturlaub\n"
        "/bruttonetto — Brutto-Netto 2026 (Niedersachsen)\n"
        "  → Steuerklasse, Lohnsteuer, Sozialabgaben, Nettolohn\n\n"
        "Abbrechen: /cancel\n\n"
        "Beispiel: \"Was tun bei Krankmeldung?\""
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def topics_command(update: Update, context: CallbackContext) -> None:
    kb: KnowledgeBase = context.application.bot_data["knowledge"]
    text = "Доступные темы:\n" + kb.topic_titles()
    await update.message.reply_text(text)


async def handle_text(update: Update, context: CallbackContext) -> None:
    kb: KnowledgeBase = context.application.bot_data["knowledge"]
    query = update.message.text.strip()
    question = kb.search(query)

    if not question:
        fallback = (
            "Ich konnte keine passende Antwort in der Wissensdatenbank finden.\n\n"
            "Bitte formulieren Sie Ihre Frage anders oder wenden Sie sich an die HR-Abteilung.\n\n"
            "Калькуляторы: /kuendigung /urlaub /bruttonetto"
        )
        await update.message.reply_text(fallback)
        return

    text = kb.question_summary(question)
    await update.message.reply_markdown_v2(text)
