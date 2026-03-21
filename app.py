# app.py — WattsInBill frontend and simulation connector
# Run from project root: streamlit run app.py

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import plotly.graph_objects as go

from simulator  import run_simulation
from prediction import train_and_evaluate, explain_prediction
from auth       import require_login, logout
from database   import (
    init_db,
    save_simulation,
    get_simulation_history,
    delete_simulation,
    get_simulation_stats,
)

st.set_page_config(page_title="WattsInBill", page_icon="⚡", layout="wide")

# ── Database init + Auth gate ─────────────────────────────────
init_db()        # creates DB, tables, seeds data (safe every startup)
require_login()  # shows login page if not authenticated; st.stop() if not

# ── Session state shortcuts ───────────────────────────────────
uid   = st.session_state.get("user_id")
uname = st.session_state.get("username", "")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Archivo+Black&display=swap');

:root {{
    --bg:       #0b0d11;
    --panel:    #12151c;
    --panel2:   #161b24;
    --border:   rgba(255,255,255,0.06);
    --border2:  rgba(255,255,255,0.10);
    --gold:     #D4A900;
    --gold-dim: #a07e18;
    --steel:    #5B8DB8;
    --blue:     #A8B0BE;
    --text-lt:  #e8edf5;
    --text-mid: #8a8f9e;
    --text-dim: #4a4f5e;
    --green:    #3db87a;
    --red:      #e05555;
    --grid:     #1a1e28;
}}

html, body, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    background-color: var(--bg);
    color: #c8cdd8;
}}

[data-testid="stMain"]::after {{
    content: '';
    position: absolute;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    background-size: 200px 200px;
    pointer-events: none;
    z-index: 9999;
    opacity: 0.45;
    animation: grain 2s steps(2) infinite;
}}
@keyframes grain {{
    0%   {{ transform: translate(0,0); }}
    25%  {{ transform: translate(-2px,1px); }}
    50%  {{ transform: translate(1px,-2px); }}
    75%  {{ transform: translate(2px,1px); }}
    100% {{ transform: translate(-1px,2px); }}
}}

[data-testid="stSidebar"] {{
    background: linear-gradient(180deg,#0c0f14 0%,#0a0c10 100%);
    border-right: 1px solid rgba(212,169,0,0.12);
    z-index: 10;
    position: relative;
}}

[data-testid="stAppViewContainer"] {{ background-color: var(--bg); }}

[data-testid="stMain"] {{
    background: linear-gradient(rgba(11,13,17,0.82), rgba(11,13,17,0.82)), url("app/static/bg.jpg");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    position: relative;
}}

[data-testid="stMain"] > * {{ position: relative; z-index: 1; }}
[data-testid="stAppViewContainer"] > * {{ position: relative; z-index: 1; }}

h1,h2,h3 {{
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    color: var(--text-lt) !important;
}}
h1 {{ font-size: 2.8rem !important; }}
h2 {{ font-size: 2.3rem !important; }}
h3 {{ font-size: 1.65rem !important; }}

.num-val, .metric-card .value, .bill-card .amount,
.hero-banner .hero-kwh, .hero-badge .badge-val {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em;
}}

hr {{
    border: none !important; height: 1px !important;
    background: linear-gradient(90deg,transparent,var(--gold),transparent) !important;
    opacity: 0.35 !important; margin: 1.5rem 0 !important;
}}

.sidebar-logo {{ text-align:center; padding:10px 0 6px; }}
.sidebar-logo .logo-row {{ display:flex; align-items:center; justify-content:center; gap:10px; margin-bottom:4px; }}
.sidebar-logo .icon {{
    display:inline-block; font-size:2rem;
    filter: drop-shadow(0 0 12px rgba(212,169,0,0.8)) drop-shadow(0 0 24px rgba(212,169,0,0.4));
    animation: pulse-glow 2.5s ease-in-out infinite; line-height:1;
}}
.sidebar-logo .title {{
    font-family:'Syne',sans-serif; font-size:1.5rem; font-weight:800;
    background:linear-gradient(135deg,#D4A900,#f5d060,#D4A900);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    letter-spacing:-0.02em; line-height:1;
}}
.sidebar-logo .sub {{
    font-size:0.68rem; color:var(--text-dim); letter-spacing:0.12em;
    text-transform:uppercase; margin-top:2px;
}}
@keyframes pulse-glow {{
    0%,100% {{ filter: drop-shadow(0 0 10px rgba(212,169,0,0.7)) drop-shadow(0 0 20px rgba(212,169,0,0.3)); }}
    50%      {{ filter: drop-shadow(0 0 18px rgba(212,169,0,1.0)) drop-shadow(0 0 35px rgba(212,169,0,0.5)); }}
}}

[data-testid="stSidebar"] .add-appliance-btn > button,
[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
    background:linear-gradient(135deg,#b08a00 0%,#D4A900 40%,#f5d060 60%,#D4A900 80%,#b08a00 100%) !important;
    background-size:300% 100% !important; color:#0b0d11 !important;
    border:none !important; border-radius:10px !important;
    font-family:'Syne',sans-serif !important; font-weight:700 !important;
    font-size:0.9rem !important; padding:10px 0 !important;
    position:relative; overflow:hidden;
    transition:background-position 0.4s ease,box-shadow 0.3s ease !important;
}}
[data-testid="stSidebar"] .add-appliance-btn > button:hover,
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {{
    background-position:100% 0 !important;
    box-shadow:0 0 24px rgba(212,169,0,0.35),0 0 48px rgba(212,169,0,0.12) !important;
    transform:translateY(-1px);
}}
[data-testid="stSidebar"] .add-appliance-btn > button::before,
[data-testid="stSidebar"] .stButton > button[kind="primary"]::before {{
    content:''; position:absolute; top:0; left:-100%; width:60%; height:100%;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,0.3),transparent);
    transform:skewX(-20deg); animation:shimmer 2.5s ease-in-out infinite;
}}
@keyframes shimmer {{ 0% {{ left:-100%; }} 60% {{ left:130%; }} 100% {{ left:130%; }} }}

[data-testid="stSidebar"] .stButton > button[kind="secondary"] {{
    background:transparent !important; background-image:none !important;
    border:1.5px solid rgba(212,169,0,0.45) !important;
    border-radius:10px !important; color:var(--gold) !important;
    font-family:'Syne',sans-serif !important; font-weight:600 !important;
    font-size:0.88rem !important; padding:8px 0 !important;
    box-shadow:none !important; transition:all 0.25s ease !important;
}}
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {{
    background:rgba(212,169,0,0.08) !important; border-color:var(--gold) !important;
}}
[data-testid="stSidebar"] .stButton > button[kind="secondary"]::before {{ display:none !important; }}

[data-testid="stTabs"] [role="tablist"] {{
    border-bottom:1px solid var(--grid); margin-bottom:0; gap:2px; background:transparent;
}}
[data-testid="stTabs"] > div:first-child {{ border-bottom: none !important; margin-bottom: 0 !important; }}
[data-testid="stTabs"] > div:nth-child(2) {{ border-top: none !important; }}
[data-testid="stTabContent"] {{ padding-top: 1.4rem; border-top: none !important; }}
.stTabs [data-baseweb="tab-panel"] {{ border-top: none !important; padding-top: 1.2rem !important; }}
[data-testid="stTabs"] [role="tab"] {{
    color:var(--text-dim) !important; font-family:'Syne',sans-serif !important;
    font-weight:700 !important; font-size:1.0rem !important;
    padding:11px 22px !important; border-radius:8px 8px 0 0 !important;
    border-bottom:2px solid transparent !important; margin-bottom:-1px;
    transition:all 0.2s ease; background:transparent !important;
}}
[data-testid="stTabs"] [role="tab"]:hover {{ color:var(--text-mid) !important; background:rgba(212,169,0,0.04) !important; }}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color:var(--gold) !important; border-bottom:2px solid var(--gold) !important;
    background:rgba(212,169,0,0.07) !important; box-shadow:0 2px 20px rgba(212,169,0,0.08);
}}

.metric-card {{
    display:flex; flex-direction:column; justify-content:flex-end;
    background:rgba(18,21,28,0.85); backdrop-filter:blur(16px);
    border:1px solid var(--border); border-top:2px solid var(--blue);
    border-radius:12px; padding:22px 20px 20px; margin:6px 0;
    transition:box-shadow 0.3s ease,transform 0.2s ease;
}}
.metric-card:hover {{ transform:translateY(-2px); box-shadow:0 8px 32px rgba(0,0,0,0.3); }}
.metric-card.gold-card {{
    border-top:2px solid var(--gold);
    box-shadow:0 0 30px rgba(212,169,0,0.10),0 0 60px rgba(212,169,0,0.04);
}}
.metric-card.gold-card:hover {{ box-shadow:0 0 40px rgba(212,169,0,0.18),0 8px 32px rgba(0,0,0,0.3); }}
.metric-card.blue-card {{ border-top:2px solid var(--blue); }}
.metric-card .label {{
    font-size:0.68rem; font-weight:600; text-transform:uppercase;
    letter-spacing:0.12em; color:var(--text-dim); margin-bottom:10px;
    font-family:'Plus Jakarta Sans',sans-serif;
}}
.metric-card .value {{
    font-family:'Archivo Black',sans-serif !important; font-size:1.9rem; font-weight:400;
    color:var(--text-lt); letter-spacing:-0.02em; line-height:1;
}}
.metric-card.gold-card .value {{
    background:linear-gradient(135deg,#D4A900,#f5d060);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}}
.metric-card .trend {{ font-size:0.72rem; color:var(--text-dim); margin-top:8px; }}

.bill-card {{
    background: linear-gradient(160deg, #1a1500 0%, #0f1218 60%);
    backdrop-filter: blur(20px); border-radius: 16px;
    padding: 32px 32px 28px; text-align: center; margin: 14px 0 14px;
    position: relative; overflow: hidden;
    border: 1px solid rgba(212,169,0,0.30);
    box-shadow: 0 0 0 1px rgba(212,169,0,0.08), 0 20px 60px rgba(0,0,0,0.4);
}}
.bill-card::before {{
    content:''; position:absolute; top:50%; left:50%;
    transform:translate(-50%,-55%); width:260px; height:120px;
    background:radial-gradient(ellipse,rgba(212,169,0,0.18) 0%,transparent 70%);
    pointer-events:none; animation:bill-breathe 3s ease-in-out infinite;
}}
@keyframes bill-breathe {{
    0%,100% {{ opacity:0.8; transform:translate(-50%,-55%) scale(1); }}
    50%      {{ opacity:1.0; transform:translate(-50%,-55%) scale(1.12); }}
}}
.bill-card .bill-label {{
    font-size:0.68rem; font-weight:600; text-transform:uppercase;
    letter-spacing:0.14em; color:var(--text-dim); margin-bottom:8px;
    font-family:'Plus Jakarta Sans',sans-serif;
}}
.bill-card .amount {{
    font-family:'Archivo Black',sans-serif !important; font-size:3.6rem; font-weight:400;
    background:linear-gradient(135deg,#c49800 0%,#D4A900 35%,#f5d060 60%,#D4A900 80%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    letter-spacing:-0.02em; line-height:1.05; margin:6px 0 10px;
    background-size:200% 100%; animation:gold-flow 4s ease-in-out infinite;
}}
@keyframes gold-flow {{ 0%,100% {{ background-position:0% 50%; }} 50% {{ background-position:100% 50%; }} }}
.bill-card .subtitle {{ font-size:0.85rem; color:var(--text-dim); letter-spacing:0.02em; }}

.alert-normal,.alert-high,.alert-low {{
    backdrop-filter:blur(8px); padding:12px 18px;
    border-radius:0 10px 10px 0; margin:4px 0 26px;
    font-size:0.875rem; color:var(--text-mid); animation:slide-in 0.4s ease;
}}
.alert-normal {{ background:linear-gradient(90deg,rgba(61,184,122,0.12) 0%,rgba(61,184,122,0.02) 100%); border-left:3px solid #3db87a; color:#7dfa5a; }}
.alert-high   {{ background:linear-gradient(90deg,rgba(229,57,53,0.10) 0%,rgba(229,57,53,0.02) 100%); border-left:3px solid #E53935; color:#ff6b6b; }}
.alert-low    {{ background:linear-gradient(90deg,rgba(61,184,122,0.12) 0%,rgba(61,184,122,0.02) 100%); border-left:3px solid #3db87a; color:#7dfa5a; }}
@keyframes slide-in {{ from {{ opacity:0; transform:translateX(-10px); }} to {{ opacity:1; transform:translateX(0); }} }}

.hero-banner {{
    background:linear-gradient(135deg,rgba(18,21,28,0.95) 0%,rgba(22,26,36,0.90) 60%,rgba(18,21,28,0.95) 100%);
    border:1px solid rgba(212,169,0,0.15); border-radius:16px;
    padding:24px 32px; margin-bottom:20px;
    display:flex; align-items:center; justify-content:space-between;
    flex-wrap:wrap; gap:16px; position:relative; overflow:hidden;
}}
.hero-banner::before {{
    content:''; position:absolute; top:0; right:0; width:300px; height:100%;
    background:radial-gradient(ellipse at right center,rgba(212,169,0,0.08) 0%,transparent 60%);
    pointer-events:none;
}}
.hero-banner .hero-label {{
    font-size:0.7rem; text-transform:uppercase; letter-spacing:0.14em;
    color:var(--gold); font-weight:600; margin-bottom:4px; font-family:'Plus Jakarta Sans',sans-serif;
}}
.hero-banner .hero-kwh {{
    font-family:'Archivo Black',sans-serif !important; font-size:2.6rem; font-weight:400;
    color:var(--text-lt); letter-spacing:-0.03em; line-height:1;
}}
.hero-banner .hero-sub {{ font-size:0.85rem; color:var(--text-dim); margin-top:4px; }}
.hero-badges {{ display:flex; flex-wrap:wrap; gap:12px; }}
.hero-badge {{
    background:rgba(212,169,0,0.10); border:1px solid rgba(212,169,0,0.25);
    border-radius:10px; padding:12px 20px; text-align:center; min-width:110px;
}}
.hero-badge .badge-label {{
    font-size:0.65rem; text-transform:uppercase; letter-spacing:0.1em;
    color:var(--text-dim); margin-bottom:4px; font-family:'Plus Jakarta Sans',sans-serif;
}}
.hero-badge .badge-val {{
    font-family:'Archivo Black',sans-serif !important; font-size:1.3rem; font-weight:400; color:var(--gold);
}}

.stProgress > div > div {{
    background:linear-gradient(90deg,var(--gold-dim),var(--gold)) !important;
    border-radius:4px !important; box-shadow:0 0 8px rgba(212,169,0,0.3) !important;
}}

div[data-testid="stDataFrame"] {{ border:none !important; border-radius:8px !important; overflow:hidden; }}
div[data-testid="stDataFrame"] table {{ border-collapse: collapse !important; border: none !important; }}
div[data-testid="stDataFrame"] th {{
    background: rgba(18,21,28,0.95) !important;
    border-bottom: 1px solid rgba(212,169,0,0.2) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
    color: var(--text-mid) !important; font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.75rem !important; letter-spacing: 0.08em !important;
    text-transform: uppercase !important; padding: 8px 12px !important;
}}
div[data-testid="stDataFrame"] td {{
    border-bottom: 1px solid rgba(255,255,255,0.05) !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important; padding: 7px 12px !important;
}}

[data-testid="stAlert"] {{
    background:rgba(18,21,28,0.8) !important; border-radius:10px !important;
    border:1px solid var(--border2) !important; backdrop-filter:blur(8px) !important;
}}

[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input {{
    background:rgba(18,21,28,0.9) !important; border:1px solid var(--border2) !important;
    border-radius:8px !important; color:var(--text-lt) !important;
    font-family:'Plus Jakarta Sans',sans-serif !important;
}}

[data-testid="stMetricValue"] {{ font-family:'Archivo Black',sans-serif !important; color:var(--text-lt) !important; }}

::-webkit-scrollbar {{ width:5px; }}
::-webkit-scrollbar-track {{ background:var(--bg); }}
::-webkit-scrollbar-thumb {{ background:var(--grid); border-radius:3px; }}
::-webkit-scrollbar-thumb:hover {{ background:var(--text-dim); }}
</style>
""", unsafe_allow_html=True)

# Chart color palette — shared across all matplotlib and plotly figures
BG      = "#0b0d11"
PANEL   = "#12151c"
GRID_C  = "#1a1e28"
TEXT_DIM= "#4a4f5e"
TEXT_MID= "#8a8f9e"
TEXT_LT = "#e8edf5"
GOLD    = "#D4A900"
GOLD_DIM= "#a07e18"
BLUE    = "#A8B0BE"
STEEL   = "#5B8DB8"

PIE_COLORS = [
    "#D4A900","#E53935","#5B8DB8","#3db87a",
    "#e07b55","#8b78e6","#e0c055","#8a9ab0",
    "#64d9a8","#7b9ee0","#A8B0BE","#55c9a8"
]
MODEL_COLORS = {"RandomForest":BLUE,"XGBoost":GOLD,"Ridge":"#8b78e6"}


def make_fig(w=6, h=3.8, grid_axis="y"):
    """Returns a styled matplotlib figure and axes with transparent dark background."""
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor((0,0,0,0)); ax.set_facecolor((0.07,0.08,0.11,0.45))
    ax.grid(axis=grid_axis, color=GRID_C, linewidth=0.8, linestyle="-")
    ax.set_axisbelow(True); ax.tick_params(colors=TEXT_DIM, labelsize=8)
    for sp in ax.spines.values(): sp.set_edgecolor(GRID_C); sp.set_linewidth(0.8)
    return fig, ax

def add_bar_glow(bars, color):
    """Applies a soft glow stroke effect to bar chart elements."""
    for bar in bars:
        bar.set_path_effects([pe.Stroke(linewidth=6, foreground=color, alpha=0.18), pe.Normal()])


APPLIANCES = [
    "ac","refrigerator","washing_machine","geyser","microwave","television",
    "induction_stove","water_purifier","laptop","fan","lightbulb_led","iron_box"
]
APPLIANCE_ICONS = {
    "ac":"❄️","refrigerator":"🧊","washing_machine":"🌀","geyser":"🔥",
    "microwave":"🔌","television":"📺","induction_stove":"🍳",
    "water_purifier":"💧","laptop":"💻","fan":"🌬️","lightbulb_led":"💡","iron_box":"👕"
}

# Cached to avoid retraining on every Streamlit rerun
@st.cache_data(show_spinner=False)
def cached_train_and_evaluate(): return train_and_evaluate()

@st.cache_data(show_spinner=False)
def cached_explain_prediction(): return explain_prediction()

if "appliance_list" not in st.session_state:
    st.session_state.appliance_list = []

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="logo-row">
            <div class="icon">⚡</div>
            <div class="title">WattsInBill</div>
        </div>
        <div class="sub">ML Electricity Predictor</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # ── User info + logout ────────────────────────────────
    if uname:
        label = "👤 Guest" if uname == "guest" else f"👤 {uname.title()}"
        st.markdown(
            f"<div style='text-align:center;font-size:0.78rem;"
            f"color:var(--text-mid);margin-bottom:8px;font-family:Plus Jakarta Sans,sans-serif'>"
            f"{label}</div>",
            unsafe_allow_html=True
        )
        if st.button("🚪 Logout", use_container_width=True, key="logout_btn", type="secondary"):
            logout()
        st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("### 📅 Billing Month")
    days = st.slider("Days in this month", 28, 31, 30, key="days_slider")
    st.markdown("### 🔌 Add Appliances")
    st.caption("Select an appliance and configure usage.")

    selected_appliance = st.selectbox(
        "Appliance", APPLIANCES,
        format_func=lambda x: f"{APPLIANCE_ICONS.get(x,'🔌')} {x.replace('_',' ').title()}")
    c1, c2 = st.columns(2)
    with c1: hours    = st.number_input("Hrs/day", 0.1, 24.0, 4.0, 0.1)
    with c2: quantity = st.number_input("Qty", 1, 20, 1)

    st.markdown('<div class="add-appliance-btn">', unsafe_allow_html=True)
    add_clicked = st.button("➕ Add Appliance", use_container_width=True, type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    if add_clicked:
        if hours <= 0 or quantity <= 0:
            st.error("⚠️ Hours and quantity must be greater than 0")
        else:
            st.session_state.appliance_list.append(
                {"name": selected_appliance, "hours": hours, "quantity": quantity})
            st.rerun()

    if st.session_state.appliance_list:
        st.markdown("### 📋 My Appliances")
        to_delete = None
        for idx, item in enumerate(st.session_state.appliance_list):
            icon  = APPLIANCE_ICONS.get(item["name"], "🔌")
            label = item["name"].replace("_", " ").title()
            ca, cb = st.columns([5, 1])
            ca.markdown(
                f'<div style="background:rgba(212,169,0,0.08);border:1px solid rgba(212,169,0,0.2);'
                f'border-radius:20px;padding:5px 12px;font-size:0.78rem;color:var(--text-mid);margin:3px 0">'
                f'{icon} {label} · {item["hours"]}h×{item["quantity"]}</div>',
                unsafe_allow_html=True)
            if cb.button("×", key=f"del_{idx}", help="Remove"): to_delete = idx
        if to_delete is not None:
            st.session_state.appliance_list.pop(to_delete); st.rerun()

        clear_clicked = st.button("🗑️ Clear All", use_container_width=True, key="clear_all", type="secondary")
        if clear_clicked:
            st.session_state.appliance_list = []; st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    run_btn = st.button("⚡ Run Simulation", use_container_width=True, type="primary")
    st.caption("WattsInBill v2.2")

# ── Tabs ─────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔮 Prediction & Bill",
    f"🔌 Appliance Breakdown ({len(st.session_state.appliance_list)})" if st.session_state.appliance_list else "🔌 Appliance Breakdown",
    "📊 ML Model Comparison",
    "🧠 SHAP Explainability",
    "📋 History",
])

result = None
if run_btn:
    if not st.session_state.appliance_list:
        st.warning("⚠️ Please add at least one appliance first.")
    else:
        with st.spinner("Running simulation..."):
            result = run_simulation(st.session_state.appliance_list, days)
            st.session_state["last_result"] = result

        # Auto-save to MySQL for logged-in users (not guests)
        if uid:
            try:
                save_simulation(uid, result, days)
                st.toast("✅ Simulation saved to history!", icon="💾")
            except Exception as e:
                st.toast(f"⚠️ Could not save simulation: {e}", icon="⚠️")

# Persist last simulation result across reruns
if "last_result" in st.session_state:
    result = st.session_state["last_result"]

# ── Tab 1 — Prediction & Bill ────────────────────────────────
with tab1:
    st.markdown("## Prediction & Bill")
    if result is None:
        st.info("👈 Add appliances in the sidebar and click **Run Simulation**.")
    else:
        flag_label = {
            "high_usage": f"<span style='color:#e05555'>&#9679;</span> High Usage · {result['deviation_pct']}% above average",
            "low_usage" : f"<span style='color:#3db87a'>&#9679;</span> Low Usage · {abs(result['deviation_pct'])}% below average",
            "normal"    : "<span style='color:#A8B0BE'>&#9679;</span> Normal Usage · Within expected range",
        }.get(result["usage_flag"], "")

        st.markdown(f"""
        <div class="hero-banner">
            <div>
                <div class="hero-label">Final Predicted Consumption</div>
                <div class="hero-kwh">{result['final_kwh']} <span style="font-size:1.3rem;color:var(--text-dim)">kWh</span></div>
                <div class="hero-sub">{flag_label}</div>
            </div>
            <div class="hero-badges">
                <div class="hero-badge"><div class="badge-label">Appliance Est.</div><div class="badge-val">{result['appliance_kwh']}</div></div>
                <div class="hero-badge"><div class="badge-label">Adjustment</div><div class="badge-val">{result['adjustment_factor']}×</div></div>
                <div class="hero-badge"><div class="badge-label">ML Estimate</div><div class="badge-val">{result['ml_predicted_kwh']}</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        flag = result["usage_flag"]
        if flag == "high_usage":
            st.markdown(f'<div class="alert-high"><span style="color:#e05555">&#9679;</span> <b>High Usage Detected</b> — {result["deviation_pct"]}% above average. Consider reducing consumption.</div>', unsafe_allow_html=True)
        elif flag == "low_usage":
            st.markdown(f'<div class="alert-low"><span style="color:#3db87a">&#9679;</span> <b>Low Usage</b> — {abs(result["deviation_pct"])}% below average.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-normal"><span style="color:#A8B0BE">&#9679;</span> <b>Normal Usage</b> — Within expected range.</div>', unsafe_allow_html=True)

        st.markdown("<hr style='margin:10px 0 8px !important;'>", unsafe_allow_html=True)
        col_left, col_right = st.columns([3, 2], gap="large")

        with col_left:
            st.markdown(f"""
            <div class="bill-card">
                <div class="bill-label">Estimated Electricity Bill</div>
                <div class="amount">₹{result['total_bill']}</div>
                <div class="subtitle">{result['final_kwh']} kWh &nbsp;·&nbsp; {days} days</div>
                <div class="subtitle" style="margin-top:4px;font-size:0.78rem;opacity:0.6">Tiered tariff slab billing</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### Bill Breakdown")
            charges = [
                ("Energy Charge", result["energy_charge"]),
                ("Fixed Charge",  result["fixed_charge"]),
                ("Meter Rent",    result["meter_rent"]),
            ]
            for lbl, amt in charges:
                pct = (amt / result["total_bill"] * 100) if result["total_bill"] else 0
                ca, cb = st.columns([3, 1])
                ca.markdown(f"<span style='color:var(--text-mid);font-size:0.85rem'>{lbl}</span>", unsafe_allow_html=True)
                cb.markdown(f"<span style='color:var(--gold);font-family:Plus Jakarta Sans,sans-serif;font-weight:500'>₹{amt}</span>", unsafe_allow_html=True)
                st.progress(pct / 100)

            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;align-items:center;
                        border-top:1px solid rgba(212,169,0,0.2);padding-top:12px;margin-top:8px'>
                <span style='font-family:Syne,sans-serif;font-weight:700;color:var(--text-lt)'>Total</span>
                <span style='font-family:Plus Jakarta Sans,sans-serif;font-size:1.5rem;font-weight:500;color:var(--gold)'>₹{result['total_bill']}</span>
            </div>
            """, unsafe_allow_html=True)

        with col_right:
            st.markdown("#### Slab-Wise Breakdown")
            slab_df = pd.DataFrame(result["bill_breakdown"])
            if not slab_df.empty:
                max_cost = slab_df["cost"].max()
                def _slab_style(row):
                    cost_val = row["cost"] if "cost" in row.index else row.iloc[-1]
                    pct = (cost_val / max_cost) if max_cost else 0
                    # Gold tone scale — bg gets richer, text stays readable
                    if pct < 0.25:   bg="rgba(212,169,0,0.06)";  color="#8a7020"
                    elif pct < 0.50: bg="rgba(212,169,0,0.13)";  color="#b08a00"
                    elif pct < 0.75: bg="rgba(212,169,0,0.22)";  color="#c49800"
                    else:            bg="rgba(212,169,0,0.32)";   color="#7a5c00"
                    return [f"background-color:{bg};color:{color};font-weight:600;border-bottom:1px solid rgba(212,169,0,0.10);border-right:1px solid rgba(212,169,0,0.08);" for _ in row]

                st.dataframe(
                    slab_df.rename(columns={"units":"Units (kWh)","rate":"Rate (₹/kWh)","cost":"Cost (₹)"})
                    .style.format({"Units (kWh)":"{:.2f}","Rate (₹/kWh)":"₹{:.2f}","Cost (₹)":"₹{:.2f}"})
                    .apply(_slab_style, axis=1),
                    use_container_width=True, hide_index=True)

            st.info(f"⚠️ {result['slab_alert']}")

            with st.spinner("Rendering slab chart..."):
                if not slab_df.empty:
                    fig, ax = make_fig(w=7.0, h=4.4)
                    bar_colors = [GOLD if i%2==0 else BLUE for i in range(len(slab_df))]
                    bars = ax.bar([f"Slab {i+1}" for i in range(len(slab_df))],
                                  slab_df["cost"], color=bar_colors, edgecolor=PANEL, linewidth=0.8, width=0.5)
                    add_bar_glow(bars, GOLD)
                    for bar, val in zip(bars, slab_df["cost"]):
                        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(slab_df["cost"])*0.025,
                                f"₹{val:.0f}", ha="center", va="bottom", color=TEXT_LT, fontsize=8.5, fontweight="600")
                    ax.set_ylabel("Cost (₹)", color=TEXT_DIM, fontsize=9)
                    ax.set_xlabel("Slab Tier", color=TEXT_DIM, fontsize=9)
                    ax.set_title("Cost per Slab", color=TEXT_LT, pad=12, fontsize=10, fontweight="600")
                    fig.tight_layout(pad=1.8); st.pyplot(fig); plt.close(fig)

# ── Tab 2 — Appliance Breakdown ──────────────────────────────
with tab2:
    st.markdown("## Appliance Contribution")
    if result is None:
        st.info("👈 Run a simulation first.")
    else:
        breakdown = result["appliance_breakdown"]
        if not breakdown:
            st.warning("No valid appliances found.")
        else:
            df_app = pd.DataFrame(breakdown)
            total  = df_app["monthly_kwh"].sum()
            col_left, col_right = st.columns([3, 2], gap="large")

            with col_left:
                st.markdown("### Per-Appliance Usage")
                rate_per_kwh = result["total_bill"] / result["final_kwh"] if result["final_kwh"] else 0
                df_display = df_app.copy()
                df_display["share_%"]    = (df_display["monthly_kwh"] / total * 100).round(1)
                df_display["est_cost_₹"] = (df_display["monthly_kwh"] * rate_per_kwh).round(2)
                df_renamed = df_display.rename(columns={
                    "appliance":"Appliance","power_kw":"Power (kW)","hours_day":"Hrs/Day","quantity":"Qty",
                    "monthly_kwh":"Monthly kWh","share_%":"Share (%)","est_cost_₹":"Est. Cost (₹)"
                })
                kwh_max = df_renamed["Monthly kWh"].max()

                def _app_row_style(row):
                    styles = []
                    for col in row.index:
                        base = "border-bottom:1px solid rgba(255,255,255,0.05);border-right:1px solid rgba(255,255,255,0.04);"
                        if col == "Monthly kWh":
                            pct   = row[col] / kwh_max if kwh_max else 0
                            alpha = round(0.08 + pct * 0.30, 2)
                            styles.append(f"background-color:rgba(212,169,0,{alpha});color:#3a2500;font-weight:700;{base}")
                        else:
                            styles.append(f"background-color:#0f1218;color:#c8cdd8;{base}")
                    return styles

                st.dataframe(
                    df_renamed.style.format({
                        "Power (kW)":"{:.3f}","Hrs/Day":"{:.1f}",
                        "Monthly kWh":"{:.2f}","Share (%)":"{:.1f}%","Est. Cost (₹)":"₹{:.2f}"
                    }).apply(_app_row_style, axis=1),
                    use_container_width=True, hide_index=True)

                st.markdown(f"""
                <div class="metric-card gold-card" style="margin-top:12px">
                    <div class="label">Total Appliance Estimate</div>
                    <div class="value">{total:.2f} kWh</div>
                    <div class="trend">sum of all appliances · ₹{total*rate_per_kwh:.2f} est.</div>
                </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### Monthly kWh per Appliance")
                with st.spinner("Rendering chart..."):
                    fig2, ax2 = make_fig(w=6, h=max(3.2, len(df_app)*0.55), grid_axis="x")
                    bar_colors2 = [STEEL if i%2==0 else "#3db87a" for i in range(len(df_app))]
                    bars2 = ax2.barh(df_app["appliance"], df_app["monthly_kwh"],
                                     color=bar_colors2, edgecolor=PANEL, linewidth=0.8, height=0.55)
                    add_bar_glow(bars2, GOLD)
                    for bar, val in zip(bars2, df_app["monthly_kwh"]):
                        ax2.text(bar.get_width()+df_app["monthly_kwh"].max()*0.025,
                                 bar.get_y()+bar.get_height()/2,
                                 f"{val:.1f}", va="center", ha="left", color=TEXT_MID, fontsize=8)
                    max_idx = df_app["monthly_kwh"].idxmax()
                    ax2.annotate("🔺 Highest",
                        xy=(df_app["monthly_kwh"].iloc[max_idx], max_idx),
                        xytext=(df_app["monthly_kwh"].max()*0.6, max_idx-0.4),
                        fontsize=7.5, color=GOLD, arrowprops=dict(arrowstyle="->", color=GOLD, lw=0.8))
                    ax2.set_xlabel("kWh / month", color=TEXT_DIM, fontsize=9)
                    ax2.set_ylabel("Appliance", color=TEXT_DIM, fontsize=9)
                    ax2.set_title("Appliance Consumption", color=TEXT_LT, pad=12, fontsize=10, fontweight="600")
                    fig2.tight_layout(pad=1.8); st.pyplot(fig2); plt.close(fig2)

            with col_right:
                st.markdown("### Share of Total Consumption")
                with st.spinner("Rendering donut..."):
                    donut_fig = go.Figure(go.Pie(
                        labels=df_app["appliance"], values=df_app["monthly_kwh"], hole=0.60,
                        marker=dict(colors=PIE_COLORS[:len(df_app)], line=dict(color="rgba(0,0,0,0)", width=0)),
                        textinfo="label+percent",
                        hovertemplate="<b>%{label}</b><br>%{value:.2f} kWh<br>%{percent}<extra></extra>",
                        direction="clockwise", sort=True,
                    ))
                    donut_fig.add_annotation(
                        text=f"<b>{total:.0f}</b><br><span style='font-size:11px'>kWh/mo</span>",
                        x=0.5, y=0.5, showarrow=False,
                        font=dict(size=18, color=GOLD, family="Plus Jakarta Sans"), align="center")
                    donut_fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False,
                        margin=dict(t=30,b=10,l=10,r=10), height=420,
                        font=dict(color=TEXT_MID, family="Plus Jakarta Sans"))
                    st.plotly_chart(donut_fig, use_container_width=True)

        if result["skipped_appliances"]:
            st.warning(f"⚠️ Skipped: {result['skipped_appliances']}")

# ── Tab 3 — ML Model Comparison ──────────────────────────────
with tab3:
    st.markdown("## ML Model Comparison")
    st.caption("Trained on UCI Household Power Consumption dataset · Chronological 80/20 split")

    with st.spinner("Loading model results..."):
        train_result = cached_train_and_evaluate()

    best = train_result["best_model_name"]
    st.markdown("<br>", unsafe_allow_html=True)

    cols = st.columns(3)
    for i, (name, metrics) in enumerate(train_result["results"].items()):
        flag  = " ✅ Best" if name == best else ""
        color = MODEL_COLORS.get(name, GOLD)
        card_cls = "gold-card" if name == best else "blue-card"
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card {card_cls}">
                <div class="label" style="color:{color}">{name}{flag}</div>
                <div class="value">{metrics['MAE']} <span style="font-size:1rem;opacity:0.6">kWh</span></div>
                <div class="trend">RMSE: {metrics['RMSE']} kWh</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns(2, gap="large")
    names  = list(train_result["results"].keys())
    maes   = [train_result["results"][n]["MAE"]  for n in names]
    rmses  = [train_result["results"][n]["RMSE"] for n in names]
    colors = [MODEL_COLORS.get(n, GOLD) for n in names]

    with col_left:
        st.markdown("### MAE Comparison")
        with st.spinner("Rendering MAE chart..."):
            fig4, ax4 = make_fig(w=6, h=3.5)
            bars4 = ax4.bar(names, maes, color=colors, edgecolor=PANEL, linewidth=0.8, width=0.45)
            add_bar_glow(bars4, GOLD)
            for bar, val in zip(bars4, maes):
                ax4.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(maes)*0.025,
                         f"{val}", ha="center", va="bottom", color=TEXT_LT, fontsize=9, fontweight="600")
            best_idx = maes.index(min(maes))
            ax4.annotate("🏆 Best", xy=(best_idx,min(maes)),
                         xytext=(best_idx, min(maes)+max(maes)*0.12),
                         fontsize=8, color=GOLD, ha="center",
                         arrowprops=dict(arrowstyle="->",color=GOLD,lw=0.8))
            ax4.set_ylabel("MAE (kWh)", color=TEXT_DIM, fontsize=9)
            ax4.set_xlabel("Model", color=TEXT_DIM, fontsize=9)
            ax4.set_title("Model MAE — Lower is Better", color=TEXT_LT, pad=12, fontsize=10, fontweight="600")
            fig4.tight_layout(pad=1.8); st.pyplot(fig4); plt.close(fig4)

    with col_right:
        st.markdown("### RMSE Comparison")
        with st.spinner("Rendering RMSE chart..."):
            fig5, ax5 = make_fig(w=6, h=3.5)
            bars5 = ax5.bar(names, rmses, color=colors, edgecolor=PANEL, linewidth=0.8, width=0.45)
            add_bar_glow(bars5, GOLD)
            for bar, val in zip(bars5, rmses):
                ax5.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(rmses)*0.025,
                         f"{val}", ha="center", va="bottom", color=TEXT_LT, fontsize=9, fontweight="600")
            ax5.set_ylabel("RMSE (kWh)", color=TEXT_DIM, fontsize=9)
            ax5.set_xlabel("Model", color=TEXT_DIM, fontsize=9)
            ax5.set_title("Model RMSE — Lower is Better", color=TEXT_LT, pad=12, fontsize=10, fontweight="600")
            fig5.tight_layout(pad=1.8); st.pyplot(fig5); plt.close(fig5)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📈 Monthly Consumption Trend")
    with st.spinner("Loading trend data..."):
        df_hist = pd.read_csv("data/processed/uci_monthly.csv")
        df_hist["month"] = pd.to_datetime(df_hist["month"])
        mean_val = df_hist["energy_kwh"].mean()
        max_val  = df_hist["energy_kwh"].max()
        min_val  = df_hist["energy_kwh"].min()
        max_idx  = df_hist["energy_kwh"].idxmax()
        min_idx  = df_hist["energy_kwh"].idxmin()

        trend_fig = go.Figure()
        trend_fig.add_trace(go.Scatter(
            x=df_hist["month"], y=df_hist["energy_kwh"],
            fill="tozeroy", fillcolor="rgba(212,169,0,0.04)",
            line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"))
        trend_fig.add_trace(go.Scatter(
            x=df_hist["month"], y=df_hist["energy_kwh"],
            mode="lines", name="Monthly kWh", line=dict(color=GOLD, width=2.5),
            hovertemplate="<b>%{x|%b %Y}</b><br>%{y:.1f} kWh<extra></extra>"))
        trend_fig.add_hline(y=mean_val, line_dash="dash", line_color=BLUE, line_width=1.5,
                            annotation_text=f"Mean: {mean_val:.1f} kWh", annotation_font_color=BLUE)
        trend_fig.add_annotation(x=df_hist["month"].iloc[max_idx], y=max_val,
            text=f"Peak<br>{max_val:.0f}", showarrow=True, arrowhead=2, arrowcolor=GOLD,
            font=dict(color=GOLD, size=12), ax=0, ay=-36)
        trend_fig.add_annotation(x=df_hist["month"].iloc[min_idx], y=min_val,
            text=f"Low<br>{min_val:.0f}", showarrow=True, arrowhead=2, arrowcolor=STEEL,
            font=dict(color=STEEL, size=12), ax=0, ay=36)
        trend_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(11,13,17,0.45)",
            font=dict(color=TEXT_MID, family="Plus Jakarta Sans"),
            xaxis=dict(gridcolor=GRID_C, title=dict(text="Month", font=dict(color=TEXT_DIM, size=11)), tickfont=dict(color=TEXT_DIM)),
            yaxis=dict(gridcolor=GRID_C, title=dict(text="Energy (kWh)", font=dict(color=TEXT_DIM, size=11)), tickfont=dict(color=TEXT_DIM)),
            legend=dict(bgcolor="rgba(18,21,28,0.8)", bordercolor=GRID_C, font=dict(color=TEXT_LT)),
            margin=dict(t=50, b=50, l=60, r=30), height=520, hovermode="x unified")
        st.plotly_chart(trend_fig, use_container_width=True)

# ── Tab 4 — SHAP Explainability ──────────────────────────────
with tab4:
    st.markdown("## SHAP Explainability (XAI)")
    st.caption("Explains why XGBoost predicted the value it did — which features pushed it up or down.")

    with st.spinner("Computing SHAP values..."):
        shap_result = cached_explain_prediction()

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([2, 3], gap="large")

    with col_left:
        st.markdown("### Feature Contributions")
        st.markdown(
            f"**Base value** (dataset avg): "
            f"<code style='color:{GOLD};background:#1a1e28;padding:2px 8px;"
            f"border-radius:6px;font-family:Plus Jakarta Sans,sans-serif'>{shap_result['base_value']} kWh</code>",
            unsafe_allow_html=True)
        st.markdown(
            f"**XGBoost predicted**: "
            f"<code style='color:{STEEL};background:#1a1e28;padding:2px 8px;"
            f"border-radius:6px;font-family:Plus Jakarta Sans,sans-serif'>{shap_result['predicted_kwh']} kWh</code>",
            unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        max_abs = max(abs(c["shap_value"]) for c in shap_result["contributions"])
        for c in shap_result["contributions"]:
            color = GOLD if c["shap_value"] > 0 else STEEL
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:2px'>"
                f"<span style='color:var(--text-mid);font-size:0.85rem'>{c['label']}</span>"
                f"<span style='color:{color};font-family:Plus Jakarta Sans,sans-serif;font-size:0.88rem;font-weight:500'>"
                f"{c['shap_value']:+.2f}</span></div>", unsafe_allow_html=True)
            st.progress(min(abs(c["shap_value"]) / max_abs, 1.0))

    with col_right:
        st.markdown("### SHAP Waterfall Chart")
        labels      = shap_result["feature_labels"]
        values      = shap_result["shap_values"]
        colors_shap = [GOLD if v > 0 else STEEL for v in values]

        with st.spinner("Rendering SHAP chart..."):
            fig7, ax7 = make_fig(w=7, h=5.5, grid_axis="x")
            bars7 = ax7.barh(labels, values, color=colors_shap, edgecolor=PANEL, linewidth=0.8, height=0.52)
            for bar, c in zip(bars7, colors_shap):
                bar.set_path_effects([pe.Stroke(linewidth=5, foreground=c, alpha=0.2), pe.Normal()])
            for bar, val in zip(bars7, values):
                offset = max(abs(v) for v in values) * 0.03
                ax7.text(val+(offset if val>=0 else -offset), bar.get_y()+bar.get_height()/2,
                         f"{val:+.2f}", va="center", ha="left" if val>=0 else "right",
                         color=TEXT_LT, fontsize=8.5, fontweight="600")
            ax7.axvline(0, color=GRID_C, lw=1.2)
            ax7.set_xlabel("SHAP Value (kWh contribution)", color=TEXT_DIM, fontsize=9)
            ax7.set_ylabel("Feature", color=TEXT_DIM, fontsize=9)
            ax7.set_title(f"Why XGBoost predicted {shap_result['predicted_kwh']} kWh",
                          color=TEXT_LT, pad=14, fontsize=10.5, fontweight="600")
            ax7.legend(
                handles=[
                    mpatches.Patch(color=GOLD,  label="Pushes UP ↑"),
                    mpatches.Patch(color=STEEL, label="Pushes DOWN ↓")
                ],
                facecolor=PANEL, edgecolor=GRID_C, labelcolor=TEXT_LT, fontsize=9)
            fig7.tight_layout(pad=2.0)
            st.pyplot(fig7); plt.close(fig7)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.info(f"📌 Model starts from **{shap_result['base_value']} kWh** "
                f"and adjusts to reach **{shap_result['predicted_kwh']} kWh** "
                f"via {len(values)} feature contributions.")

# ── Tab 5 — Simulation History ────────────────────────────────
with tab5:
    st.markdown("## 📋 Simulation History")

    if not uid:
        st.info("🔒 Sign in with an account (not guest) to save and view your simulation history.")
    else:
        stats   = get_simulation_stats(uid)
        history = get_simulation_history(uid, limit=20)

        if not history:
            st.caption("No simulations saved yet — run one from the sidebar!")
        else:
            # ── Stats row ──────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            s1, s2, s3, s4 = st.columns(4)
            s1.markdown(f"""
            <div class="metric-card gold-card">
                <div class="label">Total Runs</div>
                <div class="value">{stats['total_runs']}</div>
            </div>""", unsafe_allow_html=True)
            s2.markdown(f"""
            <div class="metric-card blue-card">
                <div class="label">Avg Bill</div>
                <div class="value">₹{stats['avg_bill']:.0f}</div>
            </div>""", unsafe_allow_html=True)
            s3.markdown(f"""
            <div class="metric-card blue-card">
                <div class="label">Lowest Bill</div>
                <div class="value">₹{stats['min_bill']:.0f}</div>
            </div>""", unsafe_allow_html=True)
            s4.markdown(f"""
            <div class="metric-card blue-card">
                <div class="label">Highest Bill</div>
                <div class="value">₹{stats['max_bill']:.0f}</div>
            </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<hr>", unsafe_allow_html=True)

            # ── Bill trend chart ───────────────────────────
            if len(history) > 1:
                st.markdown("### 📈 Bill Trend")
                run_dates  = [str(r["run_at"])[:16] for r in reversed(history)]
                run_bills  = [r["total_bill"]        for r in reversed(history)]
                run_kwh    = [r["final_kwh"]          for r in reversed(history)]

                hist_fig = go.Figure()
                hist_fig.add_trace(go.Scatter(
                    x=run_dates, y=run_bills,
                    mode="lines+markers", name="Total Bill (₹)",
                    line=dict(color=GOLD, width=2.5),
                    marker=dict(color=GOLD, size=7),
                    hovertemplate="<b>%{x}</b><br>₹%{y:.2f}<extra></extra>"
                ))
                hist_fig.add_trace(go.Scatter(
                    x=run_dates, y=run_kwh,
                    mode="lines+markers", name="Final kWh",
                    line=dict(color=STEEL, width=2, dash="dot"),
                    marker=dict(color=STEEL, size=6),
                    hovertemplate="<b>%{x}</b><br>%{y:.2f} kWh<extra></extra>",
                    yaxis="y2"
                ))
                hist_fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(11,13,17,0.45)",
                    font=dict(color=TEXT_MID, family="Plus Jakarta Sans"),
                    xaxis=dict(gridcolor=GRID_C, tickfont=dict(color=TEXT_DIM), tickangle=-30),
                    yaxis=dict(gridcolor=GRID_C, title=dict(text="Bill (₹)", font=dict(color=GOLD, size=11)), tickfont=dict(color=TEXT_DIM)),
                    yaxis2=dict(overlaying="y", side="right", title=dict(text="kWh", font=dict(color=STEEL, size=11)), tickfont=dict(color=TEXT_DIM), gridcolor="rgba(0,0,0,0)"),
                    legend=dict(bgcolor="rgba(18,21,28,0.8)", bordercolor=GRID_C, font=dict(color=TEXT_LT)),
                    margin=dict(t=40, b=60, l=60, r=60), height=380, hovermode="x unified"
                )
                st.plotly_chart(hist_fig, use_container_width=True)
                st.markdown("<hr>", unsafe_allow_html=True)

            # ── Per-run expandable cards ───────────────────
            st.markdown("### Run Log")
            for run in history:
                run_at    = str(run["run_at"])[:16]
                num_apps  = len(run["appliances"])
                flag_icon = {"high_usage": "🔴", "low_usage": "🟢", "normal": "⚪"}.get(run["usage_flag"], "⚪")

                with st.expander(
                    f"{flag_icon}  {run_at}  ·  ₹{run['total_bill']}  ·  "
                    f"{run['final_kwh']} kWh  ·  {num_apps} appliance{'s' if num_apps != 1 else ''}"
                ):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Final kWh",        run["final_kwh"])
                    c2.metric("Total Bill",        f"₹{run['total_bill']}")
                    c3.metric("ML Predicted",      f"{run['ml_predicted_kwh']} kWh")
                    c4.metric("Usage",             run["usage_flag"].replace("_", " ").title())

                    if run["appliances"]:
                        st.markdown("**Appliances used in this run:**")
                        df_run = pd.DataFrame(run["appliances"])[
                            ["appliance", "hours_day", "quantity", "monthly_kwh"]
                        ]
                        df_run.columns = ["Appliance", "Hrs/Day", "Qty", "kWh/Month"]
                        st.dataframe(df_run, use_container_width=True, hide_index=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑 Delete this run", key=f"del_sim_{run['id']}", type="secondary"):
                        if delete_simulation(run["id"], uid):
                            st.toast("Run deleted.", icon="🗑")
                            st.rerun()