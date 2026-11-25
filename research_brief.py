from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import pandas as pd
import streamlit as st

try:
    from fpdf import FPDF  # type: ignore
    _HAS_FPDF = True
except Exception:
    _HAS_FPDF = False


@dataclass(frozen=True)
class PharmaQuantSnapshot:
    ticker: str
    company_name: str
    spot_price: float
    implied_price: float
    ufcf_y1: float
    ufcf_y5: float
    tv_share_pct: float
    wacc_pct: float
    terminal_g_pct: float
    dio_days: float
    dso_days: float
    dpo_days: float
    ccc_days: float
    ev_ebitda: float
    pe_ratio: float
    gross_margin_pct: float
    ebit_margin_pct: float
    peer_ev_ebitda: float
    peer_pe_ratio: float
    vol_pct: float
    max_drawdown_pct: float
    beta: float
    sharpe_ratio: float
    currency: str = "₦"
    scenario: str = "Base"
    rating: str = "HOLD"
    rating_score: float = 50.0
    roic_pct: float = 12.0
    net_debt_to_ebitda: float = 1.0
    wc_cash_unlocked_m: float = 0.0
    equity_distress_flag: bool = False
    data_source: str = "NGX 9M 2026 Filings"
    as_of: str = "25 Nov 2026"


def _fmt_price(val: float, cur: str = "₦") -> str:
    sign = "-" if val < 0 else ""
    return f"{sign}{cur}{abs(val):,.2f}"


def _fmt_m(val: float, cur: str = "₦") -> str:
    sign = "-" if val < 0 else ""
    return f"{sign}{cur}{abs(val):,.1f}M"


def _build_investor_writeup(snap: PharmaQuantSnapshot, upside_pct: float, roic_spread: float) -> list[tuple[str, str]]:
    if snap.rating in ("STRONG BUY", "BUY"):
        stance = (
            "constructive fundamental quality, strong return on invested capital, and balanced peer multiples"
            if upside_pct < 0
            else "attractive upside relative to current trading levels alongside solid operating fundamentals"
        )
    elif snap.rating == "HOLD":
        stance = "balanced risk-reward where execution on margins and working capital will drive the next leg"
    else:
        stance = "cautious positioning given valuation, leverage, or cash-flow headwinds under current assumptions"

    capital_note = (
        f"generates positive economic value add with ROIC of {snap.roic_pct:.1f}% versus a {snap.wacc_pct:.1f}% WACC ({roic_spread:+.1f} pp spread)"
        if roic_spread >= 0
        else f"currently earns a ROIC of {snap.roic_pct:.1f}% versus its {snap.wacc_pct:.1f}% WACC ({roic_spread:+.1f} pp spread), keeping margin discipline front and center"
    )
    leverage_note = (
        f"conservative net leverage at {snap.net_debt_to_ebitda:.2f}x Net Debt/EBITDA"
        if snap.net_debt_to_ebitda < 1.5
        else f"moderate net leverage at {snap.net_debt_to_ebitda:.2f}x Net Debt/EBITDA"
        if snap.net_debt_to_ebitda < 2.8
        else f"elevated net leverage at {snap.net_debt_to_ebitda:.2f}x Net Debt/EBITDA that warrants close rate sensitivity tracking"
    )

    return [
        (
            "1. Investment Thesis & Valuation Summary",
            f"{snap.company_name} ({snap.ticker}) carries a {snap.rating} ({snap.rating_score:.0f}/100) stance under "
            f"the {snap.scenario} case using {snap.data_source}. At a spot price of NGN {snap.spot_price:,.2f}, "
            f"standalone 5-year unlevered free cash flow (UFCF) DCF yields an implied fair value of NGN {snap.implied_price:,.2f} "
            f"({upside_pct:+.1f}%), while multiples stand at {snap.ev_ebitda:.1f}x EV/EBITDA and {snap.pe_ratio:.1f}x P/E "
            f"versus NGX pharma peer medians of {snap.peer_ev_ebitda:.1f}x and {snap.peer_pe_ratio:.1f}x, reflecting {stance}.",
        ),
        (
            "2. Operating Margins, Cash Flows & Capital Efficiency",
            f"The business operates with a {snap.gross_margin_pct:.1f}% gross margin and {snap.ebit_margin_pct:.1f}% EBIT margin, "
            f"projecting unlevered free cash flow from NGN {snap.ufcf_y1:,.1f}M in FY+1 to NGN {snap.ufcf_y5:,.1f}M in FY+5 "
            f"(terminal value {snap.tv_share_pct:.1f}% of implied EV at {snap.terminal_g_pct:.1f}% terminal growth). "
            f"The company {capital_note}.",
        ),
        (
            "3. Working Capital & Balance Sheet Discipline",
            f"Net cash conversion is {snap.ccc_days:.0f} days (DIO {snap.dio_days:.0f}d, DSO {snap.dso_days:.0f}d, DPO {snap.dpo_days:.0f}d). "
            f"Tightening working capital unlocks an estimated NGN {snap.wc_cash_unlocked_m:,.1f}M in liquidity, alongside "
            f"{leverage_note}.",
        ),
        (
            "4. Key Risks & Investor Watchpoints",
            f"Key watchpoints include Naira FX and imported API/finished-goods cost pass-through, extended distributor "
            f"receivables or slow-moving inventory, domestic lending rate pressure, and market volatility ({snap.vol_pct:.1f}% "
            f"annualized volatility, {snap.max_drawdown_pct:.1f}% max drawdown, beta {snap.beta:.2f}, Sharpe {snap.sharpe_ratio:.2f}).",
        ),
    ]


def render_exec_brief(snap: PharmaQuantSnapshot) -> None:
    cur = snap.currency
    upside_pct = ((snap.implied_price - snap.spot_price) / max(snap.spot_price, 0.01)) * 100.0
    roic_spread = snap.roic_pct - snap.wacc_pct

    st.caption(
        f"INSTITUTIONAL TEAR-SHEET • {snap.scenario.upper()} CASE • {snap.rating} ({snap.rating_score:.0f}/100)"
    )
    st.subheader(
        f"{snap.ticker} ({snap.company_name}): Implied Fair Value {_fmt_price(snap.implied_price, cur)} "
        f"({upside_pct:+.1f}% vs. {_fmt_price(snap.spot_price, cur)})"
    )

    if snap.equity_distress_flag:
        st.warning(
            "DCF Equity Coverage Warning: Discounted cash flows under current assumptions are below net debt; "
            "per-share fair value is floored at ₦0.00 while exact unfloored equity value is shown in the bridge table."
        )

    st.markdown(
        """
        <style>
        .pq-rating-box { padding: 0.2rem 0 0.4rem 0; }
        .pq-rating-lbl { font-size: 0.85rem; color: #52606D; margin-bottom: 0.25rem; }
        .pq-rating-val { font-size: 1.25rem; font-weight: 700; line-height: 1.2; white-space: nowrap; overflow: visible; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Implied Value", _fmt_price(snap.implied_price, cur), f"{upside_pct:+.1f}% vs spot")
    with k2:
        st.metric("ROIC - WACC", f"{roic_spread:+.1f} pp", f"{snap.roic_pct:.1f}% vs {snap.wacc_pct:.1f}%")
    with k3:
        st.metric("Net CCC", f"{snap.ccc_days:.0f}d", f"+{_fmt_m(snap.wc_cash_unlocked_m, cur)} unlock")
    with k4:
        st.markdown(
            f"""
            <div class="pq-rating-box">
                <div class="pq-rating-lbl">Model Rating</div>
                <div class="pq-rating-val">{snap.rating}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"**Investor Lens:** Under the **{snap.scenario}** case, {snap.company_name} ({snap.ticker}) trades at "
        f"**{snap.ev_ebitda:.1f}x EV/EBITDA** and **{snap.pe_ratio:.1f}x P/E** with **{snap.gross_margin_pct:.1f}%** gross margin, "
        f"**{snap.ebit_margin_pct:.1f}%** EBIT margin, and **{snap.roic_pct:.1f}%** ROIC (**{roic_spread:+.1f} pp** vs. "
        f"**{snap.wacc_pct:.1f}%** WACC)."
    )
    st.markdown(
        f"**Operator Lens:** Cash durability depends on converting Naira top-line growth into free cash flow after imported "
        f"API/finished-goods FX pass-through, working-capital lockup (**{snap.ccc_days:.0f}d CCC**), and disciplined CapEx pacing."
    )


def render_dcf_brief(snap: PharmaQuantSnapshot) -> None:
    cur = snap.currency
    st.caption(f"INTRINSIC VALUATION • {snap.scenario.upper()} CASE 5-YEAR UFCF DCF")
    st.subheader(
        f"UFCF Trajectory {_fmt_m(snap.ufcf_y1, cur)} -> {_fmt_m(snap.ufcf_y5, cur)} | "
        f"Terminal Value {snap.tv_share_pct:.1f}% of EV"
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Y1 UFCF", _fmt_m(snap.ufcf_y1, cur))
    c2.metric("Y5 UFCF", _fmt_m(snap.ufcf_y5, cur))
    c3.metric("TV Share", f"{snap.tv_share_pct:.1f}%")
    c4.metric("WACC / g", f"{snap.wacc_pct:.1f}% / {snap.terminal_g_pct:.1f}%")


def render_wc_brief(snap: PharmaQuantSnapshot) -> None:
    cur = snap.currency
    st.caption("WORKING CAPITAL • CASH CONVERSION CYCLE & LIQUIDITY RELEASE")
    st.subheader(
        f"Net CCC of {snap.ccc_days:.0f} Days (DIO {snap.dio_days:.0f}d • DSO {snap.dso_days:.0f}d • DPO {snap.dpo_days:.0f}d)"
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("DIO", f"{snap.dio_days:.0f}d")
    c2.metric("DSO", f"{snap.dso_days:.0f}d")
    c3.metric("DPO", f"{snap.dpo_days:.0f}d")
    c4.metric("Cash Released", _fmt_m(snap.wc_cash_unlocked_m, cur))


def render_multiples_brief(snap: PharmaQuantSnapshot) -> None:
    st.caption("RELATIVE VALUATION • PEER MULTIPLES & MARGINS")
    st.subheader(
        f"{snap.ev_ebitda:.1f}x EV/EBITDA & {snap.pe_ratio:.1f}x P/E vs. Peers "
        f"({snap.peer_ev_ebitda:.1f}x EV/EBITDA | {snap.peer_pe_ratio:.1f}x P/E)"
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("EV / EBITDA", f"{snap.ev_ebitda:.1f}x", f"Peer {snap.peer_ev_ebitda:.1f}x")
    c2.metric("P/E", f"{snap.pe_ratio:.1f}x", f"Peer {snap.peer_pe_ratio:.1f}x")
    c3.metric("Gross Margin", f"{snap.gross_margin_pct:.1f}%")
    c4.metric("EBIT Margin", f"{snap.ebit_margin_pct:.1f}%")


def render_risk_brief(snap: PharmaQuantSnapshot) -> None:
    st.caption("RISK & RETURN • VOLATILITY, DRAWDOWN, LEVERAGE & SHARPE")
    st.subheader(
        f"Volatility {snap.vol_pct:.1f}% | Max Drawdown {snap.max_drawdown_pct:.1f}% | "
        f"Beta {snap.beta:.2f} | Sharpe {snap.sharpe_ratio:.2f}"
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Volatility", f"{snap.vol_pct:.1f}%")
    c2.metric("Max Drawdown", f"{snap.max_drawdown_pct:.1f}%")
    c3.metric("Net Debt/EBITDA", f"{snap.net_debt_to_ebitda:.2f}x")
    c4.metric("Sharpe", f"{snap.sharpe_ratio:.2f}")


def _latin_safe(text: str) -> str:
    return (
        text.replace("₦", "NGN ")
        .replace("•", "-")
        .replace("—", "-")
        .replace("–", "-")
        .replace("→", "->")
        .replace("±", "+/-")
        .replace("Δ", "Delta ")
        .encode("latin-1", errors="replace")
        .decode("latin-1")
    )


def _draw_memo_card(pdf: FPDF, heading: str, body: str, usable_w: float) -> None:
    if pdf.get_y() > 248:
        pdf.add_page()
    y_top = pdf.get_y()
    x_left = pdf.l_margin

    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(x=x_left, y=y_top, w=usable_w, h=26.0, style="DF")
    pdf.set_fill_color(13, 148, 136)
    pdf.rect(x=x_left, y=y_top, w=1.4, h=26.0, style="F")

    pdf.set_xy(x_left + 4.0, y_top + 1.8)
    pdf.set_text_color(15, 41, 66)
    pdf.set_font("Helvetica", "B", 10.0)
    pdf.multi_cell(w=usable_w - 6.0, h=5.0, text=_latin_safe(heading))

    pdf.set_x(x_left + 4.0)
    pdf.set_text_color(30, 41, 59)
    pdf.set_font("Helvetica", "", 8.8)
    pdf.multi_cell(w=usable_w - 6.0, h=4.5, text=_latin_safe(body))

    y_bottom = max(pdf.get_y() + 2.0, y_top + 27.5)
    pdf.set_y(y_bottom)


def build_pdf_memo(snap: PharmaQuantSnapshot, schedule_df: pd.DataFrame | None = None) -> bytes:
    upside_pct = ((snap.implied_price - snap.spot_price) / max(snap.spot_price, 0.01)) * 100.0
    roic_spread = snap.roic_pct - snap.wacc_pct

    if _HAS_FPDF:
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_margins(left=12, top=12, right=12)
        pdf.set_auto_page_break(auto=True, margin=14)
        pdf.add_page()
        usable_w = pdf.w - pdf.l_margin - pdf.r_margin
        x_left = pdf.l_margin

        # Top navy banner
        pdf.set_fill_color(15, 41, 66)
        pdf.set_draw_color(13, 148, 136)
        pdf.rect(x=x_left, y=12, w=usable_w, h=24.0, style="F")
        pdf.set_fill_color(13, 148, 136)
        pdf.rect(x=x_left, y=34.5, w=usable_w, h=1.5, style="F")

        pdf.set_xy(x_left + 4.0, 14.0)
        pdf.set_text_color(153, 246, 228)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.cell(w=usable_w - 8.0, h=4.0, text=_latin_safe("NGX HEALTHCARE & PHARMA VALUATION TERMINAL - INSTITUTIONAL RESEARCH MEMO"))

        pdf.set_xy(x_left + 4.0, 18.8)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 14.0)
        pdf.cell(w=usable_w - 8.0, h=7.0, text=_latin_safe(f"{snap.ticker} - {snap.company_name}"))

        pdf.set_xy(x_left + 4.0, 26.5)
        pdf.set_text_color(226, 232, 240)
        pdf.set_font("Helvetica", "", 8.0)
        pdf.cell(
            w=usable_w - 8.0,
            h=5.0,
            text=_latin_safe(
                f"{snap.scenario} Case - Rating: {snap.rating} ({snap.rating_score:.0f}/100) - "
                f"Basis: {snap.data_source} - {snap.as_of}"
            ),
        )

        # 4 KPI cards row
        y_kpi = 39.0
        gap = 2.5
        card_w = (usable_w - gap * 3.0) / 4.0
        kpi_cards = [
            ("IMPLIED DCF VALUE", f"NGN {snap.implied_price:,.2f}", f"{upside_pct:+.1f}% vs. NGN {snap.spot_price:,.2f} spot"),
            ("ROIC VS. WACC", f"{snap.roic_pct:.1f}%", f"{roic_spread:+.1f} pp vs. {snap.wacc_pct:.1f}% WACC"),
            ("CASH CONVERSION", f"{snap.ccc_days:.0f} Days", f"NGN {snap.wc_cash_unlocked_m:,.1f}M WC unlock"),
            ("NET LEVERAGE", f"{snap.net_debt_to_ebitda:.2f}x", f"EV/EBITDA {snap.ev_ebitda:.1f}x - P/E {snap.pe_ratio:.1f}x"),
        ]
        for idx, (lbl, val, note) in enumerate(kpi_cards):
            cx = x_left + idx * (card_w + gap)
            pdf.set_fill_color(255, 255, 255)
            pdf.set_draw_color(203, 213, 225)
            pdf.rect(x=cx, y=y_kpi, w=card_w, h=18.5, style="DF")
            pdf.set_fill_color(15, 41, 66)
            pdf.rect(x=cx, y=y_kpi, w=card_w, h=1.0, style="F")

            pdf.set_xy(cx + 2.0, y_kpi + 2.2)
            pdf.set_text_color(71, 85, 105)
            pdf.set_font("Helvetica", "B", 6.8)
            pdf.cell(w=card_w - 4.0, h=3.5, text=_latin_safe(lbl))

            pdf.set_xy(cx + 2.0, y_kpi + 6.3)
            pdf.set_text_color(15, 23, 42)
            pdf.set_font("Helvetica", "B", 10.5)
            pdf.cell(w=card_w - 4.0, h=5.5, text=_latin_safe(val))

            pdf.set_xy(cx + 2.0, y_kpi + 12.5)
            pdf.set_text_color(15, 118, 110)
            pdf.set_font("Helvetica", "B", 6.8)
            pdf.cell(w=card_w - 4.0, h=3.8, text=_latin_safe(note))

        pdf.set_y(y_kpi + 22.0)

        # Narrative memo blocks
        for heading, body in _build_investor_writeup(snap, upside_pct, roic_spread):
            _draw_memo_card(pdf, heading, body, usable_w)

        # 5-Year schedule table
        if schedule_df is not None and not schedule_df.empty:
            if pdf.get_y() > 215:
                pdf.add_page()
            pdf.set_x(x_left)
            pdf.set_fill_color(13, 148, 136)
            pdf.rect(x=x_left, y=pdf.get_y() + 1.0, w=1.2, h=5.5, style="F")
            pdf.set_xy(x_left + 3.0, pdf.get_y() + 0.8)
            pdf.set_text_color(15, 41, 66)
            pdf.set_font("Helvetica", "B", 10.5)
            pdf.cell(w=usable_w - 3.0, h=6.0, text=_latin_safe("5. Five-Year UFCF Projection Schedule (NGN Millions)"))
            pdf.ln(7.5)

            clean_df = schedule_df.copy()
            clean_df.columns = [_latin_safe(str(c).replace(" (₦M)", "")) for c in clean_df.columns]
            col_w = usable_w / max(len(clean_df.columns), 1)

            with pdf.table(
                col_widths=[col_w] * len(clean_df.columns),
                text_align="LEFT",
                line_height=4.8,
                padding=(1.2, 1.5, 1.2, 1.5),
            ) as table:
                pdf.set_fill_color(15, 41, 66)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Helvetica", "B", 7.8)
                hdr_row = table.row()
                for col_name in clean_df.columns:
                    hdr_row.cell(_latin_safe(str(col_name)))

                pdf.set_font("Helvetica", "", 7.6)
                for r_idx, (_, r) in enumerate(clean_df.iterrows()):
                    if r_idx % 2 == 1:
                        pdf.set_fill_color(241, 245, 249)
                    else:
                        pdf.set_fill_color(255, 255, 255)
                    pdf.set_text_color(15, 23, 42)
                    row_obj = table.row()
                    for val in r.values:
                        if isinstance(val, (int, float)) and not isinstance(val, bool):
                            txt = f"NGN {val:,.1f}M"
                        else:
                            txt = _latin_safe(str(val))
                        row_obj.cell(txt)

        # Footer line
        pdf.ln(4.0)
        pdf.set_draw_color(203, 213, 225)
        pdf.line(x_left, pdf.get_y(), x_left + usable_w, pdf.get_y())
        pdf.ln(1.8)
        pdf.set_x(x_left)
        pdf.set_text_color(71, 85, 105)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.multi_cell(
            w=usable_w,
            h=4.2,
            text=_latin_safe(
                f"Generated by NGX Healthcare & Pharma Valuation Terminal - {snap.scenario} Case ({snap.rating}) - "
                f"Source: {snap.data_source} - As of {snap.as_of}"
            ),
        )

        out = pdf.output(dest="S")
        return out.encode("latin-1") if isinstance(out, str) else bytes(out)

    buf = BytesIO()
    buf.write(b"%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    buf.write(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    buf.write(b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj\n")
    buf.write(b"4 0 obj << /Length 44 >> stream\nBT /F1 12 Tf 50 700 Td (NGX Pharma Memo) Tj ET\nendstream endobj\ntrailer << /Root 1 0 R >>\n%%EOF")
    return buf.getvalue()