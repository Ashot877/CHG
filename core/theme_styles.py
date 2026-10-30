"""One reusable styling engine for all personalized editions.

This is additive CSS and does not modify any business or Jira logic.
"""
from string import Template
import streamlit as st

STYLE = Template(r"""
<style>
:root {
  --bg: $canvas;
  --surface-soft: $surface_soft;
  --sidebar: $sidebar_start;
  --sidebar-soft: $sidebar_end;
  --accent: $accent;
  --accent-dark: $accent_dark;
  --accent-soft: $surface_soft;
  --theme-blue: $blue;
  --theme-gold: $gold;
}
.stApp {
  background:
    radial-gradient(ellipse at 88% 3%, rgba($accent_rgb,.09), transparent 29rem),
    radial-gradient(ellipse at -5% 53%, rgba($accent_rgb,.025), transparent 34rem),
    linear-gradient(180deg, #fff 0%, $canvas 46%, $canvas 100%) !important;
}
section[data-testid="stSidebar"] {
  background:
    radial-gradient(circle at 115% 0%, rgba($accent_rgb,.30), transparent 265px),
    linear-gradient(165deg, $sidebar_start 0%, $sidebar_end 100%) !important;
  border-right: 1px solid rgba(255,255,255,.12) !important;
  box-shadow: 14px 0 36px rgba(18,20,38,.10) !important;
}
section[data-testid="stSidebar"] .brand-mark {
  background: linear-gradient(130deg,$accent 4%,$blue 96%) !important;
  border: 1px solid $gold !important;
  box-shadow: 0 9px 26px rgba($accent_rgb,.22) !important;
}
section[data-testid="stSidebar"] .brand-subtitle,
section[data-testid="stSidebar"] .nav-label { color: $gold !important; }
section[data-testid="stSidebar"] .user-chip {
  background: rgba(255,255,255,.045);
  border: 1px solid rgba(255,255,255,.14);
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
  background: rgba(255,255,255,.09) !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
  background: rgba($accent_rgb,.29) !important;
  border-color: rgba(255,255,255,.19) !important;
  box-shadow: inset 3px 0 0 $gold !important;
}
section[data-testid="stSidebar"] div.stButton > button {
  background: rgba(255,255,255,.06) !important;
  border-color: rgba(255,255,255,.19) !important;
}
section[data-testid="stSidebar"] div.stButton > button:hover {
  border-color: $gold !important;
  background: rgba(255,255,255,.13) !important;
}
.personal-welcome {
  position: relative;
  margin: 0 4px 19px;
  padding: 15px 14px 18px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,.20);
  background: linear-gradient(130deg, rgba($accent_rgb,.33), rgba(255,255,255,.055) 85%);
  box-shadow: 0 12px 28px rgba(10,12,27,.13);
  overflow: hidden;
}
.personal-welcome::after {
  content: '✦';
  position: absolute; right: 10px; top: 7px;
  font-size: 23px; color: $gold; opacity:.65;
}
.personal-welcome-kicker {
  font-size: 9px; letter-spacing:.135em; text-transform:uppercase;
  font-weight: 820; color: $gold; margin-bottom:9px;
}
.personal-welcome-title {
  color: #fff; font-size: 19px; font-weight:820; letter-spacing:-.025em;
}
.personal-welcome-note { color:#dedfed; font-size:11px; margin-top:7px; line-height:1.5; }
.personal-stripes { display:flex; gap:4px; margin-top:16px; }
.personal-stripes i { height:3px; flex:1; border-radius:999px; background: $accent; }
.personal-stripes i:nth-child(2),.personal-stripes i:nth-child(4) { background:$blue; }
.personal-stripes i:nth-child(5) { background:$gold; }
.hero {
  background:
    radial-gradient(circle at 88% 22%, rgba(255,255,255,.14), transparent 15rem),
    radial-gradient(circle at 62% 100%, rgba($accent_rgb,.30), transparent 18rem),
    linear-gradient(119deg,$hero_start 0%, $hero_end 100%) !important;
  border:1px solid $gold !important;
  border-radius:24px !important;
  box-shadow:0 19px 42px rgba(25,25,58,.16) !important;
  padding-right:150px !important;
}
.hero::before {
  content: ''; position:absolute; left:0; right:0; top:0; height:3px;
  background:linear-gradient(90deg,$blue,$accent,$gold);
}
.hero::after { border-color:rgba(255,255,255,.13) !important; }
.hero-eyebrow { color:$gold !important; }
.hero-subtitle { color:#e5dfea !important; }
.pill { border-color:rgba(255,255,255,.18) !important; }
.personal-edition-pill {
  color:$gold !important;
  background:rgba(255,255,255,.105) !important;
  border-color:$gold !important;
}
.personal-hero-stamp {
  position:absolute; right:33px; top:27px; z-index:2;
  height:84px; width:84px; display:flex; flex-direction:column;
  justify-content:center; align-items:center;
  border-radius:23px; transform:rotate(6deg);
  background:linear-gradient(135deg,rgba($accent_rgb,.34),rgba(255,255,255,.08));
  border:1px solid $gold;
  box-shadow:0 9px 25px rgba(5,7,22,.15);
}
.personal-hero-stamp strong { color:#fff; font-size:27px; letter-spacing:-.075em; line-height:1; }
.personal-hero-stamp small { color:$gold; font-size:8px; font-weight:800; letter-spacing:.15em; margin-top:6px; }
.section-card,.mini-card,.metric-card {
  border-color:rgba($accent_rgb,.15) !important;
  box-shadow:0 9px 28px rgba(30,24,57,.05) !important;
}
.mini-card { transition:transform .17s ease, box-shadow .17s ease; }
.mini-card:hover {
  transform:translateY(-3px);
  box-shadow:0 14px 32px rgba($accent_rgb,.10) !important;
}
.metric-card::before { background:linear-gradient(180deg,$accent,$blue,$gold) !important; }
button[kind="primary"],button[kind="primaryFormSubmit"] {
  background:linear-gradient(120deg,$accent,$accent_dark) !important;
  border-color:$accent !important;
}
button[kind="primary"]:hover,button[kind="primaryFormSubmit"]:hover {
  filter:brightness(1.06);
  box-shadow:0 8px 20px rgba($accent_rgb,.20) !important;
}
@media(max-width: 900px) {
  .hero { padding-right:22px !important; }
  .personal-hero-stamp { display:none; }
}
@media(prefers-reduced-motion:reduce) { .mini-card { transition:none; } .mini-card:hover { transform:none; } }
</style>
""")


def apply_personal_theme_styles(theme):
    if not theme or theme["id"] == "default":
        return
    st.markdown(STYLE.substitute(theme), unsafe_allow_html=True)
