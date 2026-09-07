import streamlit as st


def apply_styles():
    st.markdown(
        """
        <style>
        :root {
            --bg: #f4f7fb;
            --card: rgba(255,255,255,.92);
            --text: #0f172a;
            --muted: #64748b;
            --border: #dfe7f1;
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --soft-blue: #eff6ff;
            --soft-green: #ecfdf5;
            --soft-amber: #fffbeb;
            --soft-red: #fef2f2;
        }

        .stApp {
            background:
                radial-gradient(circle at 12% -10%, rgba(37,99,235,.09), transparent 28%),
                radial-gradient(circle at 90% 5%, rgba(124,58,237,.06), transparent 24%),
                var(--bg);
            color: var(--text);
        }
        .block-container { padding-top: 1.15rem; padding-bottom: 2.4rem; max-width: 1540px; }

        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b1220 0%, #111827 100%);
            border-right: 1px solid rgba(255,255,255,.08);
        }
        div[data-testid="stSidebar"] * { color: #e5e7eb; }
        div[data-testid="stSidebar"] [data-testid="stRadio"] label { color: #e5e7eb !important; }

        .hero {
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, rgba(255,255,255,.98), rgba(248,250,252,.94));
            padding: 28px 30px;
            border-radius: 26px;
            border: 1px solid rgba(203,213,225,.75);
            box-shadow: 0 18px 50px rgba(15,23,42,.07);
            margin-bottom: 18px;
        }
        .hero:before {
            content: "";
            position: absolute;
            width: 330px;
            height: 330px;
            right: -130px;
            top: -190px;
            background: radial-gradient(circle, rgba(37,99,235,.18), rgba(37,99,235,0));
            border-radius: 999px;
        }
        .hero-title {
            position: relative;
            font-size: 38px;
            line-height: 1.05;
            font-weight: 850;
            letter-spacing: -0.04em;
            color: var(--text);
            margin-bottom: 8px;
        }
        .hero-subtitle { position: relative; font-size: 15px; color: var(--muted); max-width: 820px; }
        .pill-row { position: relative; margin-top: 16px; display: flex; gap: 8px; flex-wrap: wrap; }
        .pill {
            background: rgba(255,255,255,.88);
            color: #334155;
            border: 1px solid var(--border);
            padding: 7px 11px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
        }

        .section-card {
            background: var(--card);
            backdrop-filter: blur(8px);
            border: 1px solid var(--border);
            border-radius: 22px;
            box-shadow: 0 10px 30px rgba(15,23,42,.045);
            padding: 20px 22px;
            margin-bottom: 16px;
        }
        .mini-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 18px;
            box-shadow: 0 7px 24px rgba(15,23,42,.04);
            height: 100%;
        }
        .tool-card-title { font-size: 18px; font-weight: 800; color: var(--text); margin-bottom: 5px; }
        .tool-card-text { font-size: 13px; color: var(--muted); line-height: 1.5; }

        .metric-card {
            background: rgba(255,255,255,.92);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 14px 16px;
            min-height: 88px;
            box-shadow: 0 5px 18px rgba(15,23,42,.035);
            text-align: center;
        }
        .metric-number { color: var(--primary); font-size: 24px; font-weight: 850; word-break: break-word; }
        .metric-label { color: var(--muted); font-size: 12px; font-weight: 700; }

        .group-title { font-size: 17px; font-weight: 800; color: var(--text); margin-bottom: 3px; }
        .group-subtitle { font-size: 12px; color: var(--muted); margin-bottom: 10px; }
        .footer-note { color: #94a3b8; font-size: 12px; margin-top: 18px; }

        .maintenance-banner {
            border: 1px solid #bfdbfe;
            background: linear-gradient(135deg, #eff6ff, #f8fafc);
            border-radius: 18px;
            padding: 16px 18px;
            margin: 10px 0 16px 0;
        }
        .maintenance-title { color: #1e3a8a; font-weight: 800; font-size: 16px; margin-bottom: 4px; }
        .maintenance-text { color: #475569; font-size: 13px; line-height: 1.5; }

        .login-shell { min-height: 58vh; display: flex; align-items: end; justify-content: center; }
        .login-card {
            width: 100%; max-width: 560px; background: rgba(255,255,255,.96);
            border: 1px solid var(--border); border-radius: 28px;
            box-shadow: 0 28px 80px rgba(15,23,42,.13); padding: 30px;
        }
        .login-icon {
            width: 56px; height: 56px; border-radius: 18px; display: grid; place-items: center;
            background: linear-gradient(135deg, #2563eb, #7c3aed); color: white; font-size: 26px; margin-bottom: 16px;
        }
        .login-title { color: var(--text); font-size: 32px; line-height: 1.05; font-weight: 850; letter-spacing: -0.03em; margin-bottom: 8px; }
        .login-subtitle { color: var(--muted); font-size: 14px; margin-bottom: 20px; }

        div.stButton > button, div[data-testid="stDownloadButton"] > button {
            border-radius: 12px;
            min-height: 42px;
            font-weight: 700;
        }
        div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
            border-radius: 12px;
        }
        div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
            border-radius: 14px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
