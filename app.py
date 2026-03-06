# app.py
# SmartBill AI — Streamlit UI
# Run from project root: streamlit run app.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from simulator  import run_simulation
from prediction import train_and_evaluate, explain_prediction
from billing    import calculate_bill

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "SmartBill AI",
    page_icon  = "⚡",
    layout     = "wide",
)

# ─────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&family=DM+Mono&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

.metric-card {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 6px 0;
}
.metric-card .label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #64748b;
    margin-bottom: 6px;
}
.metric-card .value {
    font-family: 'Syne', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: #f1f5f9;
}

.bill-card {
    background: linear-gradient(135deg, #0f3460, #533483);
    border-radius: 16px;
    padding: 32px;
    text-align: center;
    color: white;
    margin: 16px 0;
}
.bill-card .amount {
    font-family: 'Syne', sans-serif;
    font-size: 3.5rem;
    font-weight: 800;
    margin: 8px 0;
}
.bill-card .subtitle { font-size: 0.9rem; opacity: 0.7; }

.alert-normal    { background: rgba(34,197,94,0.1);  border-left: 4px solid #22c55e; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; }
.alert-high      { background: rgba(239,68,68,0.1);  border-left: 4px solid #ef4444; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; }
.alert-low       { background: rgba(59,130,246,0.1); border-left: 4px solid #3b82f6; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; }

.slab-row {
    display: flex; justify-content: space-between;
    padding: 10px 14px; border-bottom: 1px solid rgba(255,255,255,0.06);
    font-size: 0.88rem;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# APPLIANCE LIST  (matches appliance_power.csv)
# ─────────────────────────────────────────────────────────────
APPLIANCES = [
    "ac", "refrigerator", "washing_machine", "geyser",
    "microwave", "television", "induction_stove",
    "water_purifier", "laptop", "fan", "lightbulb_led", "iron_box"
]


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ SmartBill AI")
    st.markdown("Hybrid ML Electricity Bill Predictor")
    st.markdown("---")

    st.markdown("### 📅 Billing Month")
    days = st.slider("Days in this month", 28, 31, 30)

    st.markdown("### 🔌 Add Appliances")
    st.caption("Add each appliance you use this month.")

    if "appliance_list" not in st.session_state:
        st.session_state.appliance_list = []

    selected_appliance = st.selectbox("Appliance", APPLIANCES)
    col1, col2 = st.columns(2)
    with col1:
        hours    = st.number_input("Hrs/day", 0.5, 24.0, 4.0, 0.5)
    with col2:
        quantity = st.number_input("Qty", 1, 20, 1)

    if st.button("➕ Add", use_container_width=True):
        st.session_state.appliance_list.append({
            "name"    : selected_appliance,
            "hours"   : hours,
            "quantity": quantity,
        })
        st.rerun()

    # Show current list
    if st.session_state.appliance_list:
        st.markdown("### 📋 My Appliances")
        to_remove = []
        for i, item in enumerate(st.session_state.appliance_list):
            c1, c2 = st.columns([4, 1])
            c1.caption(f"{item['name']} — {item['hours']}h × {item['quantity']}")
            if c2.button("✕", key=f"rm_{i}"):
                to_remove.append(i)
        for i in reversed(to_remove):
            st.session_state.appliance_list.pop(i)
        if to_remove:
            st.rerun()

        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.appliance_list = []
            st.rerun()

    st.markdown("---")
    run_btn = st.button("⚡ Run Simulation", use_container_width=True, type="primary")
    st.caption("SmartBill AI v1.0")


# ─────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🔮 Prediction & Bill",
    "🔌 Appliance Breakdown",
    "📊 ML Model Comparison",
    "🧠 SHAP Explainability",
])


# ─────────────────────────────────────────────────────────────
# RUN SIMULATION
# ─────────────────────────────────────────────────────────────
result = None

if run_btn:
    if not st.session_state.appliance_list:
        st.warning("⚠️ Please add at least one appliance in the sidebar first.")
    else:
        with st.spinner("Running SmartBill AI simulation..."):
            result = run_simulation(st.session_state.appliance_list, days)
            st.session_state["last_result"] = result

# Load last result if available
if "last_result" in st.session_state:
    result = st.session_state["last_result"]


# ════════════════════════════════════════════════════════════
# TAB 1 — PREDICTION & BILL
# ════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## 🔮 Hybrid Prediction & Bill")

    if result is None:
        st.info("👈 Add appliances in the sidebar and click **Run Simulation** to get started.")
    else:
        # ── Key metrics ───────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""<div class="metric-card">
                <div class="label">ML Predicted</div>
                <div class="value">{result['ml_predicted_kwh']} kWh</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="metric-card">
                <div class="label">Appliance Estimate</div>
                <div class="value">{result['appliance_kwh']} kWh</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="metric-card">
                <div class="label">Adjustment Factor</div>
                <div class="value">{result['adjustment_factor']}×</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="metric-card">
                <div class="label">Final Prediction</div>
                <div class="value">{result['final_kwh']} kWh</div>
            </div>""", unsafe_allow_html=True)

        # ── Usage flag alert ──────────────────────────────────
        flag = result["usage_flag"]
        if flag == "high_usage":
            st.markdown(f'<div class="alert-high">🔴 <b>High Usage Detected</b> — Your appliance usage is {result["deviation_pct"]}% above the dataset average. Consider reducing consumption.</div>', unsafe_allow_html=True)
        elif flag == "low_usage":
            st.markdown(f'<div class="alert-low">🔵 <b>Low Usage Detected</b> — Your appliance usage is {abs(result["deviation_pct"])}% below the dataset average.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-normal">🟢 <b>Normal Usage</b> — Your consumption is within expected range.</div>', unsafe_allow_html=True)

        st.markdown("---")
        col_left, col_right = st.columns(2)

        with col_left:
            # ── Bill card ─────────────────────────────────────
            st.markdown(f"""
            <div class="bill-card">
                <div class="subtitle">Estimated Electricity Bill</div>
                <div class="amount">₹{result['total_bill']}</div>
                <div class="subtitle">{result['final_kwh']} kWh · {days} days</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Bill breakdown ────────────────────────────────
            st.markdown("#### 🧮 Bill Breakdown")
            items = [
                ("Energy Charge", result["energy_charge"]),
                ("Fixed Charge",  result["fixed_charge"]),
                ("Meter Rent",    result["meter_rent"]),
            ]
            for label, amt in items:
                pct = (amt / result["total_bill"] * 100) if result["total_bill"] else 0
                st.markdown(f"**{label}** — ₹{amt} ({pct:.1f}%)")
                st.progress(pct / 100)
            st.markdown(f"**Total — ₹{result['total_bill']}**")

        with col_right:
            # ── Slab breakdown ────────────────────────────────
            st.markdown("#### 📊 Slab-Wise Breakdown")
            slab_df = pd.DataFrame(result["bill_breakdown"])
            if not slab_df.empty:
                st.dataframe(
                    slab_df.rename(columns={
                        "units": "Units (kWh)",
                        "rate" : "Rate (₹/kWh)",
                        "cost" : "Cost (₹)"
                    }).style.format({
                        "Units (kWh)": "{:.2f}",
                        "Rate (₹/kWh)": "₹{:.2f}",
                        "Cost (₹)": "₹{:.2f}",
                    }).background_gradient(subset=["Cost (₹)"], cmap="Oranges"),
                    use_container_width=True,
                    hide_index=True,
                )

            # ── Slab alert ────────────────────────────────────
            st.markdown("---")
            st.info(f"💡 {result['slab_alert']}")

            # ── Slab bar chart ────────────────────────────────
            if not slab_df.empty:
                fig, ax = plt.subplots(figsize=(5, 3))
                fig.patch.set_facecolor("#0d1117")
                ax.set_facecolor("#0d1117")
                labels  = [f"Slab {i+1}" for i in range(len(slab_df))]
                ax.bar(labels, slab_df["cost"], color="#58a6ff", edgecolor="#0d1117")
                ax.tick_params(colors="#8b949e")
                for spine in ax.spines.values():
                    spine.set_edgecolor("#30363d")
                ax.set_ylabel("₹ Cost", color="#8b949e")
                ax.set_title("Cost per Slab", color="#e6edf3", pad=10)
                st.pyplot(fig)
                plt.close(fig)


# ════════════════════════════════════════════════════════════
# TAB 2 — APPLIANCE BREAKDOWN
# ════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## 🔌 Appliance Contribution")

    if result is None:
        st.info("👈 Run a simulation first to see appliance breakdown.")
    else:
        breakdown = result["appliance_breakdown"]

        if not breakdown:
            st.warning("No valid appliances found in simulation.")
        else:
            df_app = pd.DataFrame(breakdown)
            total  = df_app["monthly_kwh"].sum()

            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown("### 📋 Per-Appliance Usage")
                df_display = df_app.copy()
                df_display["share_%"] = (df_display["monthly_kwh"] / total * 100).round(1)
                st.dataframe(
                    df_display.rename(columns={
                        "appliance"  : "Appliance",
                        "power_kw"   : "Power (kW)",
                        "hours_day"  : "Hrs/Day",
                        "quantity"   : "Qty",
                        "monthly_kwh": "Monthly kWh",
                        "share_%"    : "Share (%)",
                    }).style.format({
                        "Power (kW)"  : "{:.3f}",
                        "Hrs/Day"     : "{:.1f}",
                        "Monthly kWh" : "{:.2f}",
                        "Share (%)"   : "{:.1f}%",
                    }).background_gradient(subset=["Monthly kWh"], cmap="Blues"),
                    use_container_width=True,
                    hide_index=True,
                )
                st.metric("Total Appliance Estimate", f"{total:.2f} kWh")

            with col_right:
                st.markdown("### 📊 Contribution Chart")

                # Horizontal bar chart
                fig2, ax2 = plt.subplots(figsize=(6, max(3, len(df_app) * 0.5)))
                fig2.patch.set_facecolor("#0d1117")
                ax2.set_facecolor("#0d1117")

                colors = ["#58a6ff","#3fb950","#ffa657","#d2a8ff",
                          "#f78166","#79c0ff","#56d364","#e3b341",
                          "#ff7b72","#a5d6ff","#7ee787","#ffa198"]

                bars = ax2.barh(
                    df_app["appliance"],
                    df_app["monthly_kwh"],
                    color=colors[:len(df_app)],
                    edgecolor="#0d1117",
                )

                # Add value labels on bars
                for bar, val in zip(bars, df_app["monthly_kwh"]):
                    ax2.text(
                        bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                        f"{val:.1f}", va="center", ha="left",
                        color="#8b949e", fontsize=8
                    )

                ax2.tick_params(colors="#8b949e", labelsize=8)
                ax2.set_xlabel("kWh / month", color="#8b949e")
                ax2.set_title("Monthly kWh per Appliance", color="#e6edf3", pad=10)
                for spine in ax2.spines.values():
                    spine.set_edgecolor("#30363d")

                fig2.tight_layout()
                st.pyplot(fig2)
                plt.close(fig2)

                # Pie chart
                st.markdown("### 🥧 Share of Total Consumption")
                fig3, ax3 = plt.subplots(figsize=(5, 4))
                fig3.patch.set_facecolor("#0d1117")
                ax3.set_facecolor("#0d1117")
                wedges, texts, autotexts = ax3.pie(
                    df_app["monthly_kwh"],
                    labels=df_app["appliance"],
                    autopct="%1.1f%%",
                    colors=colors[:len(df_app)],
                    startangle=90,
                    textprops={"color": "#e6edf3", "fontsize": 8},
                )
                for at in autotexts:
                    at.set_fontsize(7)
                    at.set_color("#0d1117")
                    at.set_fontweight("bold")
                fig3.tight_layout()
                st.pyplot(fig3)
                plt.close(fig3)

        if result["skipped_appliances"]:
            st.warning(f"⚠️ Skipped (not found in database): {result['skipped_appliances']}")


# ════════════════════════════════════════════════════════════
# TAB 3 — ML MODEL COMPARISON
# ════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## 📊 ML Model Comparison")
    st.caption("Trained on UCI Household Power Consumption dataset · Chronological 80/20 split")

    with st.spinner("Training models..."):
        train_result = train_and_evaluate()

    best = train_result["best_model_name"]

    # ── Metric cards ──────────────────────────────────────────
    cols = st.columns(3)
    model_colors = {
        "RandomForest": "#3fb950",
        "XGBoost"     : "#58a6ff",
        "Ridge"       : "#d2a8ff",
    }
    for i, (name, metrics) in enumerate(train_result["results"].items()):
        flag = " ✅ Best" if name == best else ""
        with cols[i]:
            st.markdown(f"""<div class="metric-card">
                <div class="label">{name}{flag}</div>
                <div class="value">{metrics['MAE']} kWh</div>
                <div style="color:#64748b;font-size:0.8rem">RMSE: {metrics['RMSE']} kWh</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        # ── MAE comparison bar chart ──────────────────────────
        st.markdown("### MAE Comparison")
        fig4, ax4 = plt.subplots(figsize=(6, 3))
        fig4.patch.set_facecolor("#0d1117")
        ax4.set_facecolor("#0d1117")
        names  = list(train_result["results"].keys())
        maes   = [train_result["results"][n]["MAE"] for n in names]
        colors = [model_colors[n] for n in names]
        bars4  = ax4.bar(names, maes, color=colors, edgecolor="#0d1117")
        for bar, val in zip(bars4, maes):
            ax4.text(
                bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{val}", ha="center", va="bottom", color="#e6edf3", fontsize=9
            )
        ax4.tick_params(colors="#8b949e")
        ax4.set_ylabel("MAE (kWh)", color="#8b949e")
        ax4.set_title("Model MAE — Lower is Better", color="#e6edf3", pad=10)
        for spine in ax4.spines.values():
            spine.set_edgecolor("#30363d")
        st.pyplot(fig4)
        plt.close(fig4)

    with col_right:
        # ── RMSE comparison bar chart ─────────────────────────
        st.markdown("### RMSE Comparison")
        fig5, ax5 = plt.subplots(figsize=(6, 3))
        fig5.patch.set_facecolor("#0d1117")
        ax5.set_facecolor("#0d1117")
        rmses  = [train_result["results"][n]["RMSE"] for n in names]
        bars5  = ax5.bar(names, rmses, color=colors, edgecolor="#0d1117")
        for bar, val in zip(bars5, rmses):
            ax5.text(
                bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{val}", ha="center", va="bottom", color="#e6edf3", fontsize=9
            )
        ax5.tick_params(colors="#8b949e")
        ax5.set_ylabel("RMSE (kWh)", color="#8b949e")
        ax5.set_title("Model RMSE — Lower is Better", color="#e6edf3", pad=10)
        for spine in ax5.spines.values():
            spine.set_edgecolor("#30363d")
        st.pyplot(fig5)
        plt.close(fig5)

    # ── Historical consumption chart ──────────────────────────
    st.markdown("### 📈 Historical Consumption (UCI Dataset)")
    df_hist = pd.read_csv("data/processed/uci_monthly.csv")
    df_hist["month"] = pd.to_datetime(df_hist["month"])

    fig6, ax6 = plt.subplots(figsize=(12, 4))
    fig6.patch.set_facecolor("#0d1117")
    ax6.set_facecolor("#0d1117")
    ax6.plot(df_hist["month"], df_hist["energy_kwh"],
             color="#58a6ff", lw=2, label="Monthly Consumption")
    ax6.fill_between(df_hist["month"], df_hist["energy_kwh"],
                     alpha=0.15, color="#58a6ff")
    ax6.axhline(df_hist["energy_kwh"].mean(), color="#ffa657",
                lw=1.5, ls="--", label=f"Mean: {df_hist['energy_kwh'].mean():.1f} kWh")
    ax6.tick_params(colors="#8b949e", labelsize=8)
    ax6.set_ylabel("kWh", color="#8b949e")
    ax6.set_title("UCI Monthly Consumption Timeline", color="#e6edf3", pad=10)
    for spine in ax6.spines.values():
        spine.set_edgecolor("#30363d")
    ax6.legend(facecolor="#161b22", edgecolor="#30363d", labelcolor="white")
    fig6.tight_layout()
    st.pyplot(fig6)
    plt.close(fig6)


# ════════════════════════════════════════════════════════════
# TAB 4 — SHAP EXPLAINABILITY
# ════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## 🧠 SHAP Explainability (XAI)")
    st.caption("Explains why XGBoost predicted the value it did — which features pushed it up or down.")

    with st.spinner("Computing SHAP values..."):
        shap_result = explain_prediction()

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 📊 Feature Contributions")
        st.markdown(f"**Base value** (dataset avg): `{shap_result['base_value']} kWh`")
        st.markdown(f"**XGBoost predicted**: `{shap_result['predicted_kwh']} kWh`")
        st.markdown("---")

        for c in shap_result["contributions"]:
            color = "#3fb950" if c["shap_value"] > 0 else "#ef4444"
            bar_w = min(abs(c["shap_value"]) / max(
                abs(x["shap_value"]) for x in shap_result["contributions"]
            ), 1.0)
            st.markdown(
                f"**{c['label']}** &nbsp; `{c['shap_value']:+.2f} kWh` {c['direction']}"
            )
            st.progress(bar_w)

    with col_right:
        st.markdown("### 📉 SHAP Waterfall Chart")

        labels = shap_result["feature_labels"]
        values = shap_result["shap_values"]
        colors = ["#3fb950" if v > 0 else "#ef4444" for v in values]

        fig7, ax7 = plt.subplots(figsize=(7, 5))
        fig7.patch.set_facecolor("#0d1117")
        ax7.set_facecolor("#0d1117")

        bars7 = ax7.barh(labels, values, color=colors, edgecolor="#0d1117")

        # Value labels on bars
        for bar, val in zip(bars7, values):
            ax7.text(
                val + (0.5 if val >= 0 else -0.5),
                bar.get_y() + bar.get_height() / 2,
                f"{val:+.2f}", va="center",
                ha="left" if val >= 0 else "right",
                color="#e6edf3", fontsize=8
            )

        ax7.axvline(0, color="#8b949e", lw=1)
        ax7.tick_params(colors="#8b949e", labelsize=8)
        ax7.set_xlabel("SHAP Value (kWh)", color="#8b949e")
        ax7.set_title(
            f"Why XGBoost predicted {shap_result['predicted_kwh']} kWh",
            color="#e6edf3", pad=10
        )
        for spine in ax7.spines.values():
            spine.set_edgecolor("#30363d")

        # Legend
        pos_patch = mpatches.Patch(color="#3fb950", label="Pushes prediction UP ↑")
        neg_patch = mpatches.Patch(color="#ef4444", label="Pushes prediction DOWN ↓")
        ax7.legend(
            handles=[pos_patch, neg_patch],
            facecolor="#161b22", edgecolor="#30363d", labelcolor="white",
            fontsize=8
        )

        fig7.tight_layout()
        st.pyplot(fig7)
        plt.close(fig7)

        st.markdown("---")
        st.info(
            f"📌 The model starts from a base of **{shap_result['base_value']} kWh** "
            f"(dataset average) and each feature adjusts it up or down to reach "
            f"the final prediction of **{shap_result['predicted_kwh']} kWh**."
        )