from __future__ import annotations

import importlib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import valuation_engine
import research_brief
from research_brief import (
    PharmaQuantSnapshot,
    build_pdf_memo,
    render_dcf_brief,
    render_exec_brief,
    render_multiples_brief,
    render_risk_brief,
    render_wc_brief,
)

importlib.reload(valuation_engine)
importlib.reload(research_brief)

NGX_PHARMA_UNIVERSE = valuation_engine.NGX_PHARMA_UNIVERSE
CompanyFundamentals = valuation_engine.CompanyFundamentals
build_peer_comps_df = valuation_engine.build_peer_comps_df
build_template_csv_bytes = valuation_engine.build_template_csv_bytes
compute_institutional_rating = valuation_engine.compute_institutional_rating
load_custom_fundamentals_csv = valuation_engine.load_custom_fundamentals_csv
run_dcf_model = valuation_engine.run_dcf_model

st.set_page_config(
    page_title="NGX Healthcare & Pharma Valuation Terminal",
    page_icon="💊",
    layout="wide",
)

if "live_mode" not in st.session_state:
    st.session_state.live_mode = False
if "live_tick" not in st.session_state:
    st.session_state.live_tick = 0


def _apply_live_jitter(f: CompanyFundamentals, tick: int) -> CompanyFundamentals:
    if tick == 0:
        return f
    rng = np.random.default_rng(seed=tick + sum(ord(c) for c in f.ticker))
    pct_move = float(rng.normal(0.0, 0.006))
    new_spot = max(round(f.spot_price * (1.0 + pct_move), 2), 0.50)
    return CompanyFundamentals(
        ticker=f.ticker,
        company_name=f.company_name,
        spot_price=new_spot,
        shares_out_m=f.shares_out_m,
        revenue_m=f.revenue_m,
        gross_margin=f.gross_margin,
        ebit_margin=f.ebit_margin,
        da_m=f.da_m,
        capex_m=f.capex_m,
        cash_m=f.cash_m,
        debt_m=f.debt_m,
        book_equity_m=f.book_equity_m,
        inventory_m=f.inventory_m,
        receivables_m=f.receivables_m,
        payables_m=f.payables_m,
        tax_rate=f.tax_rate,
        wacc=f.wacc,
        terminal_g=f.terminal_g,
        rev_growth_5y=f.rev_growth_5y,
        beta=f.beta,
        daily_vol=f.daily_vol,
        max_drawdown=f.max_drawdown,
        sharpe=f.sharpe,
        data_source="Live Terminal Stream (Spot Adjusted)",
        as_of=f"Tick #{tick}",
    )


st.sidebar.title("NGX Pharma Desk")
st.sidebar.caption("Institutional Valuation, Screening & Operator Terminal")

screen_mode = st.sidebar.selectbox(
    "Institutional Screen Filter",
    [
        "All Companies",
        "ROIC > WACC (Value Creators)",
        "Fast CCC (< 95 Days)",
        "Attractive Upside (> 10%)",
        "Low Leverage (< 2.0x Net Debt/EBITDA)",
    ],
)

scenario = st.sidebar.radio(
    "Macro / Valuation Scenario",
    ["Bear", "Base", "Bull"],
    index=1,
    horizontal=True,
)

st.sidebar.markdown("---")
st.sidebar.subheader("DCF & Operator Shock Controls")
use_custom_wacc = st.sidebar.checkbox("Override WACC (%)", value=False)
wacc_override_pct = (
    st.sidebar.slider("Custom WACC (%)", min_value=14.0, max_value=38.0, value=21.5, step=0.5)
    if use_custom_wacc
    else None
)
terminal_g_override_pct = st.sidebar.slider(
    "Terminal Growth g (%)", min_value=2.0, max_value=9.0, value=6.0, step=0.5
)
fx_cogs_shock_bps = st.sidebar.slider(
    "FX / Import COGS Shock (bps)", min_value=0, max_value=1000, value=0, step=50
)
ccc_reduction_days = st.sidebar.slider(
    "Target CCC Reduction (Days)", min_value=0, max_value=45, value=10, step=5
)

st.sidebar.markdown("---")
st.sidebar.subheader("Market Feed & Custom Data")
live_toggle = st.sidebar.toggle("Live Market Terminal Mode", value=st.session_state.live_mode)
st.session_state.live_mode = live_toggle
if st.sidebar.button("Refresh Live Feed Now", use_container_width=True):
    st.session_state.live_tick += 1

with st.sidebar.expander("Custom Fundamentals CSV (Optional)"):
    uploaded_csv = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
    st.download_button(
        label="Download CSV Template",
        data=build_template_csv_bytes(),
        file_name="ngx_pharma_template.csv",
        mime="text/csv",
        use_container_width=True,
    )

base_universe = load_custom_fundamentals_csv(uploaded_csv, NGX_PHARMA_UNIVERSE)
active_universe: dict[str, CompanyFundamentals] = {
    tkr: (_apply_live_jitter(fund, st.session_state.live_tick) if st.session_state.live_mode else fund)
    for tkr, fund in base_universe.items()
}

comps_df = build_peer_comps_df(active_universe, scenario=scenario, screen_mode=screen_mode)
eligible_tickers = comps_df["Ticker"].tolist() if not comps_df.empty else list(active_universe.keys())

selected_ticker = st.selectbox(
    "Select Coverage Ticker",
    options=eligible_tickers,
    index=0,
)

f = active_universe[selected_ticker]
dcf = run_dcf_model(
    f,
    scenario=scenario,
    wacc_override_pct=wacc_override_pct,
    terminal_g_override_pct=terminal_g_override_pct,
    fx_cogs_shock_bps=fx_cogs_shock_bps,
    ccc_reduction_days=ccc_reduction_days,
)

all_ev_ebitda = [c.ev_m / max(c.ebitda_m, 1.0) for c in active_universe.values()]
all_pe = [c.market_cap_m / max(c.ebit_m * (1.0 - c.tax_rate), 1.0) for c in active_universe.values()]
peer_ev_ebitda = float(np.median(all_ev_ebitda))
peer_pe_ratio = float(np.median(all_pe))

rating, score = compute_institutional_rating(f, dcf, peer_ev_ebitda=peer_ev_ebitda)

ev_ebitda = f.ev_m / max(f.ebitda_m, 1.0)
pe_ratio = f.market_cap_m / max(f.ebit_m * (1.0 - f.tax_rate), 1.0)
nd_ebitda = f.net_debt_m / max(f.ebitda_m, 1.0)

snapshot = PharmaQuantSnapshot(
    ticker=f.ticker,
    company_name=f.company_name,
    spot_price=f.spot_price,
    implied_price=dcf["implied_price"],
    ufcf_y1=dcf["ufcf_y1"],
    ufcf_y5=dcf["ufcf_y5"],
    tv_share_pct=dcf["tv_share_pct"],
    wacc_pct=dcf["wacc_pct"],
    terminal_g_pct=dcf["terminal_g_pct"],
    dio_days=f.dio_days,
    dso_days=f.dso_days,
    dpo_days=f.dpo_days,
    ccc_days=f.ccc_days,
    ev_ebitda=ev_ebitda,
    pe_ratio=pe_ratio,
    gross_margin_pct=f.gross_margin * 100.0,
    ebit_margin_pct=f.ebit_margin * 100.0,
    peer_ev_ebitda=peer_ev_ebitda,
    peer_pe_ratio=peer_pe_ratio,
    vol_pct=f.daily_vol * 100.0,
    max_drawdown_pct=f.max_drawdown * 100.0,
    beta=f.beta,
    sharpe_ratio=f.sharpe,
    currency="₦",
    scenario=scenario,
    rating=rating,
    rating_score=score,
    roic_pct=f.roic_pct,
    net_debt_to_ebitda=nd_ebitda,
    wc_cash_unlocked_m=dcf["wc_cash_unlocked_m"],
    equity_distress_flag=dcf.get("equity_distress_flag", False),
    data_source=f.data_source,
    as_of=f.as_of,
)

st.title("NGX Healthcare & Pharma Valuation Terminal")
st.caption(
    f"Scenario: {scenario} | Screen: {screen_mode} | Source: {f.data_source} | As of: {f.as_of} | Currency: NGN (₦)"
)

render_exec_brief(snapshot)

dl1, dl2 = st.columns(2)
with dl1:
    pdf_bytes = build_pdf_memo(snapshot, schedule_df=dcf["schedule_df"])
    st.download_button(
        label=f"Download {snapshot.ticker} Tear-Sheet (.pdf)",
        data=pdf_bytes,
        file_name=f"{snapshot.ticker}_{scenario}_TearSheet.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
with dl2:
    csv_bytes = dcf["schedule_df"].to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"Download {snapshot.ticker} 5Y DCF Schedule (.csv)",
        data=csv_bytes,
        file_name=f"{snapshot.ticker}_{scenario}_5Y_DCF.csv",
        mime="text/csv",
        use_container_width=True,
    )

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "1. Intrinsic Valuation (DCF & Football Field)",
        "2. Working Capital & Cash Unlock",
        "3. Peer Comps & Screening",
        "4. Risk, Capital & Leverage",
    ]
)

with tab1:
    render_dcf_brief(snapshot)
    st.dataframe(dcf["schedule_df"], use_container_width=True, hide_index=True)

    st.markdown("#### Enterprise Value to Equity Value Bridge")
    bridge_df = pd.DataFrame(
        [
            {"Bridge Component": "PV of 5-Year UFCF (FY+1 to FY+5)", "Value": f"₦{dcf['pv_ufcf_sum_m']:,.1f}M"},
            {"Bridge Component": "PV of Terminal Value", "Value": f"₦{dcf['pv_terminal_value_m']:,.1f}M"},
            {"Bridge Component": "Plus: Working Capital Cash Unlocked", "Value": f"+₦{dcf['wc_cash_unlocked_m']:,.1f}M"},
            {"Bridge Component": "Implied Enterprise Value (EV)", "Value": f"₦{dcf['implied_ev_m']:,.1f}M"},
            {"Bridge Component": "Less: Net Debt (Debt - Cash)", "Value": f"-₦{dcf['net_debt_m']:,.1f}M"},
            {"Bridge Component": "Implied Equity Value (Unfloored)", "Value": f"₦{dcf['implied_equity_m']:,.1f}M"},
            {"Bridge Component": "Diluted Shares (Millions)", "Value": f"{f.shares_out_m:,.1f}M shares"},
            {"Bridge Component": "Implied Fair Value Per Share", "Value": f"₦{dcf['implied_price']:,.2f} vs. ₦{f.spot_price:,.2f} spot"},
        ]
    )
    st.dataframe(bridge_df, use_container_width=True, hide_index=True)

    bear_price = run_dcf_model(
        f, scenario="Bear", fx_cogs_shock_bps=fx_cogs_shock_bps, ccc_reduction_days=ccc_reduction_days
    )["implied_price"]
    base_price = run_dcf_model(
        f, scenario="Base", fx_cogs_shock_bps=fx_cogs_shock_bps, ccc_reduction_days=ccc_reduction_days
    )["implied_price"]
    bull_price = run_dcf_model(
        f, scenario="Bull", fx_cogs_shock_bps=fx_cogs_shock_bps, ccc_reduction_days=ccc_reduction_days
    )["implied_price"]

    ev_mult_implied_price = max(
        ((f.ebitda_m * peer_ev_ebitda) - f.net_debt_m + dcf["wc_cash_unlocked_m"]) / max(f.shares_out_m, 1.0),
        0.0,
    )
    pe_mult_implied_price = max(
        ((f.ebit_m * (1.0 - f.tax_rate)) * peer_pe_ratio) / max(f.shares_out_m, 1.0),
        0.0,
    )

    ff_df = pd.DataFrame(
        [
            {
                "Method": "DCF Scenario Range (Bear to Bull)",
                "Low (₦)": min(bear_price, bull_price),
                "Mid (₦)": base_price,
                "High (₦)": max(bear_price, bull_price),
            },
            {
                "Method": "Peer EV/EBITDA Comps (±15%)",
                "Low (₦)": ev_mult_implied_price * 0.85,
                "Mid (₦)": ev_mult_implied_price,
                "High (₦)": ev_mult_implied_price * 1.15,
            },
            {
                "Method": "Peer P/E Comps (±15%)",
                "Low (₦)": pe_mult_implied_price * 0.85,
                "Mid (₦)": pe_mult_implied_price,
                "High (₦)": pe_mult_implied_price * 1.15,
            },
        ]
    )

    fig_ff = go.Figure()
    for _, r in ff_df.iterrows():
        low_v = float(r["Low (₦)"])
        mid_v = float(r["Mid (₦)"])
        high_v = float(r["High (₦)"])
        fig_ff.add_trace(
            go.Bar(
                y=[r["Method"]],
                x=[max(high_v - low_v, 0.25)],
                base=[low_v],
                orientation="h",
                name=r["Method"],
                showlegend=False,
                text=[f"₦{low_v:,.1f} – ₦{high_v:,.1f}"],
                textposition="outside",
            )
        )
        fig_ff.add_trace(
            go.Scatter(
                y=[r["Method"]],
                x=[mid_v],
                mode="markers+text",
                text=[f"₦{mid_v:,.2f}"],
                textposition="top center",
                marker=dict(size=10, color="#0F172A"),
                showlegend=False,
            )
        )
    fig_ff.add_vline(
        x=f.spot_price, line_dash="dash", line_color="#DC2626", annotation_text=f"Spot ₦{f.spot_price:.2f}"
    )
    fig_ff.update_layout(
        title=f"{f.ticker} Football Field Valuation Summary (₦ / Share)",
        xaxis_title="Implied Share Price (₦)",
        height=340,
        margin=dict(l=10, r=40, t=45, b=20),
    )
    st.plotly_chart(fig_ff, use_container_width=True)

with tab2:
    render_wc_brief(snapshot)
    wc_df = pd.DataFrame(
        [
            {"Metric": "DIO (Inventory Days)", "Days": round(f.dio_days, 1), "Balance (₦M)": round(f.inventory_m, 1)},
            {"Metric": "DSO (Receivables Days)", "Days": round(f.dso_days, 1), "Balance (₦M)": round(f.receivables_m, 1)},
            {"Metric": "DPO (Payables Days)", "Days": round(f.dpo_days, 1), "Balance (₦M)": round(f.payables_m, 1)},
            {
                "Metric": "Net CCC (DIO + DSO - DPO)",
                "Days": round(f.ccc_days, 1),
                "Balance (₦M)": round(f.inventory_m + f.receivables_m - f.payables_m, 1),
            },
        ]
    )
    st.dataframe(wc_df, use_container_width=True, hide_index=True)

with tab3:
    render_multiples_brief(snapshot)
    st.dataframe(comps_df, use_container_width=True, hide_index=True)

with tab4:
    render_risk_brief(snapshot)
    risk_df = pd.DataFrame(
        [
            {"Risk / Return Metric": "Annualized Volatility", "Value": f"{f.daily_vol * 100.0:.1f}%"},
            {"Risk / Return Metric": "Max Drawdown", "Value": f"{f.max_drawdown * 100.0:.1f}%"},
            {"Risk / Return Metric": "Equity Beta", "Value": f"{f.beta:.2f}"},
            {"Risk / Return Metric": "Sharpe Ratio", "Value": f"{f.sharpe:.2f}"},
            {
                "Risk / Return Metric": "ROIC vs. WACC Spread",
                "Value": f"{f.roic_pct - dcf['wacc_pct']:+.1f} pp ({f.roic_pct:.1f}% vs {dcf['wacc_pct']:.1f}%)",
            },
            {
                "Risk / Return Metric": "Net Debt / EBITDA",
                "Value": f"{nd_ebitda:.2f}x (Net Debt: ₦{f.net_debt_m:,.1f}M)",
            },
        ]
    )
    st.dataframe(risk_df, use_container_width=True, hide_index=True)