# auth.py — WattsInBill Login & Registration Page
import streamlit as st
from database import init_db, register_user, login_user

init_db()

def logout():
    st.session_state.authenticated = False
    st.session_state.username      = ""
    st.session_state.user_id       = None
    st.rerun()


AUTH_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Archivo+Black&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: #080a0e; color: #e8edf5;
}
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"]  { display: none; }
[data-testid="stSidebar"]  { display: none !important; }
[data-testid="stAppViewContainer"], [data-testid="stMain"] { background: #080a0e !important; }
.block-container { padding-top: 0rem !important; max-width: 100% !important; }

/* grain */
[data-testid="stMain"]::after {
    content:''; position:fixed; inset:0; pointer-events:none; z-index:9999; opacity:0.28;
    background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E");
    background-size:200px; animation:grain 2s steps(2) infinite;
}
@keyframes grain {
    0%{transform:translate(0,0)} 25%{transform:translate(-2px,1px)}
    50%{transform:translate(1px,-2px)} 75%{transform:translate(2px,1px)} 100%{transform:translate(-1px,2px)}
}

/* hero left panel */
.hero-panel {
    
    padding: 28px 32px;
    background:
        radial-gradient(ellipse 80% 50% at 15% 25%, rgba(212,169,0,0.11) 0%, transparent 55%),
        radial-gradient(ellipse 50% 60% at 85% 80%, rgba(91,141,184,0.07) 0%, transparent 55%),
        linear-gradient(160deg, #0a0d13 0%, #080a0e 100%);
    border-right: 1px solid rgba(212,169,0,0.10);
    border-radius: 20px;
    position: relative; overflow: hidden;
}
.hero-panel::before {
    content:''; position:absolute; inset:0; pointer-events:none;
    background-image:
        linear-gradient(rgba(212,169,0,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(212,169,0,0.04) 1px, transparent 1px);
    background-size: 52px 52px;
    mask-image: radial-gradient(ellipse 70% 70% at 25% 40%, black 0%, transparent 70%);
    -webkit-mask-image: radial-gradient(ellipse 70% 70% at 25% 40%, black 0%, transparent 70%);
}
.hero-brand { display:flex; align-items:center; gap:14px; margin-bottom:28px; position:relative; z-index:2; }
.hero-bolt {
    font-size:2.4rem; line-height:1;
    filter: drop-shadow(0 0 14px rgba(212,169,0,1)) drop-shadow(0 0 28px rgba(212,169,0,0.5));
    animation: bolt 2.5s ease-in-out infinite;
}
@keyframes bolt {
    0%,100%{filter:drop-shadow(0 0 12px rgba(212,169,0,0.8)) drop-shadow(0 0 24px rgba(212,169,0,0.3))}
    50%{filter:drop-shadow(0 0 22px rgba(212,169,0,1)) drop-shadow(0 0 48px rgba(212,169,0,0.6))}
}
.hero-brand-name {
    font-family:'Syne',sans-serif; font-size:1.7rem; font-weight:800; letter-spacing:-0.02em; line-height:1;
    background:linear-gradient(135deg,#D4A900,#f5d060,#D4A900);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.hero-brand-sub { font-size:0.62rem; color:#3a3f4e; letter-spacing:0.14em; text-transform:uppercase; margin-top:4px; }
.hero-h1 {
    font-family:'Syne',sans-serif; font-size:2.2rem; font-weight:800; line-height:1.08;
    letter-spacing:-0.03em; color:#e8edf5; margin-bottom:14px; position:relative; z-index:2;
}
.hero-h1 em {
    font-style:normal;
    background:linear-gradient(135deg,#D4A900,#f5d060);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.hero-sub { font-size:0.88rem; color:#8a8f9e; line-height:1.7; max-width:320px; margin-bottom:18px; position:relative; z-index:2; }
.stat-pill {
    display:flex; align-items:center; gap:14px;
    background:rgba(212,169,0,0.04); border:1px solid rgba(212,169,0,0.11);
    border-radius:14px; padding:10px 14px; margin-bottom:8px;
    position:relative; z-index:2; transition:all 0.25s ease;
}
.stat-pill:hover { background:rgba(212,169,0,0.08); border-color:rgba(212,169,0,0.22); }
.stat-icon { font-size:1.4rem; width:34px; text-align:center; flex-shrink:0; }
.stat-val { font-family:'Archivo Black',sans-serif; font-size:1rem; color:#D4A900; line-height:1; }
.stat-lbl { font-size:0.64rem; color:#3a3f4e; text-transform:uppercase; letter-spacing:0.10em; margin-top:3px; }
.stat-bar { width:100%; height:3px; background:rgba(212,169,0,0.10); border-radius:2px; margin-top:7px; overflow:hidden; }
.stat-bar-fill { height:100%; background:linear-gradient(90deg,#D4A900,#f5d060); border-radius:2px; animation:grow 1.6s cubic-bezier(.4,0,.2,1) both; }
@keyframes grow { from{width:0} }
.hero-foot { font-size:0.62rem; color:#3a3f4e; letter-spacing:0.10em; text-transform:uppercase; position:relative; z-index:2; margin-top:20px; }

/* form right panel */
.form-panel {
    
    padding: 28px 36px;
    background: linear-gradient(170deg, #0c0f15 0%, #080a0e 100%);
    border-radius: 20px;
    position: relative; overflow: hidden;
    display: flex; flex-direction: column; justify-content: center;
}
.form-panel::before {
    content:''; position:absolute; top:-100px; right:-100px; width:360px; height:360px;
    background:radial-gradient(circle, rgba(212,169,0,0.07) 0%, transparent 65%);
    pointer-events:none;
}

/* tab pill */
.tab-pill {
    display:flex; background:rgba(255,255,255,0.03);
    border:1px solid rgba(255,255,255,0.06); border-radius:12px;
    padding:4px; margin-bottom:24px;
}
.tab-pill-item {
    flex:1; text-align:center; padding:10px 0;
    font-family:'Syne',sans-serif; font-size:0.83rem; font-weight:700;
    color:#3a3f4e; border-radius:9px; letter-spacing:0.03em;
}
.tab-pill-item.active {
    background:linear-gradient(135deg,rgba(212,169,0,0.22),rgba(212,169,0,0.10));
    color:#D4A900; border:1px solid rgba(212,169,0,0.24);
    box-shadow:0 0 16px rgba(212,169,0,0.08);
}

/* form header */
.f-greet { font-size:0.67rem; color:#D4A900; font-weight:700; text-transform:uppercase; letter-spacing:0.14em; margin-bottom:7px; }
.f-title { font-family:'Syne',sans-serif; font-size:1.6rem; font-weight:800; color:#e8edf5; letter-spacing:-0.03em; line-height:1.1; margin-bottom:7px; }
.f-sub   { font-size:0.82rem; color:#8a8f9e; margin-bottom:22px; }
.feat-row { display:flex; align-items:center; gap:10px; font-size:0.79rem; color:#8a8f9e; margin-bottom:8px; }
.feat-dot { width:6px; height:6px; border-radius:50%; background:#D4A900; flex-shrink:0; box-shadow:0 0 6px rgba(212,169,0,0.7); }

/* primary button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#a07800 0%,#D4A900 35%,#f5d060 55%,#D4A900 75%,#a07800 100%) !important;
    background-size: 300% 100% !important; color: #080a0e !important;
    border: none !important; border-radius: 14px !important;
    font-family: 'Syne',sans-serif !important; font-weight: 800 !important;
    font-size: 0.95rem !important; letter-spacing: 0.05em !important;
    padding: 14px 0 !important; position: relative; overflow: hidden;
    transition: background-position 0.5s ease, box-shadow 0.3s ease, transform 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    background-position: 100% 0 !important;
    box-shadow: 0 0 32px rgba(212,169,0,0.45), 0 0 64px rgba(212,169,0,0.18) !important;
    transform: translateY(-2px) !important;
}
.stButton > button[kind="primary"]::before {
    content:''; position:absolute; top:0; left:-100%; width:55%; height:100%;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,0.35),transparent);
    transform:skewX(-18deg); animation:shimmer 2.8s ease-in-out infinite;
}
@keyframes shimmer { 0%{left:-100%} 55%{left:130%} 100%{left:130%} }

/* ghost button */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid rgba(212,169,0,0.25) !important;
    border-radius: 14px !important; color: #8a8f9e !important;
    font-family: 'Syne',sans-serif !important; font-weight: 600 !important;
    font-size: 0.88rem !important; padding: 13px 0 !important;
    transition: all 0.25s ease !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(212,169,0,0.07) !important;
    border-color: rgba(212,169,0,0.45) !important; color: #D4A900 !important;
}

/* messages */
.msg-ok  { background:linear-gradient(90deg,rgba(61,184,122,0.12),transparent); border-left:3px solid #3db87a; border-radius:0 10px 10px 0; padding:11px 16px; font-size:0.82rem; color:#6ef5a8; margin-bottom:16px; }
.msg-err { background:linear-gradient(90deg,rgba(224,85,85,0.12),transparent); border-left:3px solid #e05555; border-radius:0 10px 10px 0; padding:11px 16px; font-size:0.82rem; color:#ff9090; margin-bottom:16px; }

/* divider */
.or-divider { display:flex; align-items:center; gap:12px; margin:16px 0; }
.or-divider::before, .or-divider::after { content:''; flex:1; height:1px; background:linear-gradient(90deg,transparent,rgba(212,169,0,0.15),transparent); }
.or-divider span { font-size:0.67rem; color:#3a3f4e; text-transform:uppercase; letter-spacing:0.12em; }

.f-hint { font-size:0.74rem; color:#3a3f4e; text-align:center; margin-top:16px; line-height:1.6; }
.f-hint b { color:#D4A900; font-weight:600; }

/* hide the tab radio widget — purely functional */
[data-testid="stRadio"] {
    display: none !important;
}

/* ── tab pill buttons ── */
div[data-testid="stHorizontalBlock"]:has(button[kind="secondaryFormSubmit"]),
div[data-testid="stHorizontalBlock"]:has(button[data-testid="baseButton-secondary"]) {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
}
/* active tab — gold */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#a07800 0%,#D4A900 35%,#f5d060 55%,#D4A900 75%,#a07800 100%) !important;
    background-size: 300% 100% !important; color: #080a0e !important;
    border: none !important; border-radius: 10px !important;
    font-family: 'Syne',sans-serif !important; font-weight: 800 !important;
    font-size: 0.88rem !important; letter-spacing: 0.04em !important;
    padding: 10px 0 !important; position: relative; overflow: hidden;
    transition: background-position 0.5s ease, box-shadow 0.3s ease !important;
}
.stButton > button[kind="primary"]:hover {
    background-position: 100% 0 !important;
    box-shadow: 0 0 24px rgba(212,169,0,0.4) !important;
}
.stButton > button[kind="primary"]::before {
    content:''; position:absolute; top:0; left:-100%; width:55%; height:100%;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,0.3),transparent);
    transform:skewX(-18deg); animation:shimmer 2.8s ease-in-out infinite;
}
@keyframes shimmer{0%{left:-100%}55%{left:130%}100%{left:130%}}
/* inactive tab — ghost */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: none !important;
    border-radius: 10px !important; color: #3a3f4e !important;
    font-family: 'Syne',sans-serif !important; font-weight: 700 !important;
    font-size: 0.88rem !important; padding: 10px 0 !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(212,169,0,0.06) !important;
    color: #8a8f9e !important;
}

/* ── Modern inputs — full override ── */
[data-testid="stTextInput"] { margin-bottom: 4px; }
[data-testid="stTextInput"] label {
    font-size: 0.64rem !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.14em !important;
    color: #5a6070 !important; font-family: 'Plus Jakarta Sans',sans-serif !important;
    margin-bottom: 6px !important;
}
/* kill ALL wrapper borders */
[data-testid="stTextInput"] > div,
[data-testid="stTextInput"] > div > div,
[data-testid="stTextInput"] > div > div > div {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    padding: 0 !important;
}
/* the actual input */
[data-testid="stTextInput"] input {
    background: #0d1017 !important;
    border: 1.5px solid #1e2433 !important;
    border-radius: 12px !important;
    color: #e8edf5 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.92rem !important;
    padding: 13px 16px !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    outline: none !important;
    box-shadow: none !important;
    -webkit-appearance: none !important;
    appearance: none !important;
}
[data-testid="stTextInput"] input::placeholder {
    color: #2e3444 !important;
    font-size: 0.88rem !important;
}
[data-testid="stTextInput"] input:hover {
    border-color: rgba(212,169,0,0.30) !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextInput"] input:focus-visible,
[data-testid="stTextInput"] input:focus-within,
[data-testid="stTextInput"] input:active {
    border-color: #D4A900 !important;
    box-shadow: 0 0 0 3px rgba(212,169,0,0.12), 0 0 16px rgba(212,169,0,0.08) !important;
    background: #0f131c !important;
    outline: none !important;
}

</style>
"""


def show_auth_page():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
    if "auth_msg"  not in st.session_state:
        st.session_state.auth_msg  = None

    left, right = st.columns([1.05, 0.95])

    # ══════════════════════════════════════
    # LEFT — Hero panel (pure HTML via markdown)
    # ══════════════════════════════════════
    with left:
        st.markdown("""
        <div class="hero-panel">
            <div class="hero-brand">
                <div class="hero-bolt">⚡</div>
                <div>
                    <div class="hero-brand-name">WattsInBill</div>
                    <div class="hero-brand-sub">v2.2 · ML Electricity Predictor</div>
                </div>
            </div>
            <div class="hero-h1">Predict your bill<br>before it <em>arrives.</em></div>
            <div class="hero-sub">Machine learning meets your appliance usage — get an accurate electricity bill estimate every month, automatically.</div>
            <div class="stat-pill">
                <div class="stat-icon">🤖</div>
                <div style="flex:1">
                    <div class="stat-val">3 ML Models</div>
                    <div class="stat-lbl">RandomForest · XGBoost · Ridge</div>
                    <div class="stat-bar"><div class="stat-bar-fill" style="width:92%"></div></div>
                </div>
            </div>
            <div class="stat-pill">
                <div class="stat-icon">🔌</div>
                <div style="flex:1">
                    <div class="stat-val">12 Appliances</div>
                    <div class="stat-lbl">AC · Fridge · Geyser · and more</div>
                    <div class="stat-bar"><div class="stat-bar-fill" style="width:78%;animation-delay:0.2s"></div></div>
                </div>
            </div>
            <div class="stat-pill">
                <div class="stat-icon">🧠</div>
                <div style="flex:1">
                    <div class="stat-val">SHAP XAI</div>
                    <div class="stat-lbl">Full explainability on every prediction</div>
                    <div class="stat-bar"><div class="stat-bar-fill" style="width:85%;animation-delay:0.4s"></div></div>
                </div>
            </div>
            <div class="stat-pill">
                <div class="stat-icon">📋</div>
                <div style="flex:1">
                    <div class="stat-val">History Tracking</div>
                    <div class="stat-lbl">Every run saved to your account</div>
                    <div class="stat-bar"><div class="stat-bar-fill" style="width:65%;animation-delay:0.6s"></div></div>
                </div>
            </div>
            <div class="hero-foot">Powered by UCI Household Power Dataset &nbsp;·&nbsp; 48 months of data</div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════
    # RIGHT — Form panel
    # ══════════════════════════════════════
    with right:
        mode = st.session_state.auth_mode

        st.markdown("<div class='form-panel'>", unsafe_allow_html=True)

        # Tab pill — real buttons, active=primary gold, inactive=ghost
        tc1, tc2 = st.columns(2)
        with tc1:
            if st.button("Sign In", key="tab_l", use_container_width=True,
                         type="primary" if mode == "login" else "secondary"):
                st.session_state.auth_mode = "login"
                st.session_state.auth_msg  = None
                st.rerun()
        with tc2:
            if st.button("Create Account", key="tab_r", use_container_width=True,
                         type="primary" if mode == "register" else "secondary"):
                st.session_state.auth_mode = "register"
                st.session_state.auth_msg  = None
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Message banner
        if st.session_state.auth_msg:
            t, m = st.session_state.auth_msg
            cls  = "msg-ok" if t == "success" else "msg-err"
            icon = "✓" if t == "success" else "✕"
            st.markdown(f'<div class="{cls}">{icon} &nbsp;{m}</div>', unsafe_allow_html=True)

        # ── LOGIN ──────────────────────────────────────────
        if mode == "login":
            st.markdown("""
            <div class="f-greet">Welcome back</div>
            <div class="f-title">Sign in to<br>your account</div>
            <div class="f-sub">Your simulation history is waiting.</div>
            """, unsafe_allow_html=True)

            username = st.text_input("Username", placeholder="enter your username", key="li_user")
            password = st.text_input("Password", placeholder="••••••••", type="password", key="li_pass")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("⚡  Sign In", use_container_width=True, type="primary", key="li_btn"):
                if not username or not password:
                    st.session_state.auth_msg = ("error", "Please fill in both fields.")
                else:
                    ok, msg_txt, uid = login_user(username, password)
                    if ok:
                        st.session_state.authenticated = True
                        st.session_state.username      = username.strip().lower()
                        st.session_state.user_id       = uid
                        st.session_state.auth_msg      = None
                        st.rerun()
                    else:
                        st.session_state.auth_msg = ("error", msg_txt)
                st.rerun()

            st.markdown('<div class="or-divider"><span>or</span></div>', unsafe_allow_html=True)

            if st.button("Continue as Guest", use_container_width=True, type="secondary", key="guest_btn"):
                st.session_state.authenticated = True
                st.session_state.username      = "guest"
                st.session_state.user_id       = None
                st.session_state.auth_msg      = None
                st.rerun()

            st.markdown('<div class="f-hint">No account? Switch to <b>Create Account</b> above.</div>',
                        unsafe_allow_html=True)

        # ── REGISTER ───────────────────────────────────────
        else:
            st.markdown("""
            <div class="f-greet">Get started free</div>
            <div class="f-title">Create your<br>account</div>
            <div class="f-sub">Start predicting your electricity bill in seconds.</div>
            <div class="feat-row"><div class="feat-dot"></div>Unlimited simulations</div>
            <div class="feat-row"><div class="feat-dot"></div>Full simulation history saved</div>
            <div class="feat-row" style="margin-bottom:18px"><div class="feat-dot"></div>SHAP explainability on every run</div>
            """, unsafe_allow_html=True)

            username  = st.text_input("Username",         placeholder="min. 3 characters",    key="reg_user")
            password  = st.text_input("Password",         placeholder="min. 6 characters",    type="password", key="reg_pass")
            password2 = st.text_input("Confirm password", placeholder="repeat your password", type="password", key="reg_pass2")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Create Account  →", use_container_width=True, type="primary", key="reg_btn"):
                if not username or not password or not password2:
                    st.session_state.auth_msg = ("error", "Please fill in all fields.")
                elif password != password2:
                    st.session_state.auth_msg = ("error", "Passwords do not match.")
                else:
                    ok, msg_txt = register_user(username, password)
                    if ok:
                        st.session_state.auth_msg  = ("success", f"{msg_txt} Please sign in.")
                        st.session_state.auth_mode = "login"
                    else:
                        st.session_state.auth_msg = ("error", msg_txt)
                st.rerun()

            st.markdown('<div class="f-hint">Already have an account? Switch to <b>Sign In</b> above.</div>',
                        unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


def require_login():
    for key, default in [("authenticated", False), ("username", ""), ("user_id", None)]:
        if key not in st.session_state:
            st.session_state[key] = default
    if not st.session_state.authenticated:
        show_auth_page()
        st.stop()