"""Optional private-video page for the Change Helper personal theme test app.

The video is never bundled or written to permanent storage by this module.
"""
from html import escape
import streamlit as st
from core.themes import is_preview_allowed


def can_view_moments(current_user=None):
    """Feature flag + account filter. Not a substitute for SSO or access control."""
    if not current_user:
        return False
    try:
        enabled = st.secrets.get('app', {}).get('enable_personal_moments', False)
    except Exception:
        enabled = False
    if not enabled:
        return False
    username = str(current_user.get('jira_username') or '').strip().casefold()
    return username == 'liana.hakobyan' or is_preview_allowed(current_user)


CSS = r"""
<style>
.bm-header {
  position: relative; overflow: hidden;
  background: radial-gradient(circle at 90% 5%, rgba(213,177,99,.25), transparent 260px),
              linear-gradient(115deg, #111b44 0%, #26163e 52%, #640c3c 100%);
  color: #fff; border-radius: 24px; padding: 34px 40px 37px;
  border: 1px solid rgba(222,186,119,.5);
  box-shadow: 0 22px 48px rgba(34,17,68,.18);
}
.bm-header:after {
  content: ''; position:absolute; right:-100px; top:-190px; width:430px; height:430px;
  border-radius: 50%; border: 1px solid rgba(255,255,255,.13);
  box-shadow: 0 0 0 38px rgba(255,255,255,.035),0 0 0 85px rgba(255,255,255,.02);
}
.bm-eyebrow {font-size:11px;letter-spacing:.22em;color:#e8be69;font-weight:850;text-transform:uppercase;}
.bm-headline {font-size:clamp(32px,4vw,54px);font-weight:850;letter-spacing:-.045em;line-height:1.1;margin:12px 0;max-width:740px;}
.bm-subline {font-size:15px;color:#e2dbea;max-width:650px;line-height:1.6;}
.bm-stripe {display:flex;gap:5px;width:min(260px,80%);margin-top:22px;height:5px;}
.bm-stripe i {flex:1;background:#A50044;border-radius:9px}
.bm-stripe i:nth-child(2),.bm-stripe i:nth-child(4) {background:#2456a6}
.bm-stripe i:last-child {background:#e8be69}
.bm-info {margin:25px 0 12px;background:#fff;border:1px solid #e9dfed;border-radius:18px;padding:20px 24px;}
.bm-info strong {display:block;color:#27193a;font-size:18px;margin-bottom:5px}
.bm-info p {font-size:13px;color:#6d6776;margin:0;line-height:1.6}
.bm-smallnote {font-size:12px;color:#76717f;padding-top:8px;line-height:1.6}
.bm-frame {padding:8px;border-radius:22px;background:linear-gradient(135deg,#a50044,#214e99,#e8be69);}
.bm-frame-inner {padding:10px;background:#11182a;border-radius:17px}
@media(max-width:750px) {.bm-header {padding:25px 22px}.bm-info {padding:17px}}
</style>
"""


def page_blaugrana_moments():
    if not can_view_moments(st.session_state.get('current_user')):
        st.error('This page is not available for this account.')
        st.stop()
    user = st.session_state.get('current_user') or {}
    display_name = escape(str(user.get('display_name') or 'Fan'))
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        f'''<div class="bm-header">
          <div class="bm-eyebrow">✦ Personal Edition / 1899</div>
          <div class="bm-headline">Blaugrana Moments.</div>
          <div class="bm-subline">A little piece of Barcelona, right inside your workspace.<br>
          Moments worth remembering, {display_name}.</div>
          <div class="bm-stripe" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>
        </div>''', unsafe_allow_html=True
    )
    st.markdown('''<div class="bm-info"><strong>🎞 A night in Barcelona</strong>
       <p>Stadium views, trophies, the colors of the club. Add your video to relive the trip.
       Playback begins only when you press Play.</p></div>''', unsafe_allow_html=True)

    left, center, right = st.columns([1, 2.1, 1])
    with center:
        st.caption('YOUR VIDEO / VERTICAL REEL')
        uploaded = st.file_uploader(
            'Choose a video from your device',
            type=['mp4', 'mov', 'm4v'],
            key='blaugrana_video_upload',
            help='The selected file is used only for playback in this session, not saved to GitHub.',
        )
        if uploaded is not None:
            st.video(uploaded, format='video/mp4', autoplay=False, loop=False)
            st.caption("Press play to watch your Barça moment. If it doesn't play, use an H.264 MP4 version.")
        else:
            st.markdown('''<div class="bm-frame"><div class="bm-frame-inner" style="min-height:260px;
               display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;
               background:radial-gradient(circle at 50% 20%,#333061,#0e1529 70%);color:white;">
               <div style="font-size:52px;">⚽</div><div style="font-size:20px;font-weight:800;margin-top:13px;">Your moment belongs here</div>
               <div style="font-size:12px;color:#d2c9e8;margin-top:7px;">Choose a video above to start watching</div>
               </div></div>''', unsafe_allow_html=True)
    st.markdown('''<div class="bm-smallnote">Private preview: this feature does not commit video to GitHub or
    permanently store it. Streamlit temporarily processes the uploaded file in the active session.
    Share another person's footage in a team application only with their permission.</div>''', unsafe_allow_html=True)
