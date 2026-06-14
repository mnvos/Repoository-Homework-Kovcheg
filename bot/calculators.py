"""
LK HR Assistant — Калькуляторы
  /kuendigung  — Kündigungsfrist § 622 BGB
  /urlaub      — Urlaubsrechner (anteilig + Teilzeit)
  /bruttonetto — Brutto-Netto 2026, Niedersachsen
"""
from __future__ import annotations

import math
import re
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

# ─── State constants ──────────────────────────────────────────────────────────
KU_SIDE, KU_PROBEZEIT, KU_EINSTELLUNG, KU_KUENDIGUNG = range(4)
UR_JAHRESANSPRUCH, UR_VOLLZEIT, UR_EIGEN, UR_MONATE, UR_GENOMMEN = range(10, 15)
BN_BRUTTO, BN_SK, BN_KINDER = range(20, 23)

# ─── 2026 Sozialversicherungssätze (AN-Anteil) ────────────────────────────────
_RV = 0.093          # 18,6 % / 2
_AV = 0.013          # 2,6 % / 2
_KV = 0.0730         # 14,6 % / 2
_KV_ZUSATZ = 0.0145  # Durchschn. Zusatzbeitrag 2,9 % / 2
_PV = 0.018          # 3,6 % / 2
_PV_KL_ZUSCHLAG = 0.006  # Kinderlos-Zuschlag +0,6 % (ab 23 J.)

_BBG_KV = 5_812.50   # monatlich
_BBG_RV = 8_450.00   # monatlich

_GFB = 12_348.0      # Grundfreibetrag 2026


def _clang(context: CallbackContext) -> str:
    """Текущий язык интерфейса ('ru' или 'de'), выбранный через /language."""
    return context.user_data.get("lang", "de")


class _CallbackAsMessage:
    """Адаптер: позволяет вызвать *_start(update, ctx) из CallbackQueryHandler.

    *_start читает update.message.reply_text(...) — у CallbackQuery есть
    .message с тем же reply_text, поэтому подставляем его как .message.
    """

    def __init__(self, query) -> None:
        self.message = query.message


async def ku_start_from_button(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    return await ku_start(_CallbackAsMessage(update.callback_query), context)


async def ur_start_from_button(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    return await ur_start(_CallbackAsMessage(update.callback_query), context)


async def bn_start_from_button(update: Update, context: CallbackContext) -> int:
    await update.callback_query.answer()
    return await bn_start(_CallbackAsMessage(update.callback_query), context)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_date(text: str) -> date | None:
    from dateutil.parser import parse as dp
    try:
        return dp(text.strip(), dayfirst=True).date()
    except Exception:
        return None


def _parse_euro(text: str) -> float | None:
    t = text.strip().replace("€", "").replace(" ", "")
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}\.\d{3}", t):
        t = t.replace(".", "")
    try:
        v = float(t)
        return v if v > 0 else None
    except Exception:
        return None


async def _cancel(update: Update, context: CallbackContext) -> int:
    lang = _clang(context)
    text = (
        "Расчёт отменён. (/kuendigung /urlaub /bruttonetto)" if lang == "ru"
        else "Berechnung abgebrochen. (/kuendigung /urlaub /bruttonetto)"
    )
    await update.message.reply_text(text)
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════════════════════
# KÜNDIGUNGSFRIST § 622 BGB
# ═══════════════════════════════════════════════════════════════════════════════

def _ag_frist_monate(years: int) -> int:
    """Kündigungsfrist Arbeitgeber in Monaten nach § 622 Abs. 2 BGB."""
    table = [(2, 1), (5, 2), (8, 3), (10, 4), (12, 5), (15, 6), (20, 7)]
    for threshold, months in table:
        if years < threshold:
            return months
    return 7


def _letzter_tag_monat(d: date) -> date:
    """Letzter Tag des Monats von d."""
    nxt = d.replace(day=28) + timedelta(days=4)
    return nxt - timedelta(days=nxt.day)


def _an_kuendigungstermin(kuend: date) -> date:
    """Nächster 15. oder Monatsende nach 4-Wochen-Frist (Arbeitnehmer)."""
    raw = kuend + timedelta(weeks=4)
    d15 = raw.replace(day=15)
    eom = _letzter_tag_monat(raw)
    # nächste der beiden Optionen, die >= raw liegt
    candidates = [d15, eom, d15 + relativedelta(months=1), _letzter_tag_monat(raw + relativedelta(months=1))]
    return min(c for c in candidates if c >= raw)


async def ku_start(update: Update, context: CallbackContext) -> int:
    lang = _clang(context)
    if lang == "ru":
        kb = [
            [InlineKeyboardButton("Увольняет работодатель (Arbeitgeber)", callback_data="ag"),
             InlineKeyboardButton("Увольняется сотрудник (Arbeitnehmer)", callback_data="an")],
        ]
        text = (
            "⚖️ *Калькулятор срока увольнения (Kündigungsfrist, § 622 BGB)*\n\n"
            "Кто инициирует увольнение?"
        )
    else:
        kb = [
            [InlineKeyboardButton("Arbeitgeber kündigt", callback_data="ag"),
             InlineKeyboardButton("Arbeitnehmer kündigt", callback_data="an")],
        ]
        text = "⚖️ *Kündigungsfrist-Rechner (§ 622 BGB)*\n\nWer spricht die Kündigung aus?"
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return KU_SIDE


async def ku_side(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()
    context.user_data["ku_seite"] = q.data
    lang = _clang(context)
    if lang == "ru":
        kb = [[InlineKeyboardButton("Да — Probezeit (испытательный срок)", callback_data="ja"),
               InlineKeyboardButton("Нет", callback_data="nein")]]
        text = "Сотрудник ещё на *Probezeit* (испытательный срок, максимум 6 месяцев)?"
    else:
        kb = [[InlineKeyboardButton("Ja — Probezeit", callback_data="ja"),
               InlineKeyboardButton("Nein", callback_data="nein")]]
        text = "Befindet sich der Mitarbeiter noch in der *Probezeit* (max. 6 Monate)?"
    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return KU_PROBEZEIT


async def ku_probezeit(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()
    lang = _clang(context)
    if q.data == "ja":
        ende = date.today() + timedelta(weeks=2)
        if lang == "ru":
            text = (
                f"✅ *Результат (Probezeit — испытательный срок)*\n\n"
                f"Срок: *2 недели* — увольнение возможно в любой день\n"
                f"Последний рабочий день (от сегодня): *{ende.strftime('%d.%m.%Y')}*\n\n"
                f"⚠️ Проверьте Arbeitsvertrag (трудовой договор) — там могут быть иные условия."
            )
        else:
            text = (
                f"✅ *Ergebnis (Probezeit)*\n\n"
                f"Frist: *2 Wochen* — beliebiger Tag möglich\n"
                f"Letzter Arbeitstag (ab heute): *{ende.strftime('%d.%m.%Y')}*\n\n"
                f"⚠️ Bitte prüfen Sie den Arbeitsvertrag auf abweichende Regelungen."
            )
        await q.edit_message_text(text, parse_mode="Markdown")
        return ConversationHandler.END

    text = (
        "📅 Укажи *дату приёма на работу (Einstellungsdatum)*, например 15.03.2019:" if lang == "ru"
        else "📅 Bitte *Einstellungsdatum* eingeben (z.B. 15.03.2019):"
    )
    await q.edit_message_text(text)
    return KU_EINSTELLUNG


async def ku_einstellung(update: Update, context: CallbackContext) -> int:
    lang = _clang(context)
    d = _parse_date(update.message.text)
    if not d:
        text = (
            "❌ Дата не распознана. Введи ещё раз (например 15.03.2019):" if lang == "ru"
            else "❌ Datum nicht erkannt. Bitte erneut eingeben (z.B. 15.03.2019):"
        )
        await update.message.reply_text(text)
        return KU_EINSTELLUNG
    context.user_data["ku_einstellung"] = d
    text = (
        "📅 Когда увольнение *передаётся / вручается* сотруднику (Kündigung übergeben/zugestellt)? "
        "(например 20.06.2026):" if lang == "ru"
        else "📅 Wann wird die Kündigung *übergeben / zugestellt*? (z.B. 20.06.2026):"
    )
    await update.message.reply_text(text)
    return KU_KUENDIGUNG


async def ku_kuendigung(update: Update, context: CallbackContext) -> int:
    lang = _clang(context)
    kuend = _parse_date(update.message.text)
    if not kuend:
        text = (
            "❌ Дата не распознана. Введи ещё раз:" if lang == "ru"
            else "❌ Datum nicht erkannt. Bitte erneut eingeben:"
        )
        await update.message.reply_text(text)
        return KU_KUENDIGUNG

    einst: date = context.user_data["ku_einstellung"]
    seite: str = context.user_data["ku_seite"]
    delta = relativedelta(kuend, einst)
    years = delta.years

    if seite == "an":
        letzter = _an_kuendigungstermin(kuend)
        frist_text = (
            "4 недели до 15-го или конца месяца (4 Wochen zum 15. oder Monatsende)" if lang == "ru"
            else "4 Wochen zum 15. oder Monatsende"
        )
    else:
        m = _ag_frist_monate(years)
        letzter = _letzter_tag_monat(kuend + relativedelta(months=m))
        if m == 1:
            frist_text = (
                "4 недели до 15-го или конца месяца (4 Wochen zum 15. oder Monatsende)" if lang == "ru"
                else "4 Wochen zum 15. oder Monatsende"
            )
        else:
            frist_text = (
                f"{m} мес. до конца месяца ({m} Monate zum Monatsende)" if lang == "ru"
                else f"{m} Monate zum Monatsende"
            )
        if m == 1:
            letzter = _an_kuendigungstermin(kuend)

    verbleibend = (letzter - date.today()).days

    if lang == "ru":
        seite_label = "Работодатель (Arbeitgeber)" if seite == "ag" else "Сотрудник (Arbeitnehmer)"
        text = (
            f"✅ *Результат: Kündigungsfrist (срок увольнения)*\n\n"
            f"Кто увольняет: *{seite_label}*\n"
            f"Стаж (Betriebszugehörigkeit): *{years} г.*\n"
            f"Дата вручения увольнения: *{kuend.strftime('%d.%m.%Y')}*\n"
            f"Законный срок (gesetzliche Frist): *{frist_text}*\n"
            f"Последний рабочий день: *{letzter.strftime('%d.%m.%Y')}*\n"
            f"Осталось дней: *{verbleibend}*\n\n"
            f"⚠️ Tarifvertrag (тарифный договор) или трудовой договор могут предусматривать более "
            f"длинные сроки. В сомнительных случаях обратись к юристу или Steuerberater (налоговому консультанту)."
        )
    else:
        seite_label = "Arbeitgeber" if seite == "ag" else "Arbeitnehmer"
        text = (
            f"✅ *Kündigungsfrist-Ergebnis*\n\n"
            f"Seite: *{seite_label}*\n"
            f"Betriebszugehörigkeit: *{years} Jahr(e)*\n"
            f"Kündigung übergeben am: *{kuend.strftime('%d.%m.%Y')}*\n"
            f"Gesetzliche Frist: *{frist_text}*\n"
            f"Letzter Arbeitstag: *{letzter.strftime('%d.%m.%Y')}*\n"
            f"Verbleibende Tage: *{verbleibend} Tage*\n\n"
            f"⚠️ Tarifvertrag oder Arbeitsvertrag kann längere Fristen vorsehen. "
            f"Im Zweifel Rücksprache mit Rechtsanwalt oder Steuerberater."
        )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
    )
    return ConversationHandler.END


def get_kuendigung_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("kuendigung", ku_start),
            CallbackQueryHandler(ku_start_from_button, pattern="^calc:kuendigung$"),
        ],
        states={
            KU_SIDE: [CallbackQueryHandler(ku_side, pattern="^(ag|an)$")],
            KU_PROBEZEIT: [CallbackQueryHandler(ku_probezeit, pattern="^(ja|nein)$")],
            KU_EINSTELLUNG: [MessageHandler(filters.TEXT & ~filters.COMMAND, ku_einstellung)],
            KU_KUENDIGUNG: [MessageHandler(filters.TEXT & ~filters.COMMAND, ku_kuendigung)],
        },
        fallbacks=[CommandHandler("cancel", _cancel), CommandHandler("kuendigung", ku_start)],
        per_message=False,
        allow_reentry=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# URLAUBSRECHNER
# ═══════════════════════════════════════════════════════════════════════════════

async def ur_start(update: Update, context: CallbackContext) -> int:
    lang = _clang(context)
    profile = context.user_data.get("profile")
    context.user_data.clear()
    context.user_data["lang"] = lang
    if profile is not None:
        context.user_data["profile"] = profile
    text = (
        "🏖️ *Калькулятор отпуска (Urlaubsrechner)*\n\n"
        "Сколько дней отпуска положено сотруднику *в год (pro Kalenderjahr)*?" if lang == "ru"
        else "🏖️ *Urlaubsrechner*\n\nWie viele Urlaubstage stehen dem Mitarbeiter *pro Kalenderjahr* zu?"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    return UR_JAHRESANSPRUCH


async def ur_jahresanspruch(update: Update, context: CallbackContext) -> int:
    lang = _clang(context)
    try:
        tage = float(update.message.text.strip().replace(",", "."))
        assert 1 <= tage <= 365
    except Exception:
        text = "❌ Введи число (например 30):" if lang == "ru" else "❌ Bitte Zahl eingeben (z.B. 30):"
        await update.message.reply_text(text)
        return UR_JAHRESANSPRUCH
    context.user_data["ur_ja"] = tage
    if lang == "ru":
        kb = [[InlineKeyboardButton("5-дневная неделя", callback_data="5"),
               InlineKeyboardButton("6-дневная неделя", callback_data="6")]]
        text = "Сколько дней в неделю работает сотрудник на *полной ставке (Vollzeit)* в вашей фирме?"
    else:
        kb = [[InlineKeyboardButton("5-Tage-Woche", callback_data="5"),
               InlineKeyboardButton("6-Tage-Woche", callback_data="6")]]
        text = "Wie viele Tage arbeitet ein *Vollzeitmitarbeiter* pro Woche in Ihrer Firma?"
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return UR_VOLLZEIT


async def ur_vollzeit(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()
    lang = _clang(context)
    vollzeit = int(q.data)
    context.user_data["ur_vz"] = vollzeit
    buttons = [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, vollzeit + 1)]
    rows = [buttons[:3], buttons[3:6]]
    text = (
        "Сколько дней в неделю работает *этот сотрудник*?" if lang == "ru"
        else "Wie viele Tage pro Woche arbeitet *dieser Mitarbeiter*?"
    )
    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([r for r in rows if r]),
        parse_mode="Markdown",
    )
    return UR_EIGEN


async def ur_eigen(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()
    lang = _clang(context)
    context.user_data["ur_eigen"] = int(q.data)
    kb = [
        [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, 7)],
        [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(7, 13)],
    ]
    text = (
        "За сколько *месяцев* в этом году положен отпуск (Urlaubsanspruch)?\n"
        "(12 = весь год, например 6 = принят на работу с 01.07.)" if lang == "ru"
        else "Für wie viele *Monate* in diesem Jahr besteht Urlaubsanspruch?\n"
             "(12 = ganzes Jahr, z.B. 6 = ab 01.07. eingestellt)"
    )
    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return UR_MONATE


async def ur_monate(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()
    lang = _clang(context)
    context.user_data["ur_monate"] = int(q.data)
    text = (
        "Сколько дней отпуска сотрудник *уже взял* в этом году?\n(введи 0, если ещё не брал)" if lang == "ru"
        else "Wie viele Urlaubstage wurden in diesem Jahr *bereits genommen*?\n(0 eingeben falls keine)"
    )
    await q.edit_message_text(text)
    return UR_GENOMMEN


async def ur_genommen(update: Update, context: CallbackContext) -> int:
    lang = _clang(context)
    try:
        genommen = float(update.message.text.strip().replace(",", "."))
        assert genommen >= 0
    except Exception:
        text = "❌ Введи число (например 5 или 0):" if lang == "ru" else "❌ Bitte Zahl eingeben (z.B. 5 oder 0):"
        await update.message.reply_text(text)
        return UR_GENOMMEN

    d = context.user_data
    ja = d["ur_ja"]
    vz = d["ur_vz"]
    eigen = d["ur_eigen"]
    monate = d["ur_monate"]

    # Teilzeit-Anpassung
    anspruch_teilzeit = ja / vz * eigen
    # Zeitanteilige Kürzung (Einstellung / Austritt)
    anspruch_anteilig = anspruch_teilzeit * monate / 12
    resturlaub = anspruch_anteilig - genommen

    def f(x: float) -> str:
        return f"{x:.2f}".replace(".", ",")

    if lang == "ru":
        text = (
            f"✅ *Результат: Urlaubsrechner (калькулятор отпуска)*\n\n"
            f"Годовой норматив (Vollzeit, {vz}-дневная неделя): *{f(ja)} дн.*\n"
            f"С учётом неполной занятости ({eigen}/{vz} дн.): *{f(anspruch_teilzeit)} дн.*\n"
            f"Пропорционально периоду ({monate}/12 мес.): *{f(anspruch_anteilig)} дн.*\n"
            f"Уже использовано: *{f(genommen)} дн.*\n"
            f"──────────────────────────────\n"
            f"*Остаток отпуска (Resturlaub): {f(resturlaub)} дн.*\n\n"
            f"ℹ️ Дробные значения ≥ 0,5 рабочего дня округляются в большую сторону (§ 5 Abs. 2 BUrlG).\n"
            f"⚠️ Tarifvertrag (тарифный договор) или трудовой договор могут предусматривать иные условия.\n\n"
            f"📄 Сверь результат со своей Gehaltsabrechnung (расчётный листок) — там указан актуальный "
            f"Resturlaub. При расхождении обратись в отдел кадров."
        )
    else:
        text = (
            f"✅ *Urlaubsrechner-Ergebnis*\n\n"
            f"Jahresanspruch (Vollzeit {vz}-Tage-Woche): *{f(ja)} Tage*\n"
            f"Teilzeit-Anpassung ({eigen}/{vz} Tage):       *{f(anspruch_teilzeit)} Tage*\n"
            f"Zeitanteilig ({monate}/12 Monate):             *{f(anspruch_anteilig)} Tage*\n"
            f"Bereits genommen:                              *{f(genommen)} Tage*\n"
            f"──────────────────────────────\n"
            f"*Resturlaub: {f(resturlaub)} Tage*\n\n"
            f"ℹ️ Bruchteile ≥ 0,5 Arbeitstage werden auf volle Tage aufgerundet (§ 5 Abs. 2 BUrlG).\n"
            f"⚠️ Tarifvertragliche oder vertragliche Regelungen können abweichen.\n\n"
            f"📄 Vergleichen Sie das Ergebnis mit Ihrer Gehaltsabrechnung — dort steht der aktuelle "
            f"Resturlaub. Bei Abweichungen bitte an die Personalabteilung wenden."
        )

    await update.message.reply_text(text, parse_mode="Markdown")
    return ConversationHandler.END


def get_urlaub_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("urlaub", ur_start),
            CallbackQueryHandler(ur_start_from_button, pattern="^calc:urlaub$"),
        ],
        states={
            UR_JAHRESANSPRUCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, ur_jahresanspruch)],
            UR_VOLLZEIT:       [CallbackQueryHandler(ur_vollzeit, pattern="^[56]$")],
            UR_EIGEN:          [CallbackQueryHandler(ur_eigen, pattern="^[1-6]$")],
            UR_MONATE:         [CallbackQueryHandler(ur_monate, pattern="^([1-9]|1[0-2])$")],
            UR_GENOMMEN:       [MessageHandler(filters.TEXT & ~filters.COMMAND, ur_genommen)],
        },
        fallbacks=[CommandHandler("cancel", _cancel), CommandHandler("urlaub", ur_start)],
        per_message=False,
        allow_reentry=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# BRUTTO-NETTO-RECHNER 2026 (Niedersachsen)
# ═══════════════════════════════════════════════════════════════════════════════

def _grundtarif_2026(zvE: float) -> float:
    """§ 32a EStG Grundtarif 2026 — Jahresbetrag."""
    if zvE <= 12_348:
        return 0.0
    elif zvE <= 17_602:
        y = (zvE - 12_348) / 10_000
        return (974.0 * y + 1_400.0) * y
    elif zvE <= 66_760:
        z = (zvE - 17_602) / 10_000
        return (181.19 * z + 2_397.0) * z + 1_025.0
    elif zvE <= 277_826:
        return 0.42 * zvE - 10_602.0   # Kontinuität bei 66.760
    else:
        return 0.45 * zvE - 18_934.0   # Kontinuität bei 277.826


def _lohnsteuer_jahr(zvE: float, sk: int) -> float:
    """Lohnsteuer (Jahresbetrag) je Steuerklasse."""
    if sk == 3:
        return math.floor(_grundtarif_2026(zvE / 2) * 2)
    if sk == 2:
        return math.floor(_grundtarif_2026(max(0, zvE - 4_260)))
    if sk == 5:
        return math.floor(_grundtarif_2026(zvE + _GFB))
    if sk == 6:
        return math.floor(max(0, zvE * 0.42))
    return math.floor(_grundtarif_2026(zvE))   # SK I / IV


def berechne_netto(brutto_m: float, sk: int, kinder: bool) -> dict:
    """Nettolohn monatlich — Niedersachsen 2026. Ohne Kirchensteuer.

    Annahme: Alter >= 23 Jahre (gilt für ~90% der Mitarbeiter),
    daher greift bei Kinderlosigkeit immer der PV-Kinderlosenzuschlag.
    """
    rv = min(brutto_m, _BBG_RV) * _RV
    av = min(brutto_m, _BBG_RV) * _AV
    kv = min(brutto_m, _BBG_KV) * (_KV + _KV_ZUSATZ)
    pv_satz = _PV + (_PV_KL_ZUSCHLAG if not kinder else 0)
    pv = min(brutto_m, _BBG_KV) * pv_satz

    # Lohnsteuer auf Jahresbasis
    lst_j = _lohnsteuer_jahr(brutto_m * 12, sk)
    lst_m = lst_j / 12

    # Solidaritätszuschlag 2026 (nur Spitzenverdiener)
    soli_grenze_m = 18_130 / 12
    milderung_m   = 16_245 / 12
    if lst_m > soli_grenze_m:
        soli = lst_m * 0.055
    elif lst_m > milderung_m:
        soli = (lst_m - milderung_m) * 0.199
    else:
        soli = 0.0

    abzuege = rv + av + kv + pv + lst_m + soli
    return {
        "brutto": brutto_m, "rv": rv, "av": av, "kv": kv, "pv": pv,
        "lst": lst_m, "soli": soli,
        "abzuege": abzuege, "netto": brutto_m - abzuege,
    }


async def bn_start(update: Update, context: CallbackContext) -> int:
    lang = _clang(context)
    profile = context.user_data.get("profile")
    context.user_data.clear()
    context.user_data["lang"] = lang
    if profile is not None:
        context.user_data["profile"] = profile
    text = (
        "💶 *Калькулятор Brutto-Netto (брутто → нетто) 2026*\n"
        "📍 Bundesland (земля): *Niedersachsen*\n\n"
        "Введи *месячную зарплату брутто (Bruttogehalt)* в евро (например 3500):" if lang == "ru"
        else "💶 *Brutto-Netto-Rechner 2026*\n"
             "📍 Bundesland: *Niedersachsen*\n\n"
             "Bitte *monatliches Bruttogehalt* in Euro eingeben (z.B. 3500):"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    return BN_BRUTTO


async def bn_brutto(update: Update, context: CallbackContext) -> int:
    lang = _clang(context)
    v = _parse_euro(update.message.text)
    if v is None:
        text = (
            "❌ Неверный ввод. Введи число (например 3500):" if lang == "ru"
            else "❌ Ungültige Eingabe. Bitte Zahl eingeben (z.B. 3500):"
        )
        await update.message.reply_text(text)
        return BN_BRUTTO
    context.user_data["bn_brutto"] = v

    if lang == "ru":
        kb = [
            [InlineKeyboardButton("I — холост/не замужем", callback_data="1"),
             InlineKeyboardButton("II — один родитель", callback_data="2"),
             InlineKeyboardButton("III — единств. кормилец", callback_data="3")],
            [InlineKeyboardButton("IV — в браке", callback_data="4"),
             InlineKeyboardButton("V — низкий доход", callback_data="5"),
             InlineKeyboardButton("VI — вторая работа", callback_data="6")],
        ]
        text = "Выбери *Steuerklasse* (налоговый класс):"
    else:
        kb = [
            [InlineKeyboardButton("I — ledig", callback_data="1"),
             InlineKeyboardButton("II — allein­erziehend", callback_data="2"),
             InlineKeyboardButton("III — Allein­verdiener", callback_data="3")],
            [InlineKeyboardButton("IV — verheiratet", callback_data="4"),
             InlineKeyboardButton("V — Geringverdiener", callback_data="5"),
             InlineKeyboardButton("VI — Zweitjob", callback_data="6")],
        ]
        text = "Bitte *Steuerklasse* wählen:"

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return BN_SK


async def bn_sk(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()
    lang = _clang(context)
    context.user_data["bn_sk"] = int(q.data)

    if lang == "ru":
        kb = [[InlineKeyboardButton("Да, есть дети", callback_data="ja"),
               InlineKeyboardButton("Нет", callback_data="nein")]]
        text = "Есть ли у сотрудника *дети* (Kinder, до 25 лет)?"
    else:
        kb = [[InlineKeyboardButton("Ja, mit Kindern", callback_data="ja"),
               InlineKeyboardButton("Nein", callback_data="nein")]]
        text = "Hat der Mitarbeiter *Kinder* (unter 25 Jahren)?"

    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return BN_KINDER


async def bn_kinder(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()
    lang = _clang(context)

    d = context.user_data
    kinder = q.data == "ja"
    d["bn_kinder"] = kinder
    r = berechne_netto(d["bn_brutto"], d["bn_sk"], kinder)

    def f(x: float) -> str:
        return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

    sk_names = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}
    soli_line_ru = f"  Solidaritätszuschlag (солидарный сбор): {f(r['soli'])}\n" if r["soli"] > 0.01 else ""
    soli_line_de = f"  Solidaritätszuschlag:  {f(r['soli'])}\n" if r["soli"] > 0.01 else ""

    if lang == "ru":
        kl_hinweis = (
            "" if kinder
            else "\n_Доплата к Pflegeversicherung (страхование на случай нужды в уходе) "
                 "для бездетных: +0,6 % (§ 55 SGB XI)_"
        )
        text = (
            f"✅ *Результат: Brutto-Netto (брутто → нетто) 2026*\n"
            f"📍 Niedersachsen | Steuerklasse {sk_names[d['bn_sk']]}\n\n"
            f"Брутто (Bruttogehalt):              {f(r['brutto'])}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  Rentenversicherung (пенс. страх.):  {f(r['rv'])}\n"
            f"  Arbeitslosenversicherung (страх. от безработицы): {f(r['av'])}\n"
            f"  Krankenversicherung (мед. страх.):  {f(r['kv'])}\n"
            f"  Pflegeversicherung (страх. на случай нужды в уходе): {f(r['pv'])}\n"
            f"  Lohnsteuer (подоходный налог):      {f(r['lst'])}\n"
            f"{soli_line_ru}"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Всего вычетов (Gesamtabzüge):       -{f(r['abzuege'])}\n"
            f"*Нетто (Nettogehalt):                {f(r['netto'])}*\n"
            f"{kl_hinweis}\n\n"
            f"⚠️ _Это приблизительный расчёт по § 32a EStG 2026, без учёта Kirchensteuer "
            f"(церковный налог) и без учёта точного Zusatzbeitrag (дополнительный взнос) "
            f"твоей Krankenkasse (больничной кассы) — использован усреднённый процент. "
            f"Реальная сумма в Lohnabrechnung (расчётный листок) "
            f"может отличаться примерно на ±100 €. Для точного расчёта обратись "
            f"к Steuerberater (налоговому консультанту) или в отдел кадров._"
        )
    else:
        kl_hinweis = "" if kinder else "\n_Kinderlos-Zuschlag PV: +0,6 % (§ 55 SGB XI)_"
        text = (
            f"✅ *Brutto-Netto-Ergebnis 2026*\n"
            f"📍 Niedersachsen | Steuerklasse {sk_names[d['bn_sk']]}\n\n"
            f"Bruttogehalt:             {f(r['brutto'])}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  Rentenversicherung:     {f(r['rv'])}\n"
            f"  Arbeitslosenvers.:      {f(r['av'])}\n"
            f"  Krankenversicherung:    {f(r['kv'])}\n"
            f"  Pflegeversicherung:     {f(r['pv'])}\n"
            f"  Lohnsteuer:             {f(r['lst'])}\n"
            f"{soli_line_de}"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Gesamtabzüge:            -{f(r['abzuege'])}\n"
            f"*Nettogehalt:             {f(r['netto'])}*\n"
            f"{kl_hinweis}\n\n"
            f"⚠️ _Näherungsrechnung nach § 32a EStG 2026, ohne Kirchensteuer und ohne "
            f"den individuellen Zusatzbeitrag Ihrer Krankenkasse (es wird ein "
            f"Durchschnittswert verwendet). "
            f"Die tatsächliche Gehaltsabrechnung kann um ca. ±100 € abweichen. "
            f"Für eine genaue Berechnung: Steuerberater oder Personalabteilung kontaktieren._"
        )

    await q.edit_message_text(text, parse_mode="Markdown")
    return ConversationHandler.END


def get_bruttonetto_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("bruttonetto", bn_start),
            CallbackQueryHandler(bn_start_from_button, pattern="^calc:bruttonetto$"),
        ],
        states={
            BN_BRUTTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bn_brutto)],
            BN_SK:     [CallbackQueryHandler(bn_sk, pattern="^[1-6]$")],
            BN_KINDER: [CallbackQueryHandler(bn_kinder, pattern="^(ja|nein)$")],
        },
        fallbacks=[CommandHandler("cancel", _cancel), CommandHandler("bruttonetto", bn_start)],
        per_message=False,
        allow_reentry=True,
    )
