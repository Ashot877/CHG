import streamlit as st


def get_all_secrets() -> dict:
    try:
        return dict(st.secrets)
    except Exception:
        return {}

SECRETS = get_all_secrets()
APP_CONFIG = dict(SECRETS.get("app", {})) if SECRETS.get("app") else {}
JIRA_CONFIG = dict(SECRETS.get("jira", {})) if SECRETS.get("jira") else {}
MANUAL_FIELDS_CONFIG = dict(SECRETS.get("manual_field_ids", {})) if SECRETS.get("manual_field_ids") else {}
PARTNER_TIER_CONFIG = dict(SECRETS.get("partner_tier", {})) if SECRETS.get("partner_tier") else {}

JIRA_BASE_URL = APP_CONFIG.get("jira_base_url") or JIRA_CONFIG.get("base_url", "https://jirasd.digitain.com")
API_VERSION = str(JIRA_CONFIG.get("api_version", "2"))
AUTH_TYPE = JIRA_CONFIG.get("auth_type", "Basic")
USER_PAYLOAD_TYPE = JIRA_CONFIG.get("user_payload_type", "name")
VERIFY_JIRA_ON_LOGIN = bool(APP_CONFIG.get("verify_jira_on_login", True))
APP_TITLE = APP_CONFIG.get("title", "Change Helper")
APP_SUBTITLE = APP_CONFIG.get(
    "subtitle",
    "Daily Change Management workspace for handovers, weekly follow-up, data maintenance, ROX, and Excel utilities.",
)

MANUAL_FIELD_IDS = {
    "Internal Reporter": MANUAL_FIELDS_CONFIG.get("internal_reporter", ""),
    "Waiting information from": MANUAL_FIELDS_CONFIG.get("waiting_information_from", ""),
}

def load_app_users() -> dict:
    """Return users indexed by login password."""
    raw_users = SECRETS.get("users", {})
    users_by_password = {}

    # secrets.toml format:
    # [users.ashot]
    # password = "1111"
    # display_name = "Ashot"
    # jira_auth_type = "Bearer"
    # jira_username = "ashot.mkrtchyan"
    # jira_token = "..."
    # default_current_person = "ashot.mkrtchyan"
    for user_key, raw_config in dict(raw_users).items():
        config = dict(raw_config)
        password = str(config.get("password", "")).strip()
        if not password:
            continue
        config.setdefault("display_name", user_key)
        config.setdefault("jira_auth_type", AUTH_TYPE)
        config.setdefault("user_payload_type", USER_PAYLOAD_TYPE)
        users_by_password[password] = config

    return users_by_password

APP_USERS = load_app_users()
