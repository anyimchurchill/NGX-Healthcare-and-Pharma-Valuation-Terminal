from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CompanyFundamentals:
    ticker: str
    company_name: str
    spot_price: float
    shares_out_m: float
    revenue_m: float
    gross_margin: float
    ebit_margin: float
    da_m: float
    capex_m: float
    cash_m: float
    debt_m: float
    book_equity_m: float
    inventory_m: float
    receivables_m: float
    payables_m: float
    tax_rate: float
    wacc: float
    terminal_g: float
    rev_growth_5y: float
    beta: float
    daily_vol: float
    max_drawdown: float
    sharpe: float
    data_source: str = "NGX 9M 2026 Filings"
    as_of: str = "25 Nov 2026"

    @property
    def ebitda_m(self) -> float:
        return max(self.revenue_m * self.ebit_margin + self.da_m, 1.0)

    @property
    def ebit_m(self) -> float:
        return self.revenue_m * self.ebit_margin

    @property
    def net_debt_m(self) -> float:
        return self.debt_m - self.cash_m

    @property
    def market_cap_m(self) -> float:
        return self.spot_price * self.shares_out_m

    @property
    def ev_m(self) -> float:
        return self.market_cap_m + self.net_debt_m

    @property
    def invested_capital_m(self) -> float:
        return max(self.book_equity_m + self.debt_m - self.cash_m, 1.0)

    @property
    def dio_days(self) -> float:
        cogs = max(self.revenue_m * (1.0 - self.gross_margin), 1.0)
        return (self.inventory_m / cogs) * 365.0

    @property
    def dso_days(self) -> float:
        rev = max(self.revenue_m, 1.0)
        return (self.receivables_m / rev) * 365.0

    @property
    def dpo_days(self) -> float:
        cogs = max(self.revenue_m * (1.0 - self.gross_margin), 1.0)
        return (self.payables_m / cogs) * 365.0

    @property
    def ccc_days(self) -> float:
        return self.dio_days + self.dso_days - self.dpo_days

    @property
    def roic_pct(self) -> float:
        nopat = self.ebit_m * (1.0 - self.tax_rate)
        return (nopat / self.invested_capital_m) * 100.0


NGX_PHARMA_UNIVERSE: dict[str, CompanyFundamentals] = {
    "FIDSON": CompanyFundamentals(
        ticker="FIDSON",
        company_name="Fidson Healthcare Plc",
        spot_price=91.80,
        shares_out_m=3000.0,
        revenue_m=round(112610.0 * (4.0 / 3.0), 1),
        gross_margin=0.4345,
        ebit_margin=0.1886,
        da_m=round(4200.0 * (4.0 / 3.0), 1),
        capex_m=round(6400.0 * (4.0 / 3.0), 1),
        cash_m=10930.0,
        debt_m=23850.0,
        book_equity_m=60010.0,
        inventory_m=36955.0,
        receivables_m=29600.0,
        payables_m=23716.0,
        tax_rate=0.34,
        wacc=0.175,
        terminal_g=0.065,
        rev_growth_5y=0.185,
        beta=1.05,
        daily_vol=0.298,
        max_drawdown=-0.245,
        sharpe=1.08,
        data_source="NGX 9M 2026 Filings (Annualized Run-Rate)",
        as_of="25 Nov 2026",
    ),
    "MECURE": CompanyFundamentals(
        ticker="MECURE",
        company_name="MeCure Industries Plc",
        spot_price=56.20,
        shares_out_m=4000.0,
        revenue_m=round(70237.9 * (4.0 / 3.0), 1),
        gross_margin=0.3435,
        ebit_margin=0.2489,
        da_m=round(5690.0 * (4.0 / 3.0), 1),
        capex_m=round(6800.0 * (4.0 / 3.0), 1),
        cash_m=4320.0,
        debt_m=28740.0,
        book_equity_m=24590.0,
        inventory_m=18235.0,
        receivables_m=16400.0,
        payables_m=14200.0,
        tax_rate=0.30,
        wacc=0.185,
        terminal_g=0.065,
        rev_growth_5y=0.175,
        beta=1.25,
        daily_vol=0.345,
        max_drawdown=-0.312,
        sharpe=0.72,
        data_source="NGX 9M 2026 Filings (Annualized Run-Rate)",
        as_of="25 Nov 2026",
    ),
    "MAYBAKER": CompanyFundamentals(
        ticker="MAYBAKER",
        company_name="May & Baker Nigeria Plc",
        spot_price=44.00,
        shares_out_m=1725.0,
        revenue_m=46800.0,
        gross_margin=0.385,
        ebit_margin=0.165,
        da_m=1450.0,
        capex_m=2200.0,
        cash_m=5100.0,
        debt_m=7400.0,
        book_equity_m=18600.0,
        inventory_m=7900.0,
        receivables_m=6800.0,
        payables_m=6200.0,
        tax_rate=0.30,
        wacc=0.180,
        terminal_g=0.060,
        rev_growth_5y=0.160,
        beta=0.88,
        daily_vol=0.318,
        max_drawdown=-0.220,
        sharpe=1.14,
        data_source="NGX Baseline Reference",
        as_of="25 Nov 2026",
    ),
    "NEIMETH": CompanyFundamentals(
        ticker="NEIMETH",
        company_name="Neimeth International Pharmaceuticals Plc",
        spot_price=7.10,
        shares_out_m=4270.0,
        revenue_m=14200.0,
        gross_margin=0.410,
        ebit_margin=0.115,
        da_m=520.0,
        capex_m=750.0,
        cash_m=1150.0,
        debt_m=4850.0,
        book_equity_m=5400.0,
        inventory_m=2950.0,
        receivables_m=2400.0,
        payables_m=1900.0,
        tax_rate=0.28,
        wacc=0.195,
        terminal_g=0.055,
        rev_growth_5y=0.145,
        beta=0.92,
        daily_vol=0.380,
        max_drawdown=-0.395,
        sharpe=0.45,
        data_source="NGX Baseline Reference",
        as_of="25 Nov 2026",
    ),
    "MORISON": CompanyFundamentals(
        ticker="MORISON",
        company_name="Morison Industries Plc",
        spot_price=10.40,
        shares_out_m=1256.0,
        revenue_m=6800.0,
        gross_margin=0.330,
        ebit_margin=0.110,
        da_m=180.0,
        capex_m=190.0,
        cash_m=620.0,
        debt_m=750.0,
        book_equity_m=1850.0,
        inventory_m=950.0,
        receivables_m=820.0,
        payables_m=780.0,
        tax_rate=0.25,
        wacc=0.195,
        terminal_g=0.055,
        rev_growth_5y=0.140,
        beta=0.75,
        daily_vol=0.350,
        max_drawdown=-0.320,
        sharpe=0.50,
        data_source="NGX Baseline Reference",
        as_of="25 Nov 2026",
    ),
}


def load_custom_fundamentals_csv(
    uploaded_file: Any,
    base_universe: dict[str, CompanyFundamentals] | None = None,
) -> dict[str, CompanyFundamentals]:
    universe = {k: v for k, v in (base_universe or NGX_PHARMA_UNIVERSE).items()}
    if uploaded_file is None:
        return universe

    df = pd.read_csv(uploaded_file)
    if df.empty or "ticker" not in df.columns:
        return universe

    for _, row in df.iterrows():
        tkr = str(row.get("ticker", "")).strip().upper()
        if not tkr:
            continue
        base = universe.get(tkr, universe["FIDSON"])

        def _num(col: str, fallback: float) -> float:
            if col not in row or pd.isna(row[col]):
                return fallback
            try:
                return float(row[col])
            except (ValueError, TypeError):
                return fallback

        universe[tkr] = CompanyFundamentals(
            ticker=tkr,
            company_name=str(row.get("company_name", base.company_name)).strip() or base.company_name,
            spot_price=_num("spot_price", base.spot_price),
            shares_out_m=max(_num("shares_out_m", base.shares_out_m), 1.0),
            revenue_m=max(_num("revenue_m", base.revenue_m), 10.0),
            gross_margin=np.clip(_num("gross_margin", base.gross_margin), 0.05, 0.90),
            ebit_margin=np.clip(_num("ebit_margin", base.ebit_margin), -0.25, 0.65),
            da_m=max(_num("da_m", base.da_m), 0.0),
            capex_m=max(_num("capex_m", base.capex_m), 0.0),
            cash_m=max(_num("cash_m", base.cash_m), 0.0),
            debt_m=max(_num("debt_m", base.debt_m), 0.0),
            book_equity_m=max(_num("book_equity_m", base.book_equity_m), 1.0),
            inventory_m=max(_num("inventory_m", base.inventory_m), 0.0),
            receivables_m=max(_num("receivables_m", base.receivables_m), 0.0),
            payables_m=max(_num("payables_m", base.payables_m), 0.0),
            tax_rate=np.clip(_num("tax_rate", base.tax_rate), 0.0, 0.45),
            wacc=np.clip(_num("wacc", base.wacc), 0.10, 0.45),
            terminal_g=np.clip(_num("terminal_g", base.terminal_g), 0.01, 0.12),
            rev_growth_5y=np.clip(_num("rev_growth_5y", base.rev_growth_5y), -0.15, 0.50),
            beta=np.clip(_num("beta", base.beta), 0.10, 2.50),
            daily_vol=np.clip(_num("daily_vol", base.daily_vol), 0.05, 1.20),
            max_drawdown=np.clip(_num("max_drawdown", base.max_drawdown), -0.90, -0.01),
            sharpe=np.clip(_num("sharpe", base.sharpe), -2.0, 5.0),
            data_source="Custom CSV Upload",
            as_of=base.as_of,
        )
    return universe


def build_template_csv_bytes() -> bytes:
    rows = [
        {
            "ticker": f.ticker,
            "company_name": f.company_name,
            "spot_price": f.spot_price,
            "shares_out_m": f.shares_out_m,
            "revenue_m": f.revenue_m,
            "gross_margin": f.gross_margin,
            "ebit_margin": f.ebit_margin,
            "book_equity_m": f.book_equity_m,
            "debt_m": f.debt_m,
            "cash_m": f.cash_m,
            "wacc": f.wacc,
            "terminal_g": f.terminal_g,
            "rev_growth_5y": f.rev_growth_5y,
        }
        for f in NGX_PHARMA_UNIVERSE.values()
    ]
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


def run_dcf_model(
    f: CompanyFundamentals,
    scenario: str = "Base",
    wacc_override_pct: float | None = None,
    terminal_g_override_pct: float | None = None,
    fx_cogs_shock_bps: int = 0,
    ccc_reduction_days: int = 0,
) -> dict[str, Any]:
    """5-year UFCF DCF with smooth incremental NWC scaling and transparent EV-to-Equity bridge."""
    scen = scenario.title()
    scen_growth_mult = {"Bear": 0.78, "Base": 1.00, "Bull": 1.20}.get(scen, 1.00)
    scen_margin_mult = {"Bear": 0.92, "Base": 1.00, "Bull": 1.07}.get(scen, 1.00)
    scen_wacc_adj = {"Bear": 0.015, "Base": 0.000, "Bull": -0.012}.get(scen, 0.000)

    wacc = (wacc_override_pct / 100.0) if wacc_override_pct is not None else (f.wacc + scen_wacc_adj)
    wacc = float(np.clip(wacc, 0.12, 0.42))

    term_g = (terminal_g_override_pct / 100.0) if terminal_g_override_pct is not None else f.terminal_g
    term_g = float(np.clip(term_g, 0.01, min(wacc - 0.03, 0.10)))

    fx_drag = (fx_cogs_shock_bps / 10000.0) * 0.40
    eff_ebit_margin = float(np.clip(f.ebit_margin * scen_margin_mult - fx_drag, 0.02, 0.55))
    eff_growth = float(np.clip(f.rev_growth_5y * scen_growth_mult, -0.05, 0.45))

    raw_nwc_ratio = (f.inventory_m + f.receivables_m - f.payables_m) / max(f.revenue_m, 1.0)
    nwc_ratio_base = float(np.clip(raw_nwc_ratio, 0.04, 0.22))
    wc_relief_factor = float(np.clip(ccc_reduction_days / 365.0, 0.0, 0.12))
    eff_nwc_ratio = float(np.clip(nwc_ratio_base - wc_relief_factor, 0.03, 0.22))

    da_ratio = float(np.clip(f.da_m / max(f.revenue_m, 1.0), 0.01, 0.12))
    capex_ratio = float(np.clip(f.capex_m / max(f.revenue_m, 1.0), 0.015, 0.14))

    schedule_rows = []
    prev_rev = f.revenue_m
    pv_ufcf_sum = 0.0

    for yr in range(1, 6):
        rev = prev_rev * (1.0 + eff_growth)
        delta_rev = rev - prev_rev
        ebit = rev * eff_ebit_margin
        da = rev * da_ratio
        ebitda = ebit + da
        nopat = ebit * (1.0 - f.tax_rate)
        capex = rev * capex_ratio
        delta_nwc = delta_rev * eff_nwc_ratio
        ufcf = nopat + da - capex - delta_nwc
        disc_factor = (1.0 + wacc) ** yr
        pv_ufcf = ufcf / disc_factor
        pv_ufcf_sum += pv_ufcf

        schedule_rows.append(
            {
                "Year": f"FY+{yr}",
                "Revenue (₦M)": round(rev, 1),
                "EBITDA (₦M)": round(ebitda, 1),
                "EBIT (₦M)": round(ebit, 1),
                "CapEx (₦M)": round(capex, 1),
                "ΔNWC (₦M)": round(delta_nwc, 1),
                "UFCF (₦M)": round(ufcf, 1),
                "PV of UFCF (₦M)": round(pv_ufcf, 1),
            }
        )
        prev_rev = rev

    ufcf_y5 = schedule_rows[-1]["UFCF (₦M)"]
    terminal_value = (ufcf_y5 * (1.0 + term_g)) / max(wacc - term_g, 0.01)
    pv_terminal_value = terminal_value / ((1.0 + wacc) ** 5)

    wc_cash_unlocked_m = max(f.revenue_m * wc_relief_factor, 0.0)
    implied_ev = pv_ufcf_sum + pv_terminal_value + wc_cash_unlocked_m
    implied_equity_m = implied_ev - f.net_debt_m
    equity_distress_flag = implied_equity_m < 0.0
    raw_per_share = implied_equity_m / max(f.shares_out_m, 1.0)
    display_per_share = max(raw_per_share, 0.0)
    upside_pct = ((display_per_share - f.spot_price) / max(f.spot_price, 0.01)) * 100.0
    tv_share_pct = (pv_terminal_value / max(implied_ev, 1.0)) * 100.0

    return {
        "scenario": scen,
        "wacc_pct": round(wacc * 100.0, 2),
        "terminal_g_pct": round(term_g * 100.0, 2),
        "pv_ufcf_sum_m": round(pv_ufcf_sum, 1),
        "pv_terminal_value_m": round(pv_terminal_value, 1),
        "net_debt_m": round(f.net_debt_m, 1),
        "implied_ev_m": round(implied_ev, 1),
        "implied_equity_m": round(implied_equity_m, 1),
        "equity_distress_flag": equity_distress_flag,
        "implied_price": round(display_per_share, 2),
        "upside_pct": round(upside_pct, 1),
        "ufcf_y1": schedule_rows[0]["UFCF (₦M)"],
        "ufcf_y5": ufcf_y5,
        "tv_share_pct": round(tv_share_pct, 1),
        "wc_cash_unlocked_m": round(wc_cash_unlocked_m, 1),
        "schedule_df": pd.DataFrame(schedule_rows),
    }


def compute_institutional_rating(
    f: CompanyFundamentals,
    dcf: dict[str, Any],
    peer_ev_ebitda: float | None = None,
) -> tuple[str, float]:
    score = 50.0

    upside = dcf["upside_pct"]
    if upside > 25:
        score += 12
    elif upside > 8:
        score += 7
    elif upside > -12:
        score += 2
    elif upside < -35:
        score -= 10
    elif upside < -15:
        score -= 5

    roic_spread = f.roic_pct - dcf["wacc_pct"]
    if roic_spread > 8.0:
        score += 14
    elif roic_spread > 2.0:
        score += 9
    elif roic_spread > -2.0:
        score += 3
    else:
        score -= 6

    if f.ccc_days < 80:
        score += 8
    elif f.ccc_days < 105:
        score += 4
    elif f.ccc_days > 140:
        score -= 7

    nd_ebitda = f.net_debt_m / max(f.ebitda_m, 1.0)
    if nd_ebitda < 1.0:
        score += 8
    elif nd_ebitda < 2.0:
        score += 4
    elif nd_ebitda > 3.5:
        score -= 8

    if peer_ev_ebitda is not None and peer_ev_ebitda > 0:
        ev_ebitda = f.ev_m / max(f.ebitda_m, 1.0)
        if ev_ebitda < peer_ev_ebitda * 0.85:
            score += 6
        elif ev_ebitda > peer_ev_ebitda * 1.25:
            score -= 5

    score = float(np.clip(score, 10.0, 95.0))
    if score >= 68:
        label = "STRONG BUY"
    elif score >= 55:
        label = "BUY"
    elif score >= 42:
        label = "HOLD"
    else:
        label = "UNDERWEIGHT"
    return label, score


def build_peer_comps_df(
    universe: dict[str, CompanyFundamentals],
    scenario: str = "Base",
    screen_mode: str = "All Companies",
) -> pd.DataFrame:
    ev_multiples = [f.ev_m / max(f.ebitda_m, 1.0) for f in universe.values()]
    peer_ev_median = float(np.median(ev_multiples)) if ev_multiples else None

    rows = []
    for tkr, f in universe.items():
        dcf = run_dcf_model(f, scenario=scenario)
        rating, score = compute_institutional_rating(f, dcf, peer_ev_ebitda=peer_ev_median)
        ev_ebitda = f.ev_m / max(f.ebitda_m, 1.0)
        pe_ratio = f.market_cap_m / max(f.ebit_m * (1.0 - f.tax_rate), 1.0)
        nd_ebitda = f.net_debt_m / max(f.ebitda_m, 1.0)
        roic_spread = f.roic_pct - dcf["wacc_pct"]

        rows.append(
            {
                "Ticker": tkr,
                "Company": f.company_name,
                "Data Basis": "9M 2026 Filing" if "9M 2026" in f.data_source else "Reference",
                "Spot (₦)": round(f.spot_price, 2),
                "Implied (₦)": round(dcf["implied_price"], 2),
                "Upside (%)": round(dcf["upside_pct"], 1),
                "EV/EBITDA": round(ev_ebitda, 1),
                "P/E": round(pe_ratio, 1),
                "Gross Margin (%)": round(f.gross_margin * 100.0, 1),
                "EBIT Margin (%)": round(f.ebit_margin * 100.0, 1),
                "ROIC (%)": round(f.roic_pct, 1),
                "ROIC-WACC (pp)": round(roic_spread, 1),
                "CCC (Days)": round(f.ccc_days, 0),
                "Net Debt/EBITDA": round(nd_ebitda, 2),
                "Rating Score": round(score, 0),
                "Rating": rating,
            }
        )

    df = pd.DataFrame(rows)
    if screen_mode == "ROIC > WACC (Value Creators)":
        df = df[df["ROIC-WACC (pp)"] > 0]
    elif screen_mode == "Fast CCC (< 95 Days)":
        df = df[df["CCC (Days)"] < 95]
    elif screen_mode == "Attractive Upside (> 10%)":
        df = df[df["Upside (%)"] > 10.0]
    elif screen_mode == "Low Leverage (< 2.0x Net Debt/EBITDA)":
        df = df[df["Net Debt/EBITDA"] < 2.0]

    return df.reset_index(drop=True)