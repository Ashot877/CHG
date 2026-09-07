import streamlit as st


def apply_styles():
    st.markdown(
        r"""
        <style>
        :root {
            --bg: #f5f6f8;
            --surface: #ffffff;
            --surface-soft: #fafbfc;
            --ink: #16181d;
            --muted: #6f7580;
            --line: #e3e6ea;
            --line-strong: #d6dae0;
            --sidebar: #111318;
            --sidebar-soft: #181b21;
            --accent: #f04b23;
            --accent-dark: #d73b17;
            --accent-soft: #fff3ee;
            --success: #20b486;
        }

        html, body, [class*="css"] {
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 82% -8%, rgba(240,75,35,.04), transparent 26rem),
                linear-gradient(180deg, #fafafa 0%, var(--bg) 38%, #f3f4f6 100%);
            color: var(--ink);
        }

        #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; }

        /* Hide Streamlit's automatic multipage navigation even if old pages/ files still exist. */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            display: none !important;
        }

        .block-container {
            padding-top: 1.65rem;
            padding-bottom: 3rem;
            max-width: 1460px;
        }

        /* ---------- SIDEBAR ---------- */
        section[data-testid="stSidebar"] {
            width: 274px !important;
            background: linear-gradient(180deg, #111318 0%, #0d0f13 100%);
            border-right: 1px solid rgba(255,255,255,.055);
            box-shadow: 14px 0 34px rgba(17,19,24,.06);
        }
        section[data-testid="stSidebar"] > div { padding-top: 1.15rem; }
        section[data-testid="stSidebar"] * { color: #f5f6f8; }

        .brand-lockup {
            padding: 8px 7px 19px 7px;
            border-bottom: 1px solid rgba(255,255,255,.075);
            margin-bottom: 16px;
        }
        .brand-row { display:flex; align-items:center; gap:11px; }
        .brand-mark {
            width: 36px; height: 36px; border-radius: 11px;
            display:grid; place-items:center;
            background: var(--accent);
            box-shadow: 0 8px 22px rgba(240,75,35,.22);
            color:#fff; font-size:13px; font-weight:900; letter-spacing:-.035em;
        }
        .brand-title { color:#fff; font-size:14px; font-weight:800; letter-spacing:-.01em; line-height:1.15; }
        .brand-subtitle { color:#7f8793; font-size:9px; font-weight:700; letter-spacing:.11em; text-transform:uppercase; margin-top:4px; }

        .user-chip {
            margin: 0 4px 18px 4px;
            padding: 12px 13px;
            border: 1px solid rgba(255,255,255,.075);
            border-radius: 14px;
            background: rgba(255,255,255,.028);
        }
        .user-name { color:#fff; font-size:12px; font-weight:720; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .user-meta { margin-top:5px; color:#8d95a0; font-size:10px; display:flex; align-items:center; gap:7px; }
        .status-dot { width:7px; height:7px; border-radius:99px; background:var(--success); box-shadow:0 0 0 3px rgba(32,180,134,.12); display:inline-block; }

        .nav-label {
            color:#646b76; font-size:8px; font-weight:800; letter-spacing:.15em;
            text-transform:uppercase; padding: 2px 9px 8px 9px;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 5px; }
        section[data-testid="stSidebar"] div[role="radiogroup"] > label {
            padding: 9px 11px !important;
            border-radius: 11px !important;
            min-height: 42px;
            transition: .15s ease;
            border: 1px solid transparent;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
            background: rgba(255,255,255,.045);
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
            background: rgba(240,75,35,.12);
            border-color: rgba(240,75,35,.22);
            box-shadow: inset 3px 0 0 var(--accent);
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color:#fff !important; font-weight:750 !important; }
        section[data-testid="stSidebar"] [data-testid="stRadio"] p { color:#cbd0d7; font-size:12px; }
        section[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stWidgetLabel"] { display:none; }
        section[data-testid="stSidebar"] div[role="radiogroup"] input { display:none; }

        .logout-separator {
            height:1px;
            background:rgba(255,255,255,.075);
            margin: 24px 0 14px 0;
        }

        /* Make Log out actually visible instead of white text on a white button. */
        section[data-testid="stSidebar"] div.stButton > button {
            min-height: 40px !important;
            color: #e8eaee !important;
            background: #171a20 !important;
            border: 1px solid rgba(255,255,255,.10) !important;
            border-radius: 11px !important;
            box-shadow: none !important;
            font-weight: 700 !important;
        }
        section[data-testid="stSidebar"] div.stButton > button:hover {
            color:#fff !important;
            background:#1d2027 !important;
            border-color:rgba(240,75,35,.38) !important;
            transform:none !important;
            box-shadow:none !important;
        }

        .sidebar-footer {
            color:#5f6671; font-size:9px; line-height:1.55;
            padding: 15px 7px 2px 7px;
            margin-top: 16px;
        }
        .sidebar-footer span { color:#555d68; }

        /* ---------- PAGE HEADER ---------- */
        .hero {
            position: relative;
            overflow: hidden;
            min-height: 162px;
            background:
                radial-gradient(circle at 91% 10%, rgba(240,75,35,.18), transparent 13rem),
                linear-gradient(118deg, #15171c 0%, #1a1d23 70%, #15171c 100%);
            padding: 27px 31px;
            border-radius: 22px;
            border: 1px solid #292d34;
            box-shadow: 0 18px 42px rgba(19,22,28,.12);
            margin-bottom: 21px;
        }
        .hero:after {
            content:"";
            position:absolute; right:-88px; bottom:-145px; width:310px; height:310px;
            border:1px solid rgba(255,255,255,.055); border-radius:999px;
            box-shadow: 0 0 0 34px rgba(255,255,255,.018), 0 0 0 68px rgba(255,255,255,.009);
        }
        .hero-eyebrow {
            position:relative; z-index:2;
            color:#ff845f; font-size:9px; font-weight:820; letter-spacing:.14em; text-transform:uppercase;
            margin-bottom:9px;
        }
        .hero-title {
            position:relative; z-index:2;
            font-size: 35px;
            line-height: 1.03;
            font-weight: 840;
            letter-spacing: -0.042em;
            color: #fff;
            margin-bottom: 9px;
        }
        .hero-subtitle { position:relative; z-index:2; font-size:13px; line-height:1.55; color:#aab0ba; max-width:780px; }
        .pill-row { position:relative; z-index:2; margin-top:16px; display:flex; gap:7px; flex-wrap:wrap; }
        .pill {
            background: rgba(255,255,255,.048);
            color: #d7dae0;
            border: 1px solid rgba(255,255,255,.08);
            padding: 5px 9px;
            border-radius: 999px;
            font-size: 9px;
            font-weight: 730;
        }

        /* ---------- CARDS / PANELS ---------- */
        .section-card {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 18px;
            box-shadow: 0 7px 22px rgba(17,18,22,.035);
            padding: 20px 22px;
            margin-bottom: 16px;
        }
        .mini-card {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 17px;
            box-shadow: 0 6px 20px rgba(17,18,22,.032);
            height:100%;
        }
        .tool-card-title { font-size:15px; font-weight:800; color:var(--ink); margin-bottom:4px; }
        .tool-card-text { font-size:12px; color:var(--muted); line-height:1.55; }

        .metric-card {
            position:relative; overflow:hidden;
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 14px 16px;
            min-height: 86px;
            box-shadow: 0 6px 20px rgba(17,18,22,.03);
        }
        .metric-card:before { content:""; position:absolute; top:0; left:0; width:3px; height:100%; background:var(--accent); }
        .metric-number { color:var(--ink); font-size:24px; line-height:1.1; font-weight:840; letter-spacing:-.025em; word-break:break-word; }
        .metric-label { color:var(--muted); font-size:9px; font-weight:760; letter-spacing:.06em; text-transform:uppercase; margin-top:6px; }

        .maintenance-banner, .feature-panel {
            position:relative; overflow:hidden;
            border:1px solid #eadfd9;
            background: linear-gradient(135deg, #fff 0%, #fffaf8 100%);
            border-radius:16px;
            padding:16px 18px;
            margin: 8px 0 17px 0;
        }
        .maintenance-banner:before, .feature-panel:before {
            content:""; position:absolute; top:0; left:0; bottom:0; width:3px;
            background:var(--accent);
        }
        .maintenance-title, .feature-title { color:var(--ink); font-weight:810; font-size:14px; margin-bottom:4px; }
        .maintenance-text, .feature-text { color:var(--muted); font-size:11px; line-height:1.55; }
        .step-kicker { color:var(--accent); font-size:8px; font-weight:850; letter-spacing:.15em; text-transform:uppercase; margin-bottom:5px; }
        .group-title { font-size:15px; font-weight:800; color:var(--ink); margin-bottom:3px; }
        .group-subtitle { font-size:11px; color:var(--muted); margin-bottom:9px; }

        /* ---------- STREAMLIT CONTROLS ---------- */
        div.stButton > button, div[data-testid="stDownloadButton"] > button, a[data-testid="stLinkButton"] {
            min-height: 41px;
            border-radius: 10px !important;
            font-weight: 730 !important;
            border: 1px solid var(--line-strong) !important;
            box-shadow: none !important;
            transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
        }
        div.stButton > button:hover, div[data-testid="stDownloadButton"] > button:hover, a[data-testid="stLinkButton"]:hover {
            transform: translateY(-1px);
            border-color:#c5c9cf !important;
            box-shadow:0 5px 14px rgba(17,18,22,.055) !important;
        }
        div.stButton > button[kind="primary"], button[kind="primaryFormSubmit"] {
            color:#fff !important;
            background: var(--accent) !important;
            border-color: var(--accent) !important;
            box-shadow:0 7px 17px rgba(240,75,35,.14) !important;
        }
        div.stButton > button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover {
            background:var(--accent-dark) !important;
            box-shadow:0 9px 20px rgba(240,75,35,.19) !important;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stNumberInput"] input,
        div[data-baseweb="select"] > div {
            border-radius: 10px !important;
            border-color:var(--line-strong) !important;
            background:#fff !important;
        }
        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus,
        div[data-testid="stNumberInput"] input:focus {
            border-color:rgba(240,75,35,.55) !important;
            box-shadow:0 0 0 3px rgba(240,75,35,.07) !important;
        }

        main div[data-testid="stRadio"] div[role="radiogroup"]:has(> label + label) {
            gap:4px;
            padding:4px;
            background:#e9ebee;
            border-radius:12px;
            width:fit-content;
        }
        main div[data-testid="stRadio"] div[role="radiogroup"] > label {
            border-radius:9px;
            padding:6px 13px !important;
        }
        main div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
            background:#fff;
            box-shadow:0 2px 7px rgba(17,18,22,.08);
        }
        main div[data-testid="stRadio"] div[role="radiogroup"] input { accent-color: var(--accent); }

        div[data-testid="stFileUploaderDropzone"] {
            background:linear-gradient(180deg,#fff,#fbfbfc);
            border:1.5px dashed #cfd3d9;
            border-radius:14px;
            padding:8px;
        }
        div[data-testid="stFileUploaderDropzone"]:hover { border-color:rgba(240,75,35,.5); background:#fffaf8; }

        div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
            border:1px solid var(--line);
            border-radius:14px;
            overflow:hidden;
            box-shadow:0 4px 15px rgba(17,18,22,.025);
        }
        div[data-testid="stExpander"] {
            border:1px solid var(--line) !important;
            border-radius:12px !important;
            background:#fff;
        }
        div[data-testid="stAlert"] { border-radius:12px; }

        /* ---------- LOGIN ---------- */
        .login-header {
            text-align:left;
            padding-bottom: 9px;
        }
        .login-mark {
            width: 38px;
            height: 38px;
            border-radius: 11px;
            display:grid;
            place-items:center;
            color:#fff;
            background:var(--accent);
            box-shadow:0 9px 22px rgba(240,75,35,.20);
            font-size:13px;
            font-weight:900;
            margin-bottom:20px;
        }
        .login-eyebrow {
            color:var(--accent);
            font-size:9px;
            font-weight:850;
            letter-spacing:.14em;
            text-transform:uppercase;
            margin-bottom:7px;
        }
        .login-title {
            color:var(--ink);
            font-size:31px;
            line-height:1.05;
            font-weight:850;
            letter-spacing:-.04em;
            margin-bottom:9px;
        }
        .login-subtitle {
            color:var(--muted);
            font-size:12px;
            line-height:1.55;
            max-width:430px;
            margin-bottom:10px;
        }
        .login-note {
            color:#8a9099;
            font-size:10px;
            line-height:1.45;
            text-align:center;
            margin-top:8px;
        }

        /* The whole password experience is now one card, instead of a nice header floating above random widgets. */
        div[data-testid="stForm"] {
            margin-top: 14vh;
            padding: 30px 31px 25px 31px !important;
            background: rgba(255,255,255,.97) !important;
            border: 1px solid var(--line) !important;
            border-radius: 23px !important;
            box-shadow: 0 24px 65px rgba(20,23,29,.12) !important;
        }
        div[data-testid="stForm"] label p {
            color:#4e5560 !important;
            font-size:11px !important;
            font-weight:700 !important;
        }
        div[data-testid="stForm"] div[data-testid="stTextInput"] input {
            min-height:45px;
            background:#fbfbfc !important;
        }
        div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
            min-height:44px;
            border-radius:11px !important;
            font-weight:780 !important;
            margin-top:4px;
        }

        @media (max-width: 900px) {
            .block-container { padding-top:1rem; }
            .hero { padding:23px 21px; min-height:150px; }
            .hero-title { font-size:30px; }
            div[data-testid="stForm"] { margin-top:6vh; padding:24px 22px 21px 22px !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
