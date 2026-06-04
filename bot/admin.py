"""
Admin KB management for HR staff via Telegram.
Commands: /addq, /editq, /delq, /kbstats
Access is restricted to ADMIN_USER_IDS (comma-separated Telegram user IDs in env).
"""
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext, CommandHandler, MessageHandler,
    ConversationHandler, CallbackQueryHandler, filters,
)
from bot.knowledge import KnowledgeBase

logger = logging.getLogger(__name__)

# ── Состояния диалога /addq ───────────────────────────────────────────────────
(
    ADD_TOPIC,
    ADD_TITLE,
    ADD_ANSWER,
    ADD_CHECKLIST,
    ADD_CONFIRM,
) = range(5)

# ── Состояния диалога /delq ───────────────────────────────────────────────────
(DEL_SEARCH, DEL_CONFIRM) = range(10, 12)


def _admin_ids() -> set:
    raw = os.getenv("ADMIN_USER_IDS", "")
    return {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}


def _is_admin(update: Update) -> bool:
    ids = _admin_ids()
    if not ids:
        return False
    return update.effective_user.id in ids


def _deny(update: Update):
    return update.message.reply_text("⛔ Нет доступа. Обратитесь к администратору.")


def _topics_keyboard(kb: KnowledgeBase) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(t["title"][:50], callback_data=f"adm_topic:{t['id']}")]
        for t in kb.list_topics()
    ]
    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="adm_topic:CANCEL")])
    return InlineKeyboardMarkup(buttons)


# ── /kbstats ──────────────────────────────────────────────────────────────────

async def kbstats_command(update: Update, context: CallbackContext) -> None:
    if not _is_admin(update):
        await _deny(update)
        return
    kb: KnowledgeBase = context.application.bot_data["knowledge"]
    topics = kb.list_topics()
    total_q = sum(len(t.get("questions", [])) for t in topics)
    version = kb.data.get("meta", {}).get("version", "?")
    lines = [f"📊 *База знаний KB v{version}*\n",
             f"Тем: {len(topics)} | Вопросов: {total_q}\n"]
    for t in topics:
        n = len(t.get("questions", []))
        lines.append(f"• {t['title'][:40]} — {n} вопр.")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── /addq — добавить вопрос ───────────────────────────────────────────────────

async def addq_start(update: Update, context: CallbackContext) -> int:
    if not _is_admin(update):
        await _deny(update)
        return ConversationHandler.END
    kb: KnowledgeBase = context.application.bot_data["knowledge"]
    context.user_data["addq"] = {}
    await update.message.reply_text(
        "➕ *Добавление вопроса в KB*\n\nВыбери тему:",
        parse_mode="Markdown",
        reply_markup=_topics_keyboard(kb),
    )
    return ADD_TOPIC


async def addq_topic(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    topic_id = query.data.split(":", 1)[1]
    if topic_id == "CANCEL":
        await query.edit_message_text("❌ Отменено.")
        return ConversationHandler.END
    kb: KnowledgeBase = context.application.bot_data["knowledge"]
    topic = kb.get_topic(topic_id)
    context.user_data["addq"]["topic_id"] = topic_id
    context.user_data["addq"]["topic_title"] = topic["title"] if topic else topic_id
    await query.edit_message_text(
        f"Тема: *{context.user_data['addq']['topic_title']}*\n\n"
        "Введи *заголовок* вопроса (1 строка):\n"
        "Пример: _Krankmeldung — как сообщить о болезни?_",
        parse_mode="Markdown",
    )
    return ADD_TITLE


async def addq_title(update: Update, context: CallbackContext) -> int:
    context.user_data["addq"]["title"] = update.message.text.strip()
    await update.message.reply_text(
        f"Заголовок: *{context.user_data['addq']['title']}*\n\n"
        "Теперь введи *ответ* (можно многострочный, поддерживается Markdown *жирный*, _курсив_):\n\n"
        "Когда закончишь — отправь текст одним сообщением.",
        parse_mode="Markdown",
    )
    return ADD_ANSWER


async def addq_answer(update: Update, context: CallbackContext) -> int:
    context.user_data["addq"]["answer"] = update.message.text.strip()
    context.user_data["addq"]["checklist"] = []
    await update.message.reply_text(
        "Ответ сохранён.\n\n"
        "Теперь добавь пункты *чек-листа* — по одному сообщению.\n"
        "Когда всё добавил — отправь /done\n"
        "Чтобы пропустить чек-лист — тоже /done",
        parse_mode="Markdown",
    )
    return ADD_CHECKLIST


async def addq_checklist_item(update: Update, context: CallbackContext) -> int:
    item = update.message.text.strip()
    context.user_data["addq"]["checklist"].append(item)
    n = len(context.user_data["addq"]["checklist"])
    await update.message.reply_text(
        f"✅ Пункт {n} добавлен.\nДобавь следующий или отправь /done"
    )
    return ADD_CHECKLIST


async def addq_checklist_done(update: Update, context: CallbackContext) -> int:
    data = context.user_data["addq"]
    checklist = data.get("checklist", [])
    checklist_preview = "\n".join(f"✅ {c}" for c in checklist) if checklist else "_пусто_"
    preview = (
        f"*Тема:* {data['topic_title']}\n"
        f"*Заголовок:* {data['title']}\n\n"
        f"*Ответ:*\n{data['answer'][:300]}{'...' if len(data['answer']) > 300 else ''}\n\n"
        f"*Чек-лист:*\n{checklist_preview}"
    )
    await update.message.reply_text(
        f"Проверь и подтверди:\n\n{preview}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Сохранить", callback_data="adm_confirm:save"),
            InlineKeyboardButton("❌ Отмена",    callback_data="adm_confirm:cancel"),
        ]]),
    )
    return ADD_CONFIRM


async def addq_confirm(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "adm_confirm:cancel":
        await query.edit_message_text("❌ Отменено. Вопрос не сохранён.")
        return ConversationHandler.END

    kb: KnowledgeBase = context.application.bot_data["knowledge"]
    data = context.user_data["addq"]
    new_q = {
        "title":     data["title"],
        "answer":    data["answer"],
        "checklist": data.get("checklist", []),
        "patterns":  [],
        "keywords":  [],
        "review":    "",
    }
    try:
        saved = kb.add_question(data["topic_id"], new_q)
        logger.info("ADMIN addq: topic=%s id=%s by user=%s",
                    data["topic_id"], saved.get("id"), query.from_user.id)
        await query.edit_message_text(
            f"✅ Вопрос сохранён!\n\nID: `{saved.get('id')}`\nТема: {data['topic_title']}",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error("ADMIN addq error: %s", e)
        await query.edit_message_text(f"❌ Ошибка при сохранении: {e}")
    return ConversationHandler.END


async def addq_cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("❌ Добавление отменено.")
    return ConversationHandler.END


# ── /delq — удалить вопрос ────────────────────────────────────────────────────

async def delq_start(update: Update, context: CallbackContext) -> int:
    if not _is_admin(update):
        await _deny(update)
        return ConversationHandler.END
    await update.message.reply_text(
        "🗑 *Удаление вопроса*\n\nВведи часть заголовка или ID для поиска:",
        parse_mode="Markdown",
    )
    return DEL_SEARCH


async def delq_search(update: Update, context: CallbackContext) -> int:
    kb: KnowledgeBase = context.application.bot_data["knowledge"]
    search_term = update.message.text.strip().lower()
    matches = []
    for topic in kb.list_topics():
        for q in topic.get("questions", []):
            if (search_term in q.get("title", "").lower()
                    or search_term in q.get("id", "").lower()):
                matches.append((topic["title"], q))

    if not matches:
        await update.message.reply_text(
            "Ничего не найдено. Попробуй другой запрос или /cancel"
        )
        return DEL_SEARCH

    buttons = []
    for topic_title, q in matches[:10]:
        label = f"{q['id']} — {q.get('title', '')[:40]}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"adm_del:{q['id']}")])
    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="adm_del:CANCEL")])
    await update.message.reply_text(
        f"Найдено {len(matches)} совпадений. Выбери для удаления:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return DEL_CONFIRM


async def delq_confirm(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    qid = query.data.split(":", 1)[1]
    if qid == "CANCEL":
        await query.edit_message_text("❌ Отменено.")
        return ConversationHandler.END

    kb: KnowledgeBase = context.application.bot_data["knowledge"]
    q = kb.get_question_by_id(qid)
    if not q:
        await query.edit_message_text("Вопрос не найден.")
        return ConversationHandler.END

    await query.edit_message_text(
        f"Удалить *{q.get('title', qid)}*?\n\nID: `{qid}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🗑 Да, удалить", callback_data=f"adm_del_ok:{qid}"),
            InlineKeyboardButton("❌ Нет",          callback_data="adm_del:CANCEL"),
        ]]),
    )
    return DEL_CONFIRM


async def delq_execute(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    qid = query.data.split(":", 1)[1]
    kb: KnowledgeBase = context.application.bot_data["knowledge"]
    try:
        kb.delete_question(qid)
        logger.info("ADMIN delq: id=%s by user=%s", qid, query.from_user.id)
        await query.edit_message_text(f"✅ Вопрос `{qid}` удалён.", parse_mode="Markdown")
    except Exception as e:
        logger.error("ADMIN delq error: %s", e)
        await query.edit_message_text(f"❌ Ошибка: {e}")
    return ConversationHandler.END


async def delq_cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("❌ Отменено.")
    return ConversationHandler.END


# ── Сборка хендлеров ──────────────────────────────────────────────────────────

def get_admin_handlers():
    addq_handler = ConversationHandler(
        entry_points=[CommandHandler("addq", addq_start)],
        states={
            ADD_TOPIC:     [CallbackQueryHandler(addq_topic,         pattern=r"^adm_topic:")],
            ADD_TITLE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, addq_title)],
            ADD_ANSWER:    [MessageHandler(filters.TEXT & ~filters.COMMAND, addq_answer)],
            ADD_CHECKLIST: [
                CommandHandler("done", addq_checklist_done),
                MessageHandler(filters.TEXT & ~filters.COMMAND, addq_checklist_item),
            ],
            ADD_CONFIRM:   [CallbackQueryHandler(addq_confirm, pattern=r"^adm_confirm:")],
        },
        fallbacks=[CommandHandler("cancel", addq_cancel)],
        allow_reentry=True,
    )

    delq_handler = ConversationHandler(
        entry_points=[CommandHandler("delq", delq_start)],
        states={
            DEL_SEARCH:  [
                MessageHandler(filters.TEXT & ~filters.COMMAND, delq_search),
                CallbackQueryHandler(delq_confirm, pattern=r"^adm_del:"),
            ],
            DEL_CONFIRM: [
                CallbackQueryHandler(delq_confirm,  pattern=r"^adm_del:"),
                CallbackQueryHandler(delq_execute,  pattern=r"^adm_del_ok:"),
            ],
        },
        fallbacks=[CommandHandler("cancel", delq_cancel)],
        allow_reentry=True,
    )

    return [addq_handler, delq_handler, CommandHandler("kbstats", kbstats_command)]
