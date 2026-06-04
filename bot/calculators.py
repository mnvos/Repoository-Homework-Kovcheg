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
BN_BRUTTO, BN_SK, BN_ALTER, BN_KINDER, BN_KIRCHE = range(20, 25)

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
_KIRCHE_NI = 0.09    # Niedersachsen 9 %


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
    await update.message.reply_text("Berechnung abgebrochen. (/kuendigung /urlaub /bruttonetto)")
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
    kb = [
        [InlineKeyboardButton("Arbeitgeber kündigt", callback_data="ag"),
         InlineKeyboardButton("Arbeitnehmer kündigt", callback_data="an")],
    ]
    await update.message.reply_text(
        "⚖️ *Kündigungsfrist-Rechner (§ 622 BGB)*\n\nWer spricht die Kündigung aus?",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return KU_SIDE


async def ku_side(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()
    context.user_data["ku_seite"] = q.data
    kb = [[InlineKeyboardButton("Ja — Probezeit", callback_data="ja"),
           InlineKeyboardButton("Nein", callback_data="nein")]]
    await q.edit_message_text(
        "Befindet sich der Mitarbeiter noch in der *Probezeit* (max. 6 Monate)?",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return KU_PROBEZEIT


async def ku_probezeit(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()
    if q.data == "ja":
        ende = date.today() + timedelta(weeks=2)
        await q.edit_message_text(
            f"✅ *Ergebnis (Probezeit)*\n\n"
            f"Frist: *2 Wochen* — beliebiger Tag möglich\n"
            f"Letzter Arbeitstag (ab heute): *{ende.strftime('%d.%m.%Y')}*\n\n"
            f"⚠️ Bitte prüfen Sie den Arbeitsvertrag auf abweichende Regelungen.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END
    await q.edit_message_text(
        "📅 Bitte *Einstellungsdatum* eingeben (z.B. 15.03.2019):"
    )
    return KU_EINSTELLUNG


async def ku_einstellung(update: Update, context: CallbackContext) -> int:
    d = _parse_date(update.message.text)
    if not d:
        await update.message.reply_text("❌ Datum nicht erkannt. Bitte erneut eingeben (z.B. 15.03.2019):")
        return KU_EINSTELLUNG
    context.user_data["ku_einstellung"] = d
    await update.message.reply_text(
        "📅 Wann wird die Kündigung *übergeben / zugestellt*? (z.B. 20.06.2026):"
    )
    return KU_KUENDIGUNG


async def ku_kuendigung(update: Update, context: CallbackContext) -> int:
    kuend = _parse_date(update.message.text)
    if not kuend:
        await update.message.reply_text("❌ Datum nicht erkannt. Bitte erneut eingeben:")
        return KU_KUENDIGUNG

    einst: date = context.user_data["ku_einstellung"]
    seite: str = context.user_data["ku_seite"]
    delta = relativedelta(kuend, einst)
    years = delta.years

    if seite == "an":
        letzter = _an_kuendigungstermin(kuend)
        frist_text = "4 Wochen zum 15. oder Monatsende"
    else:
        m = _ag_frist_monate(years)
        letzter = _letzter_tag_monat(kuend + relativedelta(months=m))
        frist_text = (
            "4 Wochen zum 15. oder Monatsende" if m == 1
            else f"{m} Monate zum Monatsende"
        )
        if m == 1:
            letzter = _an_kuendigungstermin(kuend)

    verbleibend = (letzter - date.today()).days
    seite_label = "Arbeitgeber" if seite == "ag" else "Arbeitnehmer"

    await update.message.reply_text(
        f"✅ *Kündigungsfrist-Ergebnis*\n\n"
        f"Seite: *{seite_label}*\n"
        f"Betriebszugehörigkeit: *{years} Jahr(e)*\n"
        f"Kündigung übergeben am: *{kuend.strftime('%d.%m.%Y')}*\n"
        f"Gesetzliche Frist: *{frist_text}*\n"
        f"Letzter Arbeitstag: *{letzter.strftime('%d.%m.%Y')}*\n"
        f"Verbleibende Tage: *{verbleibend} Tage*\n\n"
        f"⚠️ Tarifvertrag oder Arbeitsvertrag kann längere Fristen vorsehen. "
        f"Im Zweifel Rücksprache mit Rechtsanwalt oder Steuerberater.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


def get_kuendigung_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("kuendigung", ku_start)],
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
    context.user_data.clear()
    await update.message.reply_text(
        "🏖️ *Urlaubsrechner*\n\n"
        "Wie viele Urlaubstage stehen dem Mitarbeiter *pro Kalenderjahr* zu?",
        parse_mode="Markdown",
    )
    return UR_JAHRESANSPRUCH


async def ur_jahresanspruch(update: Update, context: CallbackContext) -> int:
    try:
        tage = float(update.message.text.strip().replace(",", "."))
        assert 1 <= tage <= 365
    except Exception:
        await update.message.reply_text("❌ Bitte Zahl eingeben (z.B. 30):")
        return UR_JAHRESANSPRUCH
    context.user_data["ur_ja"] = tage
    kb = [[InlineKeyboardButton("5-Tage-Woche", callback_data="5"),
           InlineKeyboardButton("6-Tage-Woche", callback_data="6")]]
    await update.message.reply_text(
        "Wie viele Tage arbeitet ein *Vollzeitmitarbeiter* pro Woche in Ihrer Firma?",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return UR_VOLLZEIT


async def ur_vollzeit(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()
    vollzeit = int(q.data)
    context.user_data["ur_vz"] = vollzeit
    buttons = [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, vollzeit + 1)]
    rows = [buttons[:3], buttons[3:6]]
    await q.edit_message_text(
        "Wie viele Tage pro Woche arbeitet *dieser Mitarbeiter*?",
        reply_markup=InlineKeyboardMarkup([r for r in rows if r]),
        parse_mode="Markdown",
    )
    return UR_EIGEN


async def ur_eigen(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()
    context.user_data["ur_eigen"] = int(q.data)
    kb = [
        [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, 7)],
        [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(7, 13)],
    ]
    await q.edit_message_text(
        "Für wie viele *Monate* in diesem Jahr besteht Urlaubsanspruch?\n"
        "(12 = ganzes Jahr, z.B. 6 = ab 01.07. eingestellt)",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return UR_MONATE


async def ur_monate(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()
    context.user_data["ur_monate"] = int(q.data)
    await q.edit_message_text(
        "Wie viele Urlaubstage wurden in diesem Jahr *bereits genommen*?\n(0 eingeben falls keine)"
    )
    return UR_GENOMMEN


async def ur_genommen(update: Update, context: CallbackContext) -> int:
    try:
        genommen = float(update.message.text.strip().replace(",", "."))
        assert genommen >= 0
    except Exception:
        await update.message.reply_text("❌ Bitte Zahl eingeben (z.B. 5 oder 0):")
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

    await update.message.reply_text(
        f"✅ *Urlaubsrechner-Ergebnis*\n\n"
        f"Jahresanspruch (Vollzeit {vz}-Tage-Woche): *{f(ja)} Tage*\n"
        f"Teilzeit-Anpassung ({eigen}/{vz} Tage):       *{f(anspruch_teilzeit)} Tage*\n"
        f"Zeitanteilig ({monate}/12 Monate):             *{f(anspruch_anteilig)} Tage*\n"
        f"Bereits genommen:                              *{f(genommen)} Tage*\n"
        f"──────────────────────────────\n"
        f"*Resturlaub: {f(resturlaub)} Tage*\n\n"
        f"ℹ️ Bruchteile ≥ 0,5 Arbeitstage werden auf volle Tage aufgerundet (§ 5 Abs. 2 BUrlG).\n"
        f"⚠️ Tarifvertragliche oder vertragliche Regelungen können abweichen.\n\n"
        f"📄 Сверь результат со своей *Gehaltsabrechnung* — там указан актуальный Resturlaub. "
        f"При расхождении обратись в отдел кадров.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


def get_urlaub_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("urlaub", ur_start)],
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


def berechne_netto(brutto_m: float, sk: int, alter: int, kinder: bool, kirche: bool) -> dict:
    """Nettolohn monatlich — Niedersachsen 2026."""
    rv = min(brutto_m, _BBG_RV) * _RV
    av = min(brutto_m, _BBG_RV) * _AV
    kv = min(brutto_m, _BBG_KV) * (_KV + _KV_ZUSATZ)
    pv_satz = _PV + (_PV_KL_ZUSCHLAG if (not kinder and alter >= 23) else 0)
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

    kirche_b = lst_m * _KIRCHE_NI if kirche else 0.0

    abzuege = rv + av + kv + pv + lst_m + soli + kirche_b
    return {
        "brutto": brutto_m, "rv": rv, "av": av, "kv": kv, "pv": pv,
        "lst": lst_m, "soli": soli, "kirche": kirche_b,
        "abzuege": abzuege, "netto": brutto_m - abzuege,
    }


async def bn_start(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "💶 *Brutto-Netto-Rechner 2026*\n"
        "📍 Bundesland: *Niedersachsen*\n\n"
        "Bitte *monatliches Bruttogehalt* in Euro eingeben (z.B. 3500):",
        parse_mode="Markdown",
    )
    return BN_BRUTTO


async def bn_brutto(update: Update, context: CallbackContext) -> int:
    v = _parse_euro(update.message.text)
    if v is None:
        await update.message.reply_text("❌ Ungültige Eingabe. Bitte Zahl eingeben (z.B. 3500):")
        return BN_BRUTTO
    context.user_data["bn_brutto"] = v
    kb = [
        [InlineKeyboardButton("I — ledig", callback_data="1"),
         InlineKeyboardButton("II — allein­erziehend", callback_data="2"),
         InlineKeyboardButton("III — Allein­verdiener", callback_data="3")],
        [InlineKeyboardButton("IV — verheiratet", callback_data="4"),
         InlineKeyboardButton("V — Geringverdiener", callback_data="5"),
         InlineKeyboardButton("VI — Zweitjob", callback_data="6")],
    ]
    await update.message.reply_text(
        "Bitte *Steuerklasse* wählen:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return BN_SK


async def bn_sk(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()
    context.user_data["bn_sk"] = int(q.data)
    await q.edit_message_text("Wie alt ist der Mitarbeiter? (Zahl eingeben, z.B. 35)")
    return BN_ALTER


async def bn_alter(update: Update, context: CallbackContext) -> int:
    try:
        alter = int(update.message.text.strip())
        assert 14 <= alter <= 85
    except Exception:
        await update.message.reply_text("❌ Bitte gültiges Alter eingeben (z.B. 35):")
        return BN_ALTER
    context.user_data["bn_alter"] = alter
    kb = [[InlineKeyboardButton("Ja, mit Kindern", callback_data="ja"),
           InlineKeyboardButton("Nein", callback_data="nein")]]
    await update.message.reply_text(
        "Hat der Mitarbeiter *Kinder* (unter 25 Jahren)?",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return BN_KINDER


async def bn_kinder(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()
    context.user_data["bn_kinder"] = q.data == "ja"
    kb = [[InlineKeyboardButton("Ja (Kirchensteuer)", callback_data="ja"),
           InlineKeyboardButton("Nein", callback_data="nein")]]
    await q.edit_message_text(
        "Zahlt der Mitarbeiter *Kirchensteuer*? (Niedersachsen: 9 %)",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return BN_KIRCHE


async def bn_kirche(update: Update, context: CallbackContext) -> int:
    q = update.callback_query
    await q.answer()

    d = context.user_data
    r = berechne_netto(d["bn_brutto"], d["bn_sk"], d["bn_alter"], d["bn_kinder"], q.data == "ja")

    def f(x: float) -> str:
        return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

    sk_names = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}
    kl_hinweis = "" if d["bn_kinder"] else "\n_Kinderlos-Zuschlag PV: +0,6 % (§ 55 SGB XI)_"
    soli_line = f"  Solidaritätszuschlag:  {f(r['soli'])}\n" if r["soli"] > 0.01 else ""
    kirche_line = f"  Kirchensteuer (9 %):   {f(r['kirche'])}\n" if r["kirche"] > 0.01 else ""

    await q.edit_message_text(
        f"✅ *Brutto-Netto-Ergebnis 2026*\n"
        f"📍 Niedersachsen | Steuerklasse {sk_names[d['bn_sk']]}\n\n"
        f"Bruttogehalt:             {f(r['brutto'])}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  Rentenversicherung:     {f(r['rv'])}\n"
        f"  Arbeitslosenvers.:      {f(r['av'])}\n"
        f"  Krankenversicherung:    {f(r['kv'])}\n"
        f"  Pflegeversicherung:     {f(r['pv'])}\n"
        f"  Lohnsteuer:             {f(r['lst'])}\n"
        f"{soli_line}"
        f"{kirche_line}"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Gesamtabzüge:            -{f(r['abzuege'])}\n"
        f"*Nettogehalt:             {f(r['netto'])}*\n"
        f"{kl_hinweis}\n\n"
        f"⚠️ _Näherungsrechnung nach § 32a EStG 2026. "
        f"Für offizielle Lohnabrechnungen: Steuerberater befragen._",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


def get_bruttonetto_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("bruttonetto", bn_start)],
        states={
            BN_BRUTTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bn_brutto)],
            BN_SK:     [CallbackQueryHandler(bn_sk, pattern="^[1-6]$")],
            BN_ALTER:  [MessageHandler(filters.TEXT & ~filters.COMMAND, bn_alter)],
            BN_KINDER: [CallbackQueryHandler(bn_kinder, pattern="^(ja|nein)$")],
            BN_KIRCHE: [CallbackQueryHandler(bn_kirche, pattern="^(ja|nein)$")],
        },
        fallbacks=[CommandHandler("cancel", _cancel), CommandHandler("bruttonetto", bn_start)],
        per_message=False,
        allow_reentry=True,
    )
