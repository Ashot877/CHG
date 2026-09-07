import streamlit as st


def apply_styles():
    st.markdown(
        r"""
        <style>
        :root {
            --bg: #f3f4f6;
            --surface: #ffffff;
            --surface-2: #f8f9fb;
            --ink: #111216;
            --muted: #6f737c;
            --line: #e4e6eb;
            --line-strong: #d7dae1;
            --sidebar: #0b0c0f;
            --sidebar-2: #111318;
            --accent: #f04b23;
            --accent-2: #ff7a45;
            --accent-soft: #fff1ec;
            --success: #17a673;
            --warning: #d59018;
            --danger: #d93a49;
        }

        html, body, [class*="css"] {
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 78% -10%, rgba(240,75,35,.055), transparent 26rem),
                linear-gradient(180deg, #f8f8f9 0%, var(--bg) 34%, #f1f2f4 100%);
            color: var(--ink);
        }

        #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; }
        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 3rem;
            max-width: 1480px;
        }

        /* ---------- SIDEBAR ---------- */
        section[data-testid="stSidebar"] {
            width: 292px !important;
            background:
                radial-gradient(circle at 20% 0%, rgba(240,75,35,.18), transparent 15rem),
                linear-gradient(180deg, #090a0d 0%, #0d0f13 52%, #090a0d 100%);
            border-right: 1px solid rgba(255,255,255,.055);
            box-shadow: 16px 0 40px rgba(10,12,16,.06);
        }
        section[data-testid="stSidebar"] > div { padding-top: 1.05rem; }
        section[data-testid="stSidebar"] * { color: #f5f6f8; }

        .brand-lockup {
            padding: 10px 8px 22px 8px;
            border-bottom: 1px solid rgba(255,255,255,.08);
            margin-bottom: 18px;
        }
        .brand-row { display:flex; align-items:center; gap:12px; }
        .brand-mark {
            width: 38px; height: 38px; border-radius: 12px;
            display:grid; place-items:center;
            background: linear-gradient(145deg, var(--accent), #c92e13);
            box-shadow: 0 10px 28px rgba(240,75,35,.25);
            color:#fff; font-size:15px; font-weight:900; letter-spacing:-.04em;
        }
        .brand-title { color:#fff; font-size:15px; font-weight:850; letter-spacing:.055em; line-height:1.1; }
        .brand-subtitle { color:#8f96a3; font-size:10px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin-top:4px; }

        .user-chip {
            margin: 0 5px 18px 5px;
            padding: 12px 13px;
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 15px;
            background: rgba(255,255,255,.035);
        }
        .user-name { color:#fff; font-size:13px; font-weight:750; }
        .user-meta { margin-top:4px; color:#8f96a3; font-size:11px; display:flex; align-items:center; gap:6px; }
        .status-dot { width:7px; height:7px; border-radius:99px; background:#22c58b; box-shadow:0 0 0 3px rgba(34,197,139,.12); display:inline-block; }

        .nav-label {
            color:#686f7b; font-size:9px; font-weight:800; letter-spacing:.14em;
            text-transform:uppercase; padding: 2px 9px 8px 9px;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 6px; }
        section[data-testid="stSidebar"] div[role="radiogroup"] > label {
            padding: 10px 12px !important;
            border-radius: 12px !important;
            min-height: 44px;
            transition: .16s ease;
            border: 1px solid transparent;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
            background: rgba(255,255,255,.055);
            border-color: rgba(255,255,255,.07);
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
            background: linear-gradient(90deg, rgba(240,75,35,.18), rgba(240,75,35,.055));
            border-color: rgba(240,75,35,.24);
            box-shadow: inset 3px 0 0 var(--accent);
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color:#fff !important; font-weight:750 !important; }
        section[data-testid="stSidebar"] [data-testid="stRadio"] p { color:#c8ccd4; font-size:13px; }
        section[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stWidgetLabel"] { display:none; }
        section[data-testid="stSidebar"] div[role="radiogroup"] input { display:none; }

        .sidebar-footer {
            color:#656b76; font-size:10px; line-height:1.55;
            padding: 16px 8px 2px 8px;
            border-top:1px solid rgba(255,255,255,.07);
            margin-top: 18px;
        }

        /* ---------- PAGE HEADER ---------- */
        .hero {
            position: relative;
            overflow: hidden;
            min-height: 180px;
            background:
                radial-gradient(circle at 87% 28%, rgba(240,75,35,.30), transparent 13rem),
                linear-gradient(118deg, #111318 0%, #171a20 63%, #0e1014 100%);
            padding: 30px 34px;
            border-radius: 24px;
            border: 1px solid #262a31;
            box-shadow: 0 22px 52px rgba(19,22,28,.14);
            margin-bottom: 22px;
        }
        .hero:after {
            content:"";
            position:absolute; right:-70px; bottom:-125px; width:310px; height:310px;
            border:1px solid rgba(255,255,255,.07); border-radius:999px;
            box-shadow: 0 0 0 36px rgba(255,255,255,.025), 0 0 0 72px rgba(255,255,255,.014);
        }
        .hero-eyebrow {
            position:relative; z-index:2;
            color:var(--accent-2); font-size:10px; font-weight:850; letter-spacing:.16em; text-transform:uppercase;
            margin-bottom:10px;
        }
        .hero-title {
            position:relative; z-index:2;
            font-size: 38px;
            line-height: 1.02;
            font-weight: 850;
            letter-spacing: -0.045em;
            color: #fff;
            margin-bottom: 10px;
        }
        .hero-subtitle { position:relative; z-index:2; font-size:14px; line-height:1.55; color:#a8aeb9; max-width:780px; }
        .pill-row { position:relative; z-index:2; margin-top:18px; display:flex; gap:8px; flex-wrap:wrap; }
        .pill {
            background: rgba(255,255,255,.055);
            color: #d6d9df;
            border: 1px solid rgba(255,255,255,.09);
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 10px;
            font-weight: 750;
            letter-spacing:.03em;
        }

        /* ---------- CARDS / PANELS ---------- */
        .section-card {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 20px;
            box-shadow: 0 9px 28px rgba(17,18,22,.045);
            padding: 22px 24px;
            margin-bottom: 18px;
        }
        .mini-card {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 8px 24px rgba(17,18,22,.04);
            height:100%;
        }
        .tool-card-title { font-size:16px; font-weight:800; color:var(--ink); margin-bottom:5px; }
        .tool-card-text { font-size:12px; color:var(--muted); line-height:1.55; }

        .metric-card {
            position:relative; overflow:hidden;
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 17px;
            padding: 15px 17px;
            min-height: 90px;
            box-shadow: 0 7px 22px rgba(17,18,22,.035);
        }
        .metric-card:before { content:""; position:absolute; top:0; left:0; width:3px; height:100%; background:var(--accent); }
        .metric-number { color:var(--ink); font-size:25px; line-height:1.1; font-weight:850; letter-spacing:-.025em; word-break:break-word; }
        .metric-label { color:var(--muted); font-size:10px; font-weight:750; letter-spacing:.055em; text-transform:uppercase; margin-top:6px; }

        .maintenance-banner, .feature-panel {
            position:relative; overflow:hidden;
            border:1px solid #eadbd6;
            background: linear-gradient(135deg, #fff 0%, #fff8f5 100%);
            border-radius:18px;
            padding:17px 19px;
            margin: 8px 0 18px 0;
        }
        .maintenance-banner:before, .feature-panel:before {
            content:""; position:absolute; top:0; left:0; bottom:0; width:4px;
            background:linear-gradient(180deg, var(--accent), var(--accent-2));
        }
        .maintenance-title, .feature-title { color:var(--ink); font-weight:820; font-size:15px; margin-bottom:4px; }
        .maintenance-text, .feature-text { color:var(--muted); font-size:12px; line-height:1.55; }
        .step-kicker { color:var(--accent); font-size:9px; font-weight:850; letter-spacing:.13em; text-transform:uppercase; margin-bottom:5px; }

        .group-title { font-size:16px; font-weight:800; color:var(--ink); margin-bottom:3px; }
        .group-subtitle { font-size:11px; color:var(--muted); margin-bottom:10px; }

        /* ---------- NATIVE STREAMLIT CONTROLS ---------- */
        h1, h2, h3 { color:var(--ink); letter-spacing:-.02em; }
        h2 { font-size:1.35rem !important; }
        h3 { font-size:1.05rem !important; }
        p, label, .stCaption { color:var(--muted); }
        hr { border-color:var(--line) !important; }

        div.stButton > button, div[data-testid="stDownloadButton"] > button, a[data-testid="stLinkButton"] {
            min-height: 42px;
            border-radius: 11px !important;
            font-weight: 750 !important;
            border: 1px solid var(--line-strong) !important;
            box-shadow: none !important;
            transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
        }
        div.stButton > button:hover, div[data-testid="stDownloadButton"] > button:hover, a[data-testid="stLinkButton"]:hover {
            transform: translateY(-1px);
            border-color:#c6c9d0 !important;
            box-shadow:0 6px 16px rgba(17,18,22,.07) !important;
        }
        div.stButton > button[kind="primary"] {
            color:#fff !important;
            background: linear-gradient(135deg, var(--accent), #d83a18) !important;
            border-color: var(--accent) !important;
            box-shadow:0 8px 18px rgba(240,75,35,.16) !important;
        }
        div.stButton > button[kind="primary"]:hover { box-shadow:0 10px 24px rgba(240,75,35,.23) !important; }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stNumberInput"] input,
        div[data-baseweb="select"] > div {
            border-radius: 11px !important;
            border-color:var(--line-strong) !important;
            background:#fff !important;
        }
        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus,
        div[data-testid="stNumberInput"] input:focus {
            border-color:rgba(240,75,35,.6) !important;
            box-shadow:0 0 0 3px rgba(240,75,35,.08) !important;
        }

        /* Horizontal radios behave like modern segmented controls. */
        main div[data-testid="stRadio"] div[role="radiogroup"]:has(> label + label) {
            gap:5px;
            padding:4px;
            background:#e9ebef;
            border-radius:13px;
            width:fit-content;
        }
        main div[data-testid="stRadio"] div[role="radiogroup"] > label {
            border-radius:10px;
            padding:7px 14px !important;
        }
        main div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
            background:#fff;
            box-shadow:0 2px 8px rgba(17,18,22,.09);
        }
        main div[data-testid="stRadio"] div[role="radiogroup"] input { accent-color: var(--accent); }

        div[data-testid="stFileUploaderDropzone"] {
            background:linear-gradient(180deg,#fff,#fafafa);
            border:1.5px dashed #cfd2d8;
            border-radius:16px;
            padding:8px;
        }
        div[data-testid="stFileUploaderDropzone"]:hover { border-color:rgba(240,75,35,.55); background:#fffaf8; }

        div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
            border:1px solid var(--line);
            border-radius:15px;
            overflow:hidden;
            box-shadow:0 5px 18px rgba(17,18,22,.03);
        }
        div[data-testid="stExpander"] {
            border:1px solid var(--line) !important;
            border-radius:14px !important;
            background:#fff;
        }
        div[data-testid="stAlert"] { border-radius:13px; }

        /* ---------- LOGIN ---------- */
        .login-shell {
            min-height: 47vh;
            display:flex; align-items:flex-end; justify-content:center;
            padding-top:4vh;
        }
        .login-card {
            position:relative; overflow:hidden;
            width:100%; max-width:590px;
            background:
                radial-gradient(circle at 92% 10%, rgba(240,75,35,.28), transparent 12rem),
                linear-gradient(145deg,#101217,#181b21);
            border:1px solid #272b33;
            border-radius:26px;
            box-shadow:0 30px 80px rgba(17,18,22,.20);
            padding:32px 34px;
        }
        .login-brand { color:var(--accent-2); font-size:10px; font-weight:850; letter-spacing:.15em; text-transform:uppercase; margin-bottom:13px; }
        .login-title { color:#fff; font-size:34px; line-height:1.04; font-weight:850; letter-spacing:-.04em; margin-bottom:10px; }
        .login-subtitle { color:#9fa5af; font-size:13px; line-height:1.55; max-width:470px; }
        .login-rule { width:42px; height:3px; background:var(--accent); border-radius:99px; margin-top:20px; }

        @media (max-width: 900px) {
            .block-container { padding-top:1rem; }
            .hero { padding:24px 22px; min-height:160px; }
            .hero-title { font-size:31px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
