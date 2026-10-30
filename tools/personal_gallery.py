"""Barça Memories 2.0: private photo gallery, no data or Jira mutations.

Photos are read from Streamlit Secrets rather than the public GitHub repository.
The in-app password does NOT provide adequate privacy on its own. Restrict app
access with real organizational authentication before sharing private photos.
"""
import base64
from binascii import Error as Base64Error
from html import escape

import streamlit as st
from core.themes import is_preview_allowed

GALLERY_USER = "liana.hakobyan"

# Current standard FC Barcelona crest (vector SVG, transparent).
# Independent third-party image host; replace this URL with a locally licensed
# asset later if guaranteed offline availability is important.
BARCA_CREST_SVG_URL = "https://assets.footylogos.com/logos/fc-barcelona/fc-barcelona-logo-footylogos.svg"

# Existing secrets section (first four photos) and an independent extension
# section (the next four photos + cropped crest).
PHOTO_SECTIONS = ("blaugrana_gallery", "blaugrana_max_gallery")


def can_view_gallery(current_user):
    if not current_user:
        return False
    try:
        enabled = st.secrets.get("app", {}).get("enable_personal_gallery") is True
    except Exception:
        return False
    if not enabled:
        return False
    username = str(current_user.get("jira_username") or "").strip().casefold()
    return username == GALLERY_USER or is_preview_allowed(current_user)


def _section(name):
    try:
        return st.secrets.get(name, {}) or {}
    except Exception:
        return {}


def gallery_data_uri(key):
    """Return the approved crest URL or a validated private image data URL."""
    user = st.session_state.get("current_user") or {}
    if not st.session_state.get("logged_in") or not can_view_gallery(user):
        return ""
    if key == "crest_icon_b64":
        return BARCA_CREST_SVG_URL
    for section_name in PHOTO_SECTIONS:
        data = _section(section_name)
        encoded = data.get(key)
        if not isinstance(encoded, str) or not encoded or len(encoded) > 4_000_000:
            continue
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (Base64Error, ValueError):
            continue
        if raw.startswith(b"\xff\xd8\xff") and len(raw) <= 3_000_000:
            # Return the validated unchanged encoding, not arbitrary HTML.
            return "data:image/jpeg;base64," + encoded
    return ""


PHOTOS = [
    dict(key="shirts_b64", title="The Colors of History", tag="THE HERITAGE",
         number="01", caption="Every shirt carries a season. Every stripe holds a story.", category="Legacy"),
    dict(key="messi_b64", title="The Magic of Number 10", tag="THE LEGEND",
         number="02", caption="A number, a shirt, and football memories that refuse to fade.", category="Legends"),
    dict(key="kits_b64", title="Wear the Colors", tag="THE IDENTITY",
         number="03", caption="Blue and garnet, generation after generation.", category="Legacy"),
    dict(key="barca_wall_b64", title="Barça, Barça!", tag="THE SPIRIT",
         number="04", caption="More than a name. A feeling written on the walls.", category="Atmosphere"),
    dict(key="golden_era_b64", title="The Golden Years", tag="THE LEGACY",
         number="05", caption="Golden footballs and the number ten. A room full of memories.", category="Legends"),
    dict(key="trophies_b64", title="Made of Dreams", tag="THE GLORY",
         number="06", caption="The trophies shine. The stories behind them shine brighter.", category="Legends"),
    dict(key="crest_b64", title="One Badge. A Thousand Stories.", tag="THE CREST",
         number="07", caption="Some symbols say everything without a single word.", category="Legacy"),
    dict(key="portrait_b64", title="A Moment of Your Own", tag="YOUR MEMORY",
         number="08", caption="The best part of a journey is having been there.", category="Personal"),
]

# All CSS scoped to the gallery so the rest of Change Helper stays usable.
CSS = r"""
<style>
.bmx-hero {position:relative;isolation:isolate;overflow:hidden;min-height:292px;
 border-radius:28px;background:radial-gradient(ellipse at 100% 0%,#6a134b 0%,transparent 52%),
 linear-gradient(119deg,#101a40 3%,#1b1c50 55%,#4b0a38 100%);
 border:1px solid #d7ae62;box-shadow:0 23px 50px rgba(13,21,49,.20);
 padding:44px 48px;margin:0 0 24px;color:white}
.bmx-hero:before {content:"";position:absolute;inset:0 0 auto;height:5px;
 background:linear-gradient(90deg,#a50044 0%,#e4b458 25%,#2155a3 50%,#a50044 75%,#e4b458 100%)}
.bmx-hero .bmx-hero-crest{position:absolute;right:5%;top:5%;width:190px;height:215px;
 object-fit:contain;opacity:1;filter:drop-shadow(0 12px 30px #0008);
 border-radius:0;transform:none;border:0}
.bmx-hero-copy{position:relative;z-index:1;max-width:680px}
.bmx-overline {font-size:10px;font-weight:850;letter-spacing:.24em;color:#e8be69}
.bmx-hero h1{font-size:clamp(40px,6vw,76px);font-weight:900;line-height:1.02;
 letter-spacing:-.058em;margin:18px 0 16px;color:#fff}
.bmx-hero p{font-size:14px;line-height:1.85;color:#d6dbea;max-width:535px}
.bmx-pills{display:flex;gap:9px;margin-top:25px;flex-wrap:wrap}
.bmx-pill{border:1px solid #e8be6977;border-radius:999px;color:#e8be69;
 background:#ffffff12;font-size:10px;padding:8px 12px;font-weight:800;letter-spacing:.06em}
.bmx-line{display:flex;max-width:310px;gap:6px;margin-top:28px}
.bmx-line span{height:5px;border-radius:10px;flex:1;background:#a50044}
.bmx-line span:nth-child(2),.bmx-line span:nth-child(4){background:#2865be}
.bmx-line span:nth-child(5){background:#e8be69}
.bmx-intro{display:grid;grid-template-columns:1.4fr .6fr;gap:24px;margin:20px 0 27px;align-items:center}
.bmx-intro h2{font-size:clamp(24px,3vw,39px);font-weight:890;color:#171a3b;
 letter-spacing:-.04em;line-height:1.16;margin:10px 0}
.bmx-intro p{font-size:13px;line-height:1.85;color:#626b7c;max-width:550px}
.bmx-intro-quote{padding:22px;background:#151b46;border:1px solid #d7ae62;
 border-radius:19px;color:#fff;text-align:center}
.bmx-intro-quote strong{display:block;font-size:22px;color:#e8be69;line-height:1.25}
.bmx-intro-quote small{font-size:10px;letter-spacing:.14em;display:block;margin-top:8px;color:#d5daeb}
.bmx-label{font-size:10px;font-weight:850;color:#a50044;letter-spacing:.18em}
.bmx-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:17px;margin:15px 0 28px}
.bmx-card{min-width:0;overflow:hidden;border-radius:20px;background:#fff;
 border:1px solid #e8e0e9;box-shadow:0 8px 22px rgba(27,25,63,.06);
 transition:transform .18s ease, box-shadow .18s ease}
.bmx-card:hover{transform:translateY(-4px);box-shadow:0 15px 38px rgba(40,24,73,.16)}
.bmx-card.featured{grid-column:span 2;grid-row:span 2}
.bmx-card-img{position:relative;height:260px;overflow:hidden;background:#1a2142}
.bmx-card.featured .bmx-card-img{height:650px}
.bmx-card-img img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .35s ease}
.bmx-card:hover img{transform:scale(1.035)}
.bmx-numeral{position:absolute;top:14px;left:14px;color:#fff;background:#161d3acb;
 border:1px solid #e8be6977;border-radius:999px;font-size:10px;font-weight:900;
 padding:6px 10px;letter-spacing:.12em}
.bmx-card-body{padding:18px 20px 20px}
.bmx-tag{font-size:9px;letter-spacing:.15em;color:#a50044;font-weight:900;margin-bottom:7px}
.bmx-card h3{font-size:19px;color:#181a34;line-height:1.2;letter-spacing:-.025em;margin:0 0 6px;font-weight:850}
.bmx-card p{font-size:12px;color:#697083;line-height:1.65;margin:0}
.bmx-feature{position:relative;overflow:hidden;border-radius:22px;margin:23px 0;
 background:linear-gradient(110deg,#101c43,#430d38);border:1px solid #d7ae62;
 display:grid;grid-template-columns:1fr 1fr;min-height:290px}
.bmx-feature-photo{height:100%;min-height:280px;width:100%;object-fit:cover}
.bmx-feature-copy{padding:30px;align-self:center}
.bmx-feature-copy h2{font-size:clamp(23px,3vw,34px);line-height:1.18;letter-spacing:-.03em;
 font-weight:900;color:#fff;margin:12px 0}
.bmx-feature-copy p{font-size:13px;color:#dce0ec;line-height:1.75}
.bmx-bottom{padding:27px 32px;border-radius:22px;color:#fff;
 background:linear-gradient(120deg,#a50044 0%,#631045 40%,#163879 100%);
 border:1px solid #e8be6970;box-shadow:0 14px 30px #1e183827;margin:25px 0 8px}
.bmx-bottom strong{font-size:26px;font-weight:850;display:block;color:#fff;letter-spacing:-.03em}
.bmx-bottom span{font-size:12px;color:#edebf5;display:block;margin-top:6px}
.bmx-privacy{font-size:11px;color:#7e7987;line-height:1.65;margin:14px 0 32px}
@media(max-width:1120px){.bmx-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
 .bmx-card.featured{grid-row:span 1}.bmx-card.featured .bmx-card-img{height:340px}}
@media(max-width:690px){.bmx-hero{padding:28px 24px}.bmx-hero .bmx-hero-crest{width:95px;height:120px;right:0;top:20px;opacity:.25}
 .bmx-intro{grid-template-columns:1fr}.bmx-grid{grid-template-columns:1fr}
 .bmx-card.featured{grid-column:span 1}.bmx-card.featured .bmx-card-img{height:315px}
 .bmx-feature{grid-template-columns:1fr}.bmx-feature-photo{height:240px}}
@media(prefers-reduced-motion:reduce){.bmx-card,.bmx-card-img img{transition:none!important}.bmx-card:hover{transform:none}}
</style>
"""


def _card_html(entry, data_uri, featured=False):
    # All user-visible text comes from constants and is escaped for HTML safety.
    klass = "bmx-card featured" if featured else "bmx-card"
    return (f'<article class="{klass}"><div class="bmx-card-img">'
            f'<img src="{data_uri}" alt="{escape(entry["title"])}" loading="lazy">'
            f'<div class="bmx-numeral">{escape(entry["number"])}</div></div>'
            f'<div class="bmx-card-body"><div class="bmx-tag">{escape(entry["tag"])}</div>'
            f'<h3>{escape(entry["title"])}</h3><p>{escape(entry["caption"])}</p></div></article>')


def page_personal_gallery():
    user = st.session_state.get("current_user") or {}
    if not can_view_gallery(user):
        st.error("This gallery is not available for this account.")
        st.stop()

    st.markdown(CSS, unsafe_allow_html=True)
    crest = gallery_data_uri("crest_icon_b64") or gallery_data_uri("crest_b64")
    crest_html = f'<img class="bmx-hero-crest" src="{crest}" alt="FC Barcelona crest">' if crest else ''
    st.markdown(f"""<section class="bmx-hero">{crest_html}<div class="bmx-hero-copy">
       <div class="bmx-overline">✦ PERSONAL COLLECTION / FC BARCELONA</div>
       <h1>Barça Memories.</h1>
       <p>Eight frames. One unforgettable feeling. From legendary jerseys and the magic of number ten to trophies, colors, and the moments that make Barça more than a club.</p>
       <div class="bmx-pills"><span class="bmx-pill">MES QUE UN CLUB</span><span class="bmx-pill">NUMBER 10</span><span class="bmx-pill">BLAUGRANA FOREVER</span></div>
       <div class="bmx-line"><span></span><span></span><span></span><span></span><span></span></div>
       </div></section>""", unsafe_allow_html=True)

    personal_enabled = _section("blaugrana_gallery").get("show_personal_photo") is True
    entries = [item for item in PHOTOS if (item["category"] != "Personal" or personal_enabled)]
    available = [(entry, gallery_data_uri(entry["key"])) for entry in entries]
    available = [(entry, uri) for entry,uri in available if uri]
    if not available:
        st.info("Photos are not configured yet. Add the private photo sections to this TEST app's Streamlit Secrets.")
        return

    st.markdown("""<div class="bmx-intro"><div><span class="bmx-label">THE COLLECTION</span>
      <h2>Some colors never fade.</h2><p>This is a visual journey through a place where history lives in the shirts, the walls, and every piece of silverware.</p></div>
      <div class="bmx-intro-quote"><strong>Més que un club.</strong><small>MORE THAN A CLUB</small></div></div>""", unsafe_allow_html=True)

    choices = ["All moments", "Legends", "Legacy", "Atmosphere"]
    if personal_enabled:
        choices.append("Personal")
    selected = st.radio("Explore the collection", choices, horizontal=True, key="barca_moments_filter")
    chosen = [(entry, uri) for entry,uri in available if selected == "All moments" or entry["category"] == selected]
    if chosen:
        grid = ''.join(_card_html(entry, uri, featured=(selected == "All moments" and i == 0))
                       for i,(entry,uri) in enumerate(chosen))
        st.markdown('<div class="bmx-grid">'+grid+'</div>', unsafe_allow_html=True)
    else:
        st.info("No photos in this category yet.")

    # Additional cinematic player spotlight from an actual user-supplied museum photo.
    if selected in ("All moments", "Legends"):
        messi = gallery_data_uri("messi_b64")
        if messi:
            st.markdown(f"""<div class="bmx-feature"><div class="bmx-feature-copy">
                <span class="bmx-overline">THE NUMBER 10 / THE LEGEND</span>
                <h2>Not every legend needs an introduction.</h2>
                <p>A jersey, a number, and a chapter of football history written in blaugrana.</p>
                </div><img class="bmx-feature-photo" src="{messi}" alt="Museum exhibit celebrating the number 10"></div>""", unsafe_allow_html=True)
    st.markdown("""<div class="bmx-bottom"><strong>Visca el Barça. 💙❤️</strong>
       <span>For the stories worth remembering and the colors worth carrying.</span></div>""", unsafe_allow_html=True)
    st.markdown("""<p class="bmx-privacy">Private test gallery. Images come from private app configuration, not GitHub.
      Show identifiable personal photos only with the person’s permission. A password-only public app is not an access-controlled photo vault.</p>""", unsafe_allow_html=True)
