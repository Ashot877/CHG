"""Visual themes for all Change Helper users. Not an authorization system.

To add an edition for a new colleague:
  1. Add its palette and copy to THEMES (using the same field names).
  2. Map Jira username in USER_DEFAULT_THEMES, or put `theme = "id"` in
     that user's Streamlit Cloud Secrets entry.
No app.py, UI, or tool logic needs to change.
"""
import streamlit as st

THEMES = {
    "default": {"id": "default", "name": "Classic", "badge": "", "monogram": "CH", "note": ""},
    "blaugrana": {
        "id": "blaugrana", "name": "Blaugrana · Liana Edition",
        "badge": "Blaugrana Edition", "monogram": "LH",
        "note": "A little color for the busiest days.",
        "accent": "#A50044", "accent_dark": "#7A0033", "accent_rgb": "165,0,68",
        "blue": "#2155A3", "gold": "#E8BE69",
        "sidebar_start": "#101A40", "sidebar_end": "#351735",
        "hero_start": "#111C47", "hero_end": "#550D37",
        "canvas": "#F7F5FA", "surface_soft": "#FBF8FD",
    },
    "aurora": {
        # An optional, unassigned example proving the same engine works for anyone.
        "id": "aurora", "name": "Aurora · Example Edition",
        "badge": "Aurora Edition", "monogram": "CH",
        "note": "Your workspace, your rhythm.",
        "accent": "#2563EB", "accent_dark": "#1D4ED8", "accent_rgb": "37,99,235",
        "blue": "#0D9488", "gold": "#84E1D1",
        "sidebar_start": "#0F172A", "sidebar_end": "#173A50",
        "hero_start": "#14233A", "hero_end": "#125B5C",
        "canvas": "#F3F7FA", "surface_soft": "#F7FBFC",
    },
}

# Current account-based defaults. Others remain unchanged.
USER_DEFAULT_THEMES = {"liana.hakobyan": "blaugrana"}


def _normalized(value):
    return str(value or "").strip().casefold()


def assigned_theme_id(current_user):
    if not current_user:
        return "default"
    configured = _normalized(current_user.get("theme"))
    if configured in THEMES:
        return configured
    username = _normalized(current_user.get("jira_username"))
    return USER_DEFAULT_THEMES.get(username, "default")


def is_preview_allowed(current_user):
    """Only specifically allowlisted usernames can preview visual themes."""
    if not current_user:
        return False
    try:
        cfg = st.secrets.get("app", {})
        if not cfg.get("enable_theme_preview", False):
            return False
        allowlist = cfg.get("theme_preview_users", [])
        if not isinstance(allowlist, (list, tuple)):
            return False
        return _normalized(current_user.get("jira_username")) in {
            _normalized(name) for name in allowlist
        }
    except Exception:
        return False


def get_active_theme():
    if not st.session_state.get("logged_in"):
        return THEMES["default"]
    user = st.session_state.get("current_user")
    assigned = assigned_theme_id(user)
    if is_preview_allowed(user):
        preview = _normalized(st.session_state.get("theme_preview"))
        if preview in THEMES:
            return THEMES[preview]
    return THEMES[assigned]
