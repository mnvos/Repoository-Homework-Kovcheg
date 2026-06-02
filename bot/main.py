import os
from telegram import Update
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, filters
from bot.knowledge import KnowledgeBase


def build_application(token: str, knowledge_path: str) -> Application:
    kb = KnowledgeBase(knowledge_path)
    application = Application.builder().token(token).build()
    application.bot_data["knowledge"] = kb
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("topics", topics_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return application


async def start(update: Update, context: CallbackContext) -> None:
    text = (
        "Привет! Я внутренний помощник LK HR Assistant."
        "\nЯ помогу с вопросами по оформлению, больничным, отпускам и другим HR-процессам."
        "\nНапиши вопрос или воспользуйся командой /topics для списка тем."
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: CallbackContext) -> None:
    text = (
        "Я отвечаю на типовые HR-вопросы сотрудников и отдела кадров."
        "\n\nКоманды:\n"
        "/start — приветствие\n"
        "/help — эта подсказка\n"
        "/topics — список доступных тем\n"
        "\nПример запроса: \"Что делать при оформлении нового сотрудника?\""
    )
    await update.message.reply_text(text)


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
            "Я не нашёл точный ответ в базе знаний. "
            "Попробуйте переформулировать вопрос или обратитесь к HR-менеджеру."
        )
        await update.message.reply_text(fallback)
        return

    text = kb.question_summary(question)
    await update.message.reply_markdown_v2(text)
