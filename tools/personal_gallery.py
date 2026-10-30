"""Private, persistent, account-scoped photo gallery for Change Helper.

Photographs are loaded from Streamlit Cloud Secrets, NOT from the GitHub repo.
This is a visual feature only. Actual access requires secure application authentication
and viewer access restrictions; the basic password login is insufficient by itself.
"""
import base64
from binascii import Error as Base64Error
from html import escape
import streamlit as st
from core.themes import is_preview_allowed

GALLERY_USER = "liana.hakobyan"
SECRETS_SECTION = "blaugrana_gallery"


def can_view_gallery(current_user):
    """Show the menu only for the intended user and allowlisted design testers."""
    if not current_user:
        return False
    try:
        enabled = bool(st.secrets.get("app", {}).get("enable_personal_gallery", False))
    except Exception:
        return False
    if not enabled:
        return False
    username = str(current_user.get("jira_username") or "").strip().casefold()
    return username == GALLERY_USER or is_preview_allowed(current_user)


def _photo(section, key):
    """Base64 bytes from an app secret. Never print the value or cache globally."""
    encoded = str(section.get(key, "") or "")
    if not encoded:
        return None
    try:
        raw = base64.b64decode(encoded, validate=True)
        # Avoid excessive memory use from malformed or oversized configuration.
        return raw if raw.startswith(b"\xff\xd8\xff") and len(raw) <= 3_000_000 else None
    except (ValueError, Base64Error):
        return None


CSS = """
<style>
.bm-head {
  position:relative; overflow:hidden;
  padding:39px 43px 43px;
  border-radius:26px;
  background:radial-gradient(circle at 83% 5%,rgba(231,178,78,.20),transparent 300px),
             radial-gradient(circle at -15% 120%,rgba(192,21,85,.34),transparent 360px),
             linear-gradient(112deg,#111936 0%,#141B48 55%,#4A103B 100%);
  border:1px solid rgba(233,190,109,.55); color:white;
  box-shadow:0 20px 55px rgba(20,23,54,.18); margin-bottom:22px;
}
.bm-head::after { content:'10'; position:absolute; right:30px; bottom:-80px;
  font-size:245px; font-weight:900; letter-spacing:-.11em; color:rgba(255,255,255,.036);
  pointer-events:none; }
.bm-kicker {color:#E8BE69; text-transform:uppercase; font-size:10px; letter-spacing:.23em; font-weight:900;}
.bm-title {font-size:clamp(34px,5vw,61px); line-height:1; font-weight:900;
  letter-spacing:-.05em; color:#fff; margin:14px 0 14px; position:relative;z-index:1}
.bm-sub {font-size:14px; color:#D7DBED; max-width:630px; line-height:1.8; position:relative;z-index:1}
.bm-stripe {display:flex; width:min(260px,100%); gap:6px; margin-top:23px; position:relative;z-index:1}
.bm-stripe i {height:5px; flex:1; border-radius:6px; background:#A50044; }
.bm-stripe i:nth-child(2),.bm-stripe i:nth-child(4) {background:#2563BB;}
.bm-stripe i:last-child {background:#E8BE69;}
.bm-kicktitle {font-size:11px;letter-spacing:.16em;text-transform:uppercase;font-weight:850;color:#A50044;margin:14px 0 7px}
.bm-editorial {font-size:clamp(25px,3vw,36px);font-weight:880;line-height:1.14;letter-spacing:-.035em;color:#171B2F;margin:5px 0 12px}
.bm-body {font-size:14px;line-height:1.8;color:#687084;}
.bm-stat {border:1px solid #EAE2EC;border-radius:15px;padding:13px 16px;
    color:#32334D;background:#FFF;box-shadow:0 8px 22px rgba(33,16,45,.035);}
.bm-stat strong {display:block;font-size:20px;color:#A50044;}
.bm-stat small {color:#72738B;font-size:10px;text-transform:uppercase;font-weight:750;letter-spacing:.09em}
.bm-gallery-title {font-size:22px;line-height:1.2;font-weight:850;color:#171A2D;margin:20px 0 7px;}
.bm-photo-caption {font-size:12px;letter-spacing:.02em;color:#64677A;margin:7px 0 22px;line-height:1.6}
.bm-private {font-size:12px;color:#767687;padding-top:18px;line-height:1.8}
.bm-foot {margin:28px 0 0;padding:25px 27px;border-radius:21px;color:#fff;
  background:linear-gradient(110deg,#A50044 0%,#60205E 50%,#1B3375 100%);}
.bm-foot strong {font-size:24px;letter-spacing:-.025em;display:block;margin-bottom:6px;}
.bm-foot span {font-size:13px;color:#F1E5EF;}
@media (max-width:800px) {.bm-head {padding:26px 23px 30px;} .bm-head::after {font-size:150px;right:15px;bottom:-35px}}
@media (prefers-reduced-motion:reduce) {.bm-head,.bm-foot {scroll-behavior:auto}}
</style>
"""


def page_personal_gallery():
    current_user = st.session_state.get("current_user") or {}
    if not can_view_gallery(current_user):
        st.error("This gallery is not available for this account.")
        st.stop()

    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("""<div class="bm-head"><div class="bm-kicker">✦ Personal collection / FC Barcelona</div>
      <div class="bm-title">Barça Memories.</div>
      <div class="bm-sub">A journey through the colors, the history and the moments that stay with us.
      A little corner of Barcelona, inside Change Helper.</div>
      <div class="bm-stripe"><i></i><i></i><i></i><i></i><i></i></div></div>""", unsafe_allow_html=True)

    try:
        gallery = st.secrets.get(SECRETS_SECTION, {})
    except Exception:
        gallery = {}

    wall = _photo(gallery, "shirts_b64")
    messi = _photo(gallery, "messi_b64")
    shop = _photo(gallery, "kits_b64")
    portrait = _photo(gallery, "portrait_b64") if gallery.get("show_personal_photo", False) else None

    if not any((wall, messi, shop)):
        st.info("The gallery is ready. Add the private [blaugrana_gallery] photo section in the TEST app's Streamlit Secrets to display the photographs.")
        return

    left, right = st.columns([1.20, 1], gap="large")
    with left:
        if wall:
            st.image(wall, use_container_width=True)
            st.markdown('<div class="bm-photo-caption">01 / The colors of history · A wall of legendary Barça jerseys</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="bm-kicktitle">Més que un club</div>', unsafe_allow_html=True)
        st.markdown('<div class="bm-editorial">Some colors mean more than words.</div>', unsafe_allow_html=True)
        st.markdown('<div class="bm-body">From the iconic stripes to the legendary number ten, every jersey carries a story. This is a small collection of moments worth keeping.</div>', unsafe_allow_html=True)
        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="bm-stat"><strong>1899</strong><small>Since the beginning</small></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="bm-stat"><strong>10</strong><small>Iconic memories</small></div>', unsafe_allow_html=True)
        if portrait:
            st.write("")
            st.image(portrait, use_container_width=True)
            st.markdown('<div class="bm-photo-caption">A moment from the visit · Personal photograph</div>', unsafe_allow_html=True)

    st.markdown('<div class="bm-gallery-title">Inside the Barça universe</div>', unsafe_allow_html=True)
    st.markdown('<div class="bm-body">Three frames, one story: football, history, and the feeling of being there.</div>', unsafe_allow_html=True)
    g1, g2 = st.columns(2, gap="large")
    if messi:
        with g1:
            st.image(messi, use_container_width=True)
            st.markdown('<div class="bm-photo-caption"><strong>02 / Number Ten</strong> · A tribute to an unforgettable era</div>', unsafe_allow_html=True)
    if shop:
        with g2:
            st.image(shop, use_container_width=True)
            st.markdown('<div class="bm-photo-caption"><strong>03 / Blaugrana, always</strong> · The new colors on display</div>', unsafe_allow_html=True)

    st.markdown("""<div class="bm-foot"><strong>Visca el Barça. Visca Catalunya.</strong>
        <span>Made for the moments that deserve their own page.</span></div>""", unsafe_allow_html=True)
    st.markdown("""<div class="bm-private">Personal gallery · Photos are read from private app settings,
    not uploaded to GitHub. Page access in the UI does not replace organization-managed authentication
    and deployment-level access restrictions.</div>""", unsafe_allow_html=True)
