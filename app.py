import base64
import json
import re
import zipfile
from collections import defaultdict
from io import BytesIO

import pandas as pd
import requests
import streamlit as st
from requests.auth import HTTPBasicAuth


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Change Helper",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# SAFE CONFIG FROM .streamlit/secrets.toml
# =========================================================
def get_all_secrets() -> dict:
    try:
        return dict(st.secrets)
    except Exception:
        return {}


SECRETS = get_all_secrets()
APP_CONFIG = dict(SECRETS.get("app", {})) if SECRETS.get("app") else {}
JIRA_CONFIG = dict(SECRETS.get("jira", {})) if SECRETS.get("jira") else {}
MANUAL_FIELDS_CONFIG = dict(SECRETS.get("manual_field_ids", {})) if SECRETS.get("manual_field_ids") else {}

JIRA_BASE_URL = APP_CONFIG.get("jira_base_url") or JIRA_CONFIG.get("base_url", "https://jirasd.digitain.com")
API_VERSION = str(JIRA_CONFIG.get("api_version", "2"))
AUTH_TYPE = JIRA_CONFIG.get("auth_type", "Basic")
USER_PAYLOAD_TYPE = JIRA_CONFIG.get("user_payload_type", "name")
VERIFY_JIRA_ON_LOGIN = bool(APP_CONFIG.get("verify_jira_on_login", True))
APP_TITLE = APP_CONFIG.get("title", "Change Helper")
APP_SUBTITLE = APP_CONFIG.get(
    "subtitle",
    "AM Handover, ROX Domain Grouper, and Excel Splitter in one clean workspace.",
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


# =========================================================
# CSS
# =========================================================
st.markdown(
    """
    <style>
    :root {
        --bg: #f5f7fb;
        --card: #ffffff;
        --text: #0f172a;
        --muted: #64748b;
        --border: #e2e8f0;
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --soft-blue: #eff6ff;
        --soft-green: #ecfdf5;
        --soft-purple: #f5f3ff;
        --danger: #ef4444;
    }

    .stApp { background: var(--bg); }
    .block-container { padding-top: 1.1rem; padding-bottom: 2rem; max-width: 1500px; }

    div[data-testid="stSidebar"] {
        background: #0f172a;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    div[data-testid="stSidebar"] * { color: #e5e7eb; }
    div[data-testid="stSidebar"] .stRadio label { color: #e5e7eb !important; }

    .hero {
        position: relative;
        overflow: hidden;
        background: radial-gradient(circle at top left, #dbeafe 0, transparent 34%),
                    linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        padding: 26px 30px;
        border-radius: 24px;
        border: 1px solid var(--border);
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
        margin-bottom: 18px;
    }
    .hero:after {
        content: "";
        position: absolute;
        width: 240px;
        height: 240px;
        right: -80px;
        top: -90px;
        background: rgba(37, 99, 235, .12);
        border-radius: 999px;
    }
    .hero-title {
        font-size: 38px;
        line-height: 1.05;
        font-weight: 900;
        letter-spacing: -0.04em;
        color: var(--text);
        margin-bottom: 8px;
    }
    .hero-subtitle {
        font-size: 15px;
        color: var(--muted);
        max-width: 760px;
    }
    .pill-row { margin-top: 16px; display: flex; gap: 8px; flex-wrap: wrap; }
    .pill {
        background: #ffffff;
        color: #334155;
        border: 1px solid var(--border);
        padding: 7px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
    }

    .login-shell {
        min-height: 72vh;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .login-card {
        width: 100%;
        max-width: 520px;
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: 28px;
        box-shadow: 0 24px 70px rgba(15, 23, 42, .14);
        padding: 30px;
    }
    .login-icon {
        width: 54px;
        height: 54px;
        border-radius: 18px;
        display: grid;
        place-items: center;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        color: white;
        font-size: 26px;
        margin-bottom: 16px;
    }
    .login-title {
        color: var(--text);
        font-size: 32px;
        line-height: 1.05;
        font-weight: 900;
        letter-spacing: -0.03em;
        margin-bottom: 8px;
    }
    .login-subtitle { color: var(--muted); font-size: 14px; margin-bottom: 20px; }

    .section-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 22px;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
        padding: 20px 22px;
        margin-bottom: 16px;
    }
    .mini-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
        height: 100%;
    }
    .tool-card-title { font-size: 18px; font-weight: 850; color: var(--text); margin-bottom: 4px; }
    .tool-card-text { font-size: 13px; color: var(--muted); }

    .metric-card {
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 14px 16px;
        min-height: 88px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        text-align: center;
    }
    .metric-number {
        color: var(--primary);
        font-size: 24px;
        font-weight: 900;
        word-break: break-word;
    }
    .metric-label { color: var(--muted); font-size: 12px; font-weight: 700; }

    .group-title { font-size: 17px; font-weight: 900; color: var(--text); margin-bottom: 3px; }
    .group-subtitle { font-size: 12px; color: var(--muted); margin-bottom: 10px; }

    .footer-note { color: #94a3b8; font-size: 12px; margin-top: 18px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# JIRA HELPERS
# =========================================================
class JiraAuthError(Exception):
    pass


def clean_base_url(url: str) -> str:
    return (url or "").strip().rstrip("/")


def build_auth(auth_type: str, username: str, token: str):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    auth = None
    auth_type = (auth_type or "Basic").strip()
    username = (username or "").strip()
    token = (token or "").strip()

    if auth_type == "Basic":
        auth = HTTPBasicAuth(username, token)
    elif auth_type == "Bearer":
        headers["Authorization"] = f"Bearer {token}"
    else:
        raise Exception(f"Unsupported auth type: {auth_type}")

    return headers, auth


def jira_request(method, base_url, api_version, auth_type, username, token, path, **kwargs):
    base_url = clean_base_url(base_url)
    headers, auth = build_auth(auth_type, username, token)
    url = f"{base_url}/rest/api/{api_version}{path}"

    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        auth=auth,
        timeout=45,
        **kwargs,
    )

    if response.status_code == 401:
        if auth_type == "Basic":
            hint = (
                "Jira returned 401 Unauthorized. App password only opens Change Helper; "
                "Jira needs real Jira credentials. For Basic, jira_token must be the real Jira password. "
                "If you use PAT, set jira_auth_type to Bearer."
            )
        else:
            hint = (
                "Jira returned 401 Unauthorized. For Bearer, jira_token must be a valid Jira PAT. "
                "The login password is not a Jira token. Tiny naming issue, enormous disaster."
            )
        raise JiraAuthError(f"{hint}\n\nAuth type: {auth_type}\nUsername: {username or '-'}\nEndpoint: {url}")

    if not response.ok:
        text = response.text or ""
        raise Exception(f"{response.status_code}: {text[:1200]}")

    if response.text.strip():
        try:
            return response.json()
        except Exception:
            return response.text

    return None


def jira_get_myself(base_url, api_version, auth_type, username, token):
    return jira_request("GET", base_url, api_version, auth_type, username, token, "/myself")


def jira_get_fields(base_url, api_version, auth_type, username, token):
    return jira_request("GET", base_url, api_version, auth_type, username, token, "/field")


def jira_search(base_url, api_version, auth_type, username, token, jql, fields):
    all_issues = []
    start_at = 0
    max_results = 100

    while True:
        data = jira_request(
            "GET",
            base_url,
            api_version,
            auth_type,
            username,
            token,
            "/search",
            params={
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": ",".join([f for f in fields if f]),
            },
        )

        issues = data.get("issues", [])
        total = data.get("total", 0)
        all_issues.extend(issues)
        start_at += max_results

        if start_at >= total or not issues:
            break

    return all_issues



def summarize_exception(error, limit=520):
    """Return a short readable Jira error. Keeps the UI calm instead of screaming HTML at people."""
    text = str(error or "").strip()
    if not text:
        return "Unknown error"

    json_start = text.find("{")
    if json_start != -1:
        try:
            payload = json.loads(text[json_start:])
            messages = payload.get("errorMessages") or []
            errors = payload.get("errors") or {}
            parts = []
            if messages:
                parts.extend([str(item) for item in messages if item])
            if errors:
                parts.extend([f"{key}: {value}" for key, value in errors.items()])
            if parts:
                text = "; ".join(parts)
        except Exception:
            pass

    text = re.sub(r"<[^>]+>", " ", text)
    text = " ".join(text.split())
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def jira_user_picker_search(base_url, api_version, auth_type, username, token, query, max_results=20):
    query = (query or "").strip()
    if not query:
        return []

    data = jira_request(
        "GET",
        base_url,
        api_version,
        auth_type,
        username,
        token,
        "/user/picker",
        params={"query": query, "maxResults": max_results},
    )

    users = data.get("users", []) if isinstance(data, dict) else []
    result = []
    seen = set()
    for user in users:
        clean_user = {
            "displayName": user.get("displayName") or user.get("name") or user.get("key") or "",
            "name": user.get("name") or "",
            "key": user.get("key") or "",
            "accountId": user.get("accountId") or "",
            "emailAddress": user.get("emailAddress") or "",
        }
        identifier = clean_user.get("name") or clean_user.get("key") or clean_user.get("accountId") or clean_user.get("displayName")
        if not identifier:
            continue
        dedupe_key = identifier.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        result.append(clean_user)
    return result


def user_identifier_for_payload(user, user_payload_type):
    if not isinstance(user, dict):
        return ""
    preferred = user.get(user_payload_type)
    if preferred:
        return str(preferred)
    for key in ["name", "key", "accountId", "emailAddress", "displayName"]:
        value = user.get(key)
        if value:
            return str(value)
    return ""


def user_suggestion_label(user, user_payload_type):
    identifier = user_identifier_for_payload(user, user_payload_type)
    display_name = user.get("displayName") or identifier
    if display_name and identifier and display_name != identifier:
        return f"{display_name}  ·  {identifier}"
    return identifier or display_name or "Unknown user"


def jira_jql_field_suggestions(base_url, api_version, auth_type, username, token, field_name, field_value, max_results=20):
    field_value = (field_value or "").strip()
    if not field_value:
        return []

    data = jira_request(
        "GET",
        base_url,
        api_version,
        auth_type,
        username,
        token,
        "/jql/autocompletedata/suggestions",
        params={"fieldName": field_name, "fieldValue": field_value, "maxResults": max_results},
    )

    raw_results = []
    if isinstance(data, dict):
        raw_results = data.get("results") or data.get("suggestions") or []
    elif isinstance(data, list):
        raw_results = data

    suggestions = []
    seen = set()
    for item in raw_results:
        if isinstance(item, dict):
            value = str(item.get("value") or item.get("name") or item.get("displayName") or "").strip()
            display_name = str(item.get("displayName") or item.get("label") or value).strip()
        else:
            value = str(item).strip()
            display_name = value
        if not value:
            continue
        clean_value = value.strip('"')
        dedupe_key = clean_value.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        suggestions.append({"value": clean_value, "displayName": display_name or clean_value})
        if len(suggestions) >= max_results:
            break
    return suggestions


def suggestion_label(item):
    value = item.get("value", "")
    display_name = item.get("displayName") or value
    if display_name and value and display_name != value:
        return f"{display_name}  ·  {value}"
    return value or display_name


def append_values_to_text_area(existing_text, values):
    existing = parse_projects(existing_text)
    seen = {item.lower() for item in existing}
    for value in values:
        value = (value or "").strip()
        if value and value.lower() not in seen:
            existing.append(value)
            seen.add(value.lower())
    return "\n".join(existing)


def jira_update_issue_fields(base_url, api_version, auth_type, username, token, issue_key, fields_payload):
    jira_request(
        "PUT",
        base_url,
        api_version,
        auth_type,
        username,
        token,
        f"/issue/{issue_key}",
        json={"fields": fields_payload},
    )


def make_user_payload(user_value, user_payload_type):
    user_value = (user_value or "").strip()

    if user_payload_type == "name":
        return {"name": user_value}

    if user_payload_type == "key":
        return {"key": user_value}

    if user_payload_type == "accountId":
        return {"accountId": user_value}

    return {"name": user_value}


def user_values_to_compare(user_value):
    values = []

    if not user_value:
        return values

    if isinstance(user_value, str):
        values.append(user_value)
        return values

    if isinstance(user_value, dict):
        for key in ["name", "key", "accountId", "displayName", "emailAddress"]:
            value = user_value.get(key)
            if value:
                values.append(str(value))

    return values


def user_matches(user_value, target_user):
    target_user = (target_user or "").strip().lower()

    if not target_user:
        return False

    for value in user_values_to_compare(user_value):
        if value.strip().lower() == target_user:
            return True

    return False


def user_to_payload(user_value, user_payload_type):
    if isinstance(user_value, dict):
        preferred_value = user_value.get(user_payload_type)

        if not preferred_value:
            for key in ["name", "key", "accountId"]:
                if user_value.get(key):
                    preferred_value = user_value.get(key)
                    break

        if preferred_value:
            return make_user_payload(str(preferred_value), user_payload_type)

    if isinstance(user_value, str):
        return make_user_payload(user_value, user_payload_type)

    return user_value


def build_replaced_user_list(existing_users, old_user, new_user, user_payload_type):
    if existing_users is None:
        existing_users = []

    if not isinstance(existing_users, list):
        existing_users = [existing_users]

    if (old_user or "").strip().lower() == (new_user or "").strip().lower():
        return [
            user_to_payload(existing_user, user_payload_type)
            for existing_user in existing_users
        ]

    new_user_payload = make_user_payload(new_user, user_payload_type)
    result = []
    replaced = False

    new_user_already_exists = any(
        user_matches(existing_user, new_user)
        for existing_user in existing_users
    )

    for existing_user in existing_users:
        if user_matches(existing_user, old_user):
            replaced = True

            if not new_user_already_exists:
                result.append(new_user_payload)

            continue

        result.append(user_to_payload(existing_user, user_payload_type))

    if not replaced:
        raise Exception(
            f"Old user '{old_user}' was not found in the current field value. "
            f"Field was not changed to avoid removing other users."
        )

    return result


def jira_get_issue_field_value(
    base_url,
    api_version,
    auth_type,
    username,
    token,
    issue_key,
    field_id,
):
    data = jira_request(
        "GET",
        base_url,
        api_version,
        auth_type,
        username,
        token,
        f"/issue/{issue_key}",
        params={"fields": field_id},
    )

    return data.get("fields", {}).get(field_id)


def jira_update_assignee(base_url, api_version, auth_type, username, token, issue_key, new_user, user_payload_type):
    jira_request(
        "PUT",
        base_url,
        api_version,
        auth_type,
        username,
        token,
        f"/issue/{issue_key}/assignee",
        json=make_user_payload(new_user, user_payload_type),
    )


def find_field_id_by_name(fields, field_name):
    wanted = field_name.strip().lower()
    for field in fields or []:
        if field.get("name", "").strip().lower() == wanted:
            return field.get("id")
    return None


def get_field_map(base_url, api_version, auth_type, username, token, manual_ids=None):
    manual_ids = manual_ids or {}
    needed_fields = ["Internal Reporter", "Waiting information from"]
    result = {}
    all_manual_are_real = True

    for field_name in needed_fields:
        manual = (manual_ids.get(field_name) or "").strip()
        if manual.startswith("customfield_") and "XXXXX" not in manual and "YYYYY" not in manual:
            result[field_name] = manual
        else:
            all_manual_are_real = False

    if all_manual_are_real:
        return result

    fields = jira_get_fields(base_url, api_version, auth_type, username, token)
    for field_name in needed_fields:
        manual = (manual_ids.get(field_name) or "").strip()
        if manual.startswith("customfield_") and "XXXXX" not in manual and "YYYYY" not in manual:
            result[field_name] = manual
        else:
            result[field_name] = find_field_id_by_name(fields, field_name)

    return result


def jira_apply_handover_change(
    base_url,
    api_version,
    auth_type,
    username,
    token,
    issue_key,
    field_group,
    old_user,
    new_user,
    user_payload_type,
    internal_reporter_field_id,
    waiting_info_field_id,
):
    user_payload = make_user_payload(new_user, user_payload_type)

    if field_group == "Assignee":
        jira_update_assignee(
            base_url,
            api_version,
            auth_type,
            username,
            token,
            issue_key,
            new_user,
            user_payload_type,
        )
        return

    if field_group == "Reporter":
        jira_update_issue_fields(
            base_url,
            api_version,
            auth_type,
            username,
            token,
            issue_key,
            {"reporter": user_payload},
        )
        return

    if field_group == "Internal Reporter":
        current_users = jira_get_issue_field_value(
            base_url,
            api_version,
            auth_type,
            username,
            token,
            issue_key,
            internal_reporter_field_id,
        )

        updated_users = build_replaced_user_list(
            current_users,
            old_user,
            new_user,
            user_payload_type,
        )

        jira_update_issue_fields(
            base_url,
            api_version,
            auth_type,
            username,
            token,
            issue_key,
            {internal_reporter_field_id: updated_users},
        )
        return

    if field_group == "Waiting Information From":
        current_users = jira_get_issue_field_value(
            base_url,
            api_version,
            auth_type,
            username,
            token,
            issue_key,
            waiting_info_field_id,
        )

        updated_users = build_replaced_user_list(
            current_users,
            old_user,
            new_user,
            user_payload_type,
        )

        jira_update_issue_fields(
            base_url,
            api_version,
            auth_type,
            username,
            token,
            issue_key,
            {waiting_info_field_id: updated_users},
        )
        return

    raise Exception(f"Unknown field group: {field_group}")


# =========================================================
# FORMATTERS / UTILS
# =========================================================
def user_display(value):
    if not value:
        return ""
    if isinstance(value, dict):
        return value.get("displayName") or value.get("name") or value.get("key") or value.get("accountId") or ""
    return str(value)


def field_to_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return ", ".join([field_to_text(item) for item in value if field_to_text(item)])
    if isinstance(value, dict):
        for key in ["value", "name", "displayName", "key", "accountId"]:
            if value.get(key):
                return str(value.get(key))
        return str(value)
    return str(value)


def compact(text, limit=160):
    text = " ".join((text or "").split())
    return text[: limit - 3] + "..." if len(text) > limit else text


def jql_value(value):
    value = (value or "").strip()
    if not value:
        return '""'
    if value.startswith('"') and value.endswith('"'):
        return value
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
    if all(ch in allowed for ch in value):
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def parse_projects(raw_text):
    raw_text = raw_text or ""
    parts = re.split(r"[,\n;]+", raw_text)
    projects = []
    seen = set()
    for part in parts:
        project = part.strip()
        if not project:
            continue
        key = project.lower()
        if key not in seen:
            seen.add(key)
            projects.append(project)
    return projects


def build_partner_clause(projects):
    if not projects:
        return '"Partner / Project" is EMPTY'
    if len(projects) == 1:
        return f'"Partner / Project" = {jql_value(projects[0])}'
    values = ", ".join(jql_value(project) for project in projects)
    return f'"Partner / Project" in ({values})'


def build_handover_jqls(projects, current_person):
    partner_clause = build_partner_clause(projects)
    current_person_value = jql_value(current_person)
    return {
        "Reporter": f'''project = "Change Management" AND {partner_clause} AND reporter = {current_person_value} AND statusCategory != Done''',
        "Internal Reporter": f'''project = "Change Management" AND {partner_clause} AND "Internal Reporter" = {current_person_value} AND statusCategory != Done''',
        "Assignee": f'''project = "Change Management" AND {partner_clause} AND assignee = {current_person_value} AND statusCategory != Done''',
        "Waiting Information From": f'''project = "Change Management" AND {partner_clause} AND "Waiting information from" = {current_person_value} AND statusCategory != Done''',
    }


def parse_ticket_keys(raw_text):
    raw_text = raw_text or ""
    return set(re.findall(r"[A-Z][A-Z0-9]+-\d+", raw_text.upper()))


def issue_type_fallback_symbol(issue_type_name):
    name = (issue_type_name or "").strip().lower()
    if "configuration" in name:
        return "C"
    if "internal" in name and "change" in name:
        return "IC"
    if name == "change" or " change" in name:
        return "CH"
    if "incident" in name:
        return "!"
    if "sub-task" in name or "subtask" in name:
        return "↳"
    if "task" in name:
        return "T"
    return "?"


def svg_icon_data_uri(text):
    text = (text or "?").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18">'
        '<rect x="1" y="1" width="16" height="16" rx="3" fill="#dbeafe" stroke="#60a5fa"/>'
        f'<text x="9" y="12" text-anchor="middle" font-size="8" font-family="Arial" font-weight="700" fill="#1d4ed8">{text}</text>'
        '</svg>'
    )
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_jira_icon_as_data_uri(icon_url, base_url, auth_type, username, token):
    icon_url = (icon_url or "").strip()
    if not icon_url:
        return ""
    if icon_url.startswith("/"):
        icon_url = f"{clean_base_url(base_url)}{icon_url}"
    try:
        headers, auth = build_auth(auth_type, username, token)
        headers.pop("Content-Type", None)
        response = requests.get(icon_url, headers=headers, auth=auth, timeout=20)
        if not response.ok or not response.content:
            return ""
        content_type = response.headers.get("Content-Type", "image/png").split(";")[0].strip()
        if not content_type.startswith("image/"):
            return ""
        encoded = base64.b64encode(response.content).decode("ascii")
        return f"data:{content_type};base64,{encoded}"
    except Exception:
        return ""


def issue_type_icon_value(issue_type, base_url, auth_type, username, token):
    issue_type = issue_type or {}
    issue_type_name = field_to_text(issue_type)
    icon_url = issue_type.get("iconUrl", "") if isinstance(issue_type, dict) else ""
    exact_icon = fetch_jira_icon_as_data_uri(icon_url, base_url, auth_type, username, token)
    if exact_icon:
        return exact_icon
    return svg_icon_data_uri(issue_type_fallback_symbol(issue_type_name))


def issue_to_handover_row(issue, base_url, field_map, auth_type, username, token):
    fields = issue.get("fields", {})
    key = issue.get("key", "")
    internal_reporter_id = field_map.get("Internal Reporter")
    waiting_info_id = field_map.get("Waiting information from")
    issue_type = fields.get("issuetype") or {}
    issue_type_name = field_to_text(issue_type)

    return {
        "Select": True,
        "T": issue_type_icon_value(issue_type, base_url, auth_type, username, token),
        "Issue Type": issue_type_name,
        "Key": key,
        "Open": f"{clean_base_url(base_url)}/browse/{key}",
        "Summary": compact(fields.get("summary", ""), 160),
        "Status": field_to_text(fields.get("status")),
        "Assignee": user_display(fields.get("assignee")),
        "Reporter": user_display(fields.get("reporter")),
        "Internal Reporter": field_to_text(fields.get(internal_reporter_id)) if internal_reporter_id else "",
        "Waiting information from": field_to_text(fields.get(waiting_info_id)) if waiting_info_id else "",
        "Updated": fields.get("updated", ""),
    }


def jira_icon_column(label="T"):
    return st.column_config.ImageColumn(label, width="small", help="Jira issue type")


# =========================================================
# ROX DOMAIN GROUPER
# =========================================================
PROJECT_PATTERNS = {
    "1Go": ["1go"],
    "Drip": ["drip"],
    "Fresh": ["fresh"],
    "Galaktika 15": ["martin"],
    "Galaktika 16": ["beef"],
    "Galaktika 17": ["fugu"],
    "Gizbo": ["gizbo"],
    "Irwin": ["irwin"],
    "izzi": ["izzi"],
    "Jet": ["jet"],
    "Legzo": ["legzo"],
    "Lex": ["lex"],
    "Monro": ["monro"],
    "Rox": ["rox"],
    "Sol": ["sol"],
    "Starda": ["starda"],
    "Flagman": ["flagman"],
}

ALL_PATTERNS = []
for project, patterns in PROJECT_PATTERNS.items():
    for pattern in patterns:
        ALL_PATTERNS.append((project, pattern.lower()))
ALL_PATTERNS.sort(key=lambda x: len(x[1]), reverse=True)


def clean_domain(line: str) -> str:
    line = (line or "").strip()
    if not line:
        return ""
    line = re.sub(r"^https?://", "", line, flags=re.IGNORECASE)
    line = line.strip("/")
    return line.lower()


def find_project(domain: str):
    for project, pattern in ALL_PATTERNS:
        if pattern in domain:
            return project
    return None


def group_domains(input_text: str, greeting: str, default_tag: str) -> str:
    lines = input_text.splitlines()
    grouped = defaultdict(list)
    unknown = []
    seen = set()

    for line in lines:
        raw = line.strip()
        if not raw:
            continue

        cleaned = clean_domain(raw)
        project = find_project(cleaned)
        full_url = raw if raw.lower().startswith(("http://", "https://")) else f"http://{cleaned}/"

        if full_url in seen:
            continue
        seen.add(full_url)

        if project:
            grouped[project].append(full_url)
        else:
            unknown.append(full_url)

    if not grouped and not unknown:
        return "No domains to process."

    result = [greeting.strip() or f"Hi, can you activate LiveTV for these domains as well? /{default_tag}/", ""]

    for project in sorted(grouped.keys()):
        result.append(f"{project}:")
        result.extend(grouped[project])
        result.append("")

    if unknown:
        result.append("Unknown:")
        result.extend(unknown)
        result.append("")

    return "\n".join(result).strip() + "\n"


# =========================================================
# SESSION HELPERS
# =========================================================
def init_state():
    defaults = {
        "logged_in": False,
        "current_user": None,
        "jira_me": None,
        "zip_data": None,
        "zip_name": None,
        "split_ready": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


def current_jira_context():
    current_user = st.session_state.current_user or {}
    jira_base_url = JIRA_BASE_URL
    api_version = API_VERSION
    auth_type = current_user.get("jira_auth_type", AUTH_TYPE)
    username = current_user.get("jira_username", "")
    token = current_user.get("jira_token", "")
    user_payload_type = current_user.get("user_payload_type", USER_PAYLOAD_TYPE)
    return jira_base_url, api_version, auth_type, username, token, user_payload_type


def require_jira_settings():
    jira_base_url, api_version, auth_type, username, token, _ = current_jira_context()
    token_text = (token or "").strip()

    if not jira_base_url:
        st.error("Jira Base URL is not configured in secrets.toml.")
        return False
    if not token_text or "PASTE_" in token_text:
        st.error("Jira credentials are not configured in .streamlit/secrets.toml. Password opens the app; token connects Jira. Obviously one password was too merciful.")
        return False
    if auth_type == "Basic" and not username:
        st.error("Jira username is not configured in .streamlit/secrets.toml.")
        return False
    if auth_type not in ["Basic", "Bearer"]:
        st.error('jira_auth_type must be either "Basic" or "Bearer".')
        return False
    return True


def get_cached_field_map():
    jira_base_url, api_version, auth_type, username, token, _ = current_jira_context()
    cache_key = f"field_map_{username}_{auth_type}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = get_field_map(jira_base_url, api_version, auth_type, username, token, MANUAL_FIELD_IDS)
    return st.session_state[cache_key]


def clear_handover_results():
    for key in [
        "handover_groups",
        "handover_jqls",
        "handover_search_errors",
        "loaded_projects",
        "loaded_current_person",
        "confirm_handover",
    ]:
        st.session_state.pop(key, None)


# =========================================================
# LOGIN PAGE
# =========================================================
def render_login():
    st.markdown(
        f"""
        <div class="login-shell">
          <div class="login-card">
            <div class="login-icon">🛠️</div>
            <div class="login-title">{APP_TITLE}</div>
            <div class="login-subtitle">{APP_SUBTITLE}<br>Enter password. If Jira is configured, the app will verify API access immediately.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Streamlit cannot place native inputs inside the HTML card, so this is intentionally below it.
    login_col1, login_col2, login_col3 = st.columns([1.15, 1, 1.15])
    with login_col2:
        entered_password = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Password")
        login_clicked = st.button("Open Change Helper", type="primary", use_container_width=True)

        if not APP_USERS:
            st.warning("No users found. Create `.streamlit/secrets.toml` first. Humanity has once again hidden the keys under the doormat.")

        if login_clicked:
            entered_password_clean = (entered_password or "").strip()
            user_config = APP_USERS.get(entered_password_clean)

            if not user_config:
                st.session_state.logged_in = False
                st.session_state.current_user = None
                st.session_state.jira_me = None
                st.error("Wrong password.")
                st.stop()

            token = (user_config.get("jira_token") or "").strip()
            auth_type = user_config.get("jira_auth_type", AUTH_TYPE)
            username = user_config.get("jira_username", "")

            if VERIFY_JIRA_ON_LOGIN and token and "PASTE_" not in token:
                try:
                    with st.spinner("Checking Jira API access..."):
                        me = jira_get_myself(JIRA_BASE_URL, API_VERSION, auth_type, username, token)
                    st.session_state.jira_me = me
                except Exception as e:
                    st.session_state.logged_in = False
                    st.session_state.current_user = None
                    st.session_state.jira_me = None
                    st.error("Password is correct, but Jira API connection failed.")
                    st.code(str(e))
                    st.stop()

            st.session_state.logged_in = True
            st.session_state.current_user = user_config
            st.rerun()

    st.stop()


# =========================================================
# LAYOUT HELPERS
# =========================================================
def render_hero(title, subtitle, pills=None):
    pills = pills or []
    pill_html = "".join([f'<span class="pill">{pill}</span>' for pill in pills])
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
            <div class="pill-row">{pill_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_nav():
    current_user = st.session_state.current_user or {}
    display_name = current_user.get("display_name") or current_user.get("jira_username") or "User"

    st.sidebar.markdown(f"### 🛠️ {APP_TITLE}")
    st.sidebar.caption(f"Logged in as **{display_name}**")
    if st.session_state.jira_me:
        me = st.session_state.jira_me
        st.sidebar.caption(f"Jira: **{me.get('displayName') or me.get('name') or display_name}**")

    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "AM Handover", "ROX Domain Grouper", "Excel Splitter", "Settings"],
        label_visibility="collapsed",
    )

    st.sidebar.divider()
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.jira_me = None
        clear_handover_results()
        st.rerun()

    st.sidebar.markdown('<div class="footer-note">Local-first tool. Keep tokens in secrets, not Git. A shocking concept, apparently.</div>', unsafe_allow_html=True)
    return page


# =========================================================
# PAGES
# =========================================================
def page_dashboard():
    render_hero(
        "Change Helper",
        "One clean internal tool for daily Change Management work: handover tickets, group ROX domains, and split Excel files.",
        ["AM Handover", "ROX", "Excel", "Jira API"],
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="mini-card">
              <div class="tool-card-title">🔁 AM Handover</div>
              <div class="tool-card-text">Generate 4 JQL groups, review found tickets, exclude keys, and apply handover changes after confirmation.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="mini-card">
              <div class="tool-card-title">📡 ROX Domain Grouper</div>
              <div class="tool-card-text">Paste domains, auto-detect projects, remove duplicates, and produce a clean ready-to-copy message.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="mini-card">
              <div class="tool-card-title">📊 Excel Splitter</div>
              <div class="tool-card-text">Upload an Excel file, split it by row count, and download all chunks in one ZIP.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    jira_base_url, api_version, auth_type, username, token, _ = current_jira_context()
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-number">{auth_type}</div><div class="metric-label">Jira auth</div></div>', unsafe_allow_html=True)
    with m2:
        token_state = "Configured" if token and "PASTE_" not in token else "Missing"
        st.markdown(f'<div class="metric-card"><div class="metric-number">{token_state}</div><div class="metric-label">Jira token</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><div class="metric-number">{api_version}</div><div class="metric-label">API version</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card"><div class="metric-number">{username or "-"}</div><div class="metric-label">Jira username</div></div>', unsafe_allow_html=True)


def page_settings():
    render_hero("Settings", "Read-only view of current app configuration. Real secrets stay hidden, as nature intended.", ["Secrets", "Jira", "Users"])

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Jira connection")
    jira_base_url, api_version, auth_type, username, token, user_payload_type = current_jira_context()

    s1, s2, s3 = st.columns(3)
    s1.text_input("Jira base URL", value=jira_base_url, disabled=True)
    s2.text_input("API version", value=api_version, disabled=True)
    s3.text_input("User payload type", value=user_payload_type, disabled=True)

    s4, s5 = st.columns(2)
    s4.text_input("Auth type", value=auth_type, disabled=True)
    s5.text_input("Current Jira username", value=username, disabled=True)

    if st.button("Check Jira connection", type="primary"):
        if require_jira_settings():
            try:
                me = jira_get_myself(jira_base_url, api_version, auth_type, username, token)
                st.session_state.jira_me = me
                st.success(f"Connected as {me.get('displayName') or me.get('name') or username}")
            except Exception as e:
                st.error("Jira connection failed")
                st.code(str(e))
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Manual field IDs")
    f1, f2 = st.columns(2)
    f1.text_input("Internal Reporter", value=MANUAL_FIELD_IDS.get("Internal Reporter") or "Auto-detect", disabled=True)
    f2.text_input("Waiting information from", value=MANUAL_FIELD_IDS.get("Waiting information from") or "Auto-detect", disabled=True)
    st.caption("If field IDs are empty, the app will call Jira `/field` and try to detect them by name.")
    st.markdown('</div>', unsafe_allow_html=True)


def page_excel_splitter():
    render_hero("Excel Splitter", "Split a big Excel file into smaller XLSX parts and download one ZIP.", ["XLSX", "ZIP", "No Jira needed"])

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"], key="excel_uploader")
    chunk_size = st.number_input("Rows per file", value=1000, min_value=1, step=1, key="chunk_size")

    if uploaded_file and st.button("Split Excel", type="primary", key="split_button"):
        try:
            with st.spinner("Processing file..."):
                df = pd.read_excel(uploaded_file, engine="openpyxl")
                base_name = uploaded_file.name.rsplit(".", 1)[0]
                zip_filename = f"{base_name}_split.zip"
                zip_buffer = BytesIO()

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
                    for i in range(0, len(df), chunk_size):
                        chunk = df.iloc[i : i + chunk_size]
                        part_filename = f"{base_name}_{i // chunk_size + 1}.xlsx"
                        excel_buffer = BytesIO()
                        chunk.to_excel(excel_buffer, index=False, engine="openpyxl")
                        excel_buffer.seek(0)
                        z.writestr(part_filename, excel_buffer.read())

                zip_buffer.seek(0)
                st.session_state.zip_data = zip_buffer.read()
                st.session_state.zip_name = zip_filename
                st.session_state.split_ready = True
                st.session_state.split_rows = len(df)
                st.session_state.split_parts = (len(df) + chunk_size - 1) // chunk_size
        except Exception as e:
            st.error("Failed to split Excel file")
            st.code(str(e))

    if st.session_state.split_ready:
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{st.session_state.get("split_rows", 0)}</div><div class="metric-label">Rows</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{st.session_state.get("split_parts", 0)}</div><div class="metric-label">Files created</div></div>', unsafe_allow_html=True)
        st.success("Done. ZIP is ready.")
        st.download_button(
            label="Download ZIP",
            data=st.session_state.zip_data,
            file_name=st.session_state.zip_name,
            mime="application/zip",
            key="download_zip",
            use_container_width=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)


def page_domain_grouper():
    render_hero("ROX Domain Grouper", "Paste domains, group them by project pattern, remove duplicates, and copy the final message.", ["ROX", "Domains", "Copy-ready"])

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    g1, g2 = st.columns([2, 1])
    with g1:
        greeting = st.text_input(
            "Message header",
            value="Hi, can you activate LiveTV for these domains as well? /ROX/",
            key="domain_greeting",
        )
    with g2:
        default_tag = st.text_input("Default tag", value="ROX", key="default_tag")

    domain_input = st.text_area(
        "Paste domains, one per line",
        height=290,
        placeholder="http://jetcasino527.com/\nhttp://gizbocasinovip37.com/",
        key="domain_input",
    )

    if st.button("Group Domains", type="primary", key="group_domains_button"):
        st.session_state.grouped_result = group_domains(domain_input, greeting, default_tag)

    if "grouped_result" in st.session_state:
        st.text_area(
            "Formatted output",
            value=st.session_state.grouped_result,
            height=360,
            key="grouped_output",
        )
        total_domains = len([line for line in domain_input.splitlines() if line.strip()])
        st.caption(f"Input lines: {total_domains}. Duplicates are ignored in output.")

    st.markdown('</div>', unsafe_allow_html=True)


def page_am_handover():
    for state_key, widget_key in [
        ("pending_project_input", "project_input"),
        ("pending_from_user", "handover_current"),
        ("pending_to_user", "handover_new"),
    ]:
        if state_key in st.session_state:
            st.session_state[widget_key] = st.session_state.pop(state_key)

    render_hero(
        "AM Handover",
        "Search Change Management tickets by Partner / Project, review the results, and transfer only the selected user fields.",
        ["Review before update", "Jira API", "Safe multi-user fields"],
    )

    jira_base_url, api_version, auth_type, username, token, user_payload_type = current_jira_context()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Search setup")
    st.caption("Write one or several Partner / Project values, choose the current user and the new user, then search tickets.")

    form_col1, form_col2, form_col3, form_col4 = st.columns([2.2, 1.5, 1.5, 1.1])
    with form_col1:
        project_input = st.text_area(
            "Partner / Project(s)",
            value=st.session_state.get("project_input", "Betibas"),
            height=92,
            placeholder="Betibas\nproject 2\nproject 3",
            help="Use comma, semicolon, or new line. Values with spaces will be quoted automatically in JQL.",
            key="project_input",
        )
    with form_col2:
        default_current = (st.session_state.current_user or {}).get("default_current_person", username)
        current_person = st.text_input(
            "From user",
            value=st.session_state.get("handover_current", default_current),
            key="handover_current",
        )
    with form_col3:
        new_person = st.text_input(
            "To user",
            value=st.session_state.get("handover_new", "new.user"),
            key="handover_new",
        )
    with form_col4:
        st.write("")
        st.write("")
        search_handover = st.button("Search tickets", type="primary", use_container_width=True)

    projects = parse_projects(project_input)

    with st.expander("Jira search helpers", expanded=False):
        st.caption("Search users and Partner / Project values directly from Jira. It is not Jira's exact autocomplete UI, but it saves you from copy-pasting names like a medieval scribe.")
        helper_col1, helper_col2 = st.columns(2)

        with helper_col1:
            st.markdown("**Find Partner / Project**")
            partner_lookup = st.text_input("Partner search text", value="", placeholder="Betibas / Ganaexpress / project name", key="partner_lookup_text")
            if st.button("Search partner values", use_container_width=True, key="search_partner_values"):
                if require_jira_settings():
                    try:
                        st.session_state.partner_suggestions = jira_jql_field_suggestions(
                            jira_base_url,
                            api_version,
                            auth_type,
                            username,
                            token,
                            "Partner / Project",
                            partner_lookup,
                            max_results=25,
                        )
                    except Exception as e:
                        st.session_state.partner_suggestions = []
                        st.warning("Partner / Project suggestions failed. Jira may not expose autocomplete for this custom field.")
                        st.caption(summarize_exception(e))

            partner_suggestions = st.session_state.get("partner_suggestions", [])
            if partner_suggestions:
                partner_labels = [suggestion_label(item) for item in partner_suggestions]
                picked_partner_labels = st.multiselect("Choose values to add", options=partner_labels, key="picked_partner_labels")
                if st.button("Add selected Partner / Project", use_container_width=True, key="add_partner_values"):
                    selected_values = [partner_suggestions[partner_labels.index(label)]["value"] for label in picked_partner_labels]
                    st.session_state.pending_project_input = append_values_to_text_area(project_input, selected_values)
                    st.rerun()
            elif partner_lookup:
                st.caption("No partner suggestions loaded yet.")

        with helper_col2:
            st.markdown("**Find Jira user**")
            user_lookup = st.text_input("User search text", value="", placeholder="asthghik.sa / name.surname", key="user_lookup_text")
            if st.button("Search users", use_container_width=True, key="search_jira_users"):
                if require_jira_settings():
                    try:
                        st.session_state.user_suggestions = jira_user_picker_search(
                            jira_base_url,
                            api_version,
                            auth_type,
                            username,
                            token,
                            user_lookup,
                            max_results=25,
                        )
                    except Exception as e:
                        st.session_state.user_suggestions = []
                        st.warning("User search failed.")
                        st.caption(summarize_exception(e))

            user_suggestions = st.session_state.get("user_suggestions", [])
            if user_suggestions:
                user_labels = [user_suggestion_label(item, user_payload_type) for item in user_suggestions]
                picked_user_label = st.selectbox("Choose user", options=user_labels, key="picked_jira_user")
                picked_user = user_suggestions[user_labels.index(picked_user_label)]
                picked_identifier = user_identifier_for_payload(picked_user, user_payload_type)
                u1, u2 = st.columns(2)
                with u1:
                    if st.button("Set as From user", use_container_width=True, key="set_from_user"):
                        st.session_state.pending_from_user = picked_identifier
                        st.rerun()
                with u2:
                    if st.button("Set as To user", use_container_width=True, key="set_to_user"):
                        st.session_state.pending_to_user = picked_identifier
                        st.rerun()
            elif user_lookup:
                st.caption("No user suggestions loaded yet.")

    if projects and current_person.strip():
        with st.expander("Generated JQL preview", expanded=True):
            preview_jqls = build_handover_jqls(projects, current_person)
            for group_name, jql in preview_jqls.items():
                st.markdown(f"**{group_name}**")
                st.code(jql, language="sql")

    st.markdown('</div>', unsafe_allow_html=True)

    if search_handover:
        if not projects:
            st.error("Partner / Project is empty.")
        elif not current_person.strip():
            st.error("From user is empty.")
        elif require_jira_settings():
            try:
                with st.spinner("Loading handover tickets from Jira..."):
                    jqls = build_handover_jqls(projects, current_person)
                    field_map = get_cached_field_map()
                    extra_fields = [field_map.get("Internal Reporter"), field_map.get("Waiting information from")]
                    fields = ["summary", "status", "issuetype", "assignee", "reporter", "created", "updated"] + [field for field in extra_fields if field]

                    handover_groups = {}
                    search_errors = []
                    empty_columns = ["Select", "T", "Issue Type", "Key", "Open", "Summary", "Status", "Assignee", "Reporter", "Internal Reporter", "Waiting information from", "Updated"]
                    for group_name, jql in jqls.items():
                        try:
                            issues = jira_search(jira_base_url, api_version, auth_type, username, token, jql, fields)
                            handover_groups[group_name] = pd.DataFrame(
                                [issue_to_handover_row(issue, jira_base_url, field_map, auth_type, username, token) for issue in issues]
                            )
                        except Exception as e:
                            search_errors.append({"Group": group_name, "Message": summarize_exception(e)})
                            handover_groups[group_name] = pd.DataFrame(columns=empty_columns)

                    st.session_state.handover_groups = handover_groups
                    st.session_state.handover_jqls = jqls
                    st.session_state.loaded_projects = projects
                    st.session_state.loaded_current_person = current_person
                    st.session_state.handover_search_errors = search_errors

                total = sum(len(df) for df in st.session_state.handover_groups.values())
                search_errors = st.session_state.get("handover_search_errors", [])
                if search_errors:
                    unique_messages = sorted({item["Message"] for item in search_errors})
                    if len(search_errors) == 4 and len(unique_messages) == 1:
                        st.warning("Jira did not accept the generated JQL. Most likely Partner / Project or user value is written incorrectly.")
                        st.caption(unique_messages[0])
                    else:
                        st.warning(f"Loaded with {len(search_errors)} group error(s). Check the compact error table below.")
                        st.dataframe(pd.DataFrame(search_errors), hide_index=True, use_container_width=True)
                if total:
                    st.success(f"Loaded {total} ticket rows.")
                elif not search_errors:
                    st.info("Search completed. No tickets found.")
            except Exception as e:
                st.error("Handover search failed")
                st.code(str(e))

    handover_groups = st.session_state.get("handover_groups", {})
    if not handover_groups:
        st.info("Search tickets to start AM handover.")
        return

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Review tickets")
    st.caption("Open tickets and uncheck rows you do not want to update. The active JQL is shown in the preview above.")

    search_errors = st.session_state.get("handover_search_errors", [])
    if search_errors:
        with st.expander("Search warnings", expanded=False):
            st.dataframe(pd.DataFrame(search_errors), hide_index=True, use_container_width=True)

    filtered_groups = {group_name: df.copy() for group_name, df in handover_groups.items()}

    total_visible = sum(len(df) for df in filtered_groups.values())
    unique_visible = len(set().union(*[set(df["Key"].tolist()) for df in filtered_groups.values() if not df.empty])) if filtered_groups else 0

    result_metrics = st.columns(4)
    with result_metrics[0]:
        st.markdown(f'<div class="metric-card"><div class="metric-number">{total_visible}</div><div class="metric-label">Visible rows</div></div>', unsafe_allow_html=True)
    with result_metrics[1]:
        st.markdown(f'<div class="metric-card"><div class="metric-number">{unique_visible}</div><div class="metric-label">Unique tickets</div></div>', unsafe_allow_html=True)
    with result_metrics[2]:
        search_warning_count = len(st.session_state.get("handover_search_errors", []))
        st.markdown(f'<div class="metric-card"><div class="metric-number">{search_warning_count}</div><div class="metric-label">Search warnings</div></div>', unsafe_allow_html=True)
    with result_metrics[3]:
        loaded_project_count = len(st.session_state.get("loaded_projects", []))
        st.markdown(f'<div class="metric-card"><div class="metric-number">{loaded_project_count}</div><div class="metric-label">Loaded projects</div></div>', unsafe_allow_html=True)

    selected_changes = []
    group_order = ["Reporter", "Internal Reporter", "Assignee", "Waiting Information From"]
    cols = st.columns(4)

    for col, group_name in zip(cols, group_order):
        with col:
            df = filtered_groups.get(group_name, pd.DataFrame())
            st.markdown(f'<div class="group-title">{group_name}</div><div class="group-subtitle">{len(df)} rows found</div>', unsafe_allow_html=True)

            if df.empty:
                st.info("No tickets found")
                continue

            visible_columns = ["Select", "T", "Key", "Open", "Summary", "Status", "Assignee", "Reporter"]
            if group_name == "Internal Reporter":
                visible_columns.append("Internal Reporter")
            if group_name == "Waiting Information From":
                visible_columns.append("Waiting information from")

            edited_df = st.data_editor(
                df[visible_columns],
                hide_index=True,
                use_container_width=True,
                height=460,
                key=f"handover_editor_{group_name}",
                column_config={
                    "Select": st.column_config.CheckboxColumn("Select", default=True),
                    "T": jira_icon_column("T"),
                    "Open": st.column_config.LinkColumn("Open", display_text="Open"),
                    "Summary": st.column_config.TextColumn("Summary", width="medium"),
                    "Key": st.column_config.TextColumn("Key", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                },
                disabled=[column for column in visible_columns if column != "Select"],
            )

            selected_df = edited_df[edited_df["Select"] == True]
            st.caption(f"Selected: {len(selected_df)} / {len(edited_df)}")

            for _, row in selected_df.iterrows():
                selected_changes.append(
                    {
                        "Ticket": row["Key"],
                        "Open": row["Open"],
                        "Field": group_name,
                        "From": st.session_state.get("loaded_current_person", current_person),
                        "To": new_person,
                        "Summary": row["Summary"],
                    }
                )

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Planned changes")

    if selected_changes:
        preview_df = pd.DataFrame(selected_changes).sort_values(["Ticket", "Field"])
        st.dataframe(
            preview_df,
            hide_index=True,
            use_container_width=True,
            height=300,
            column_config={
                "Open": st.column_config.LinkColumn("Open", display_text="Open"),
                "Summary": st.column_config.TextColumn("Summary", width="large"),
            },
        )
    else:
        st.warning("No tickets selected.")

    st.divider()
    confirm_apply = st.checkbox("I checked the preview and want to update selected Jira tickets", key="confirm_handover")
    apply_handover = st.button("Apply handover changes", type="primary", disabled=not confirm_apply or not selected_changes)

    if apply_handover:
        try:
            if not new_person.strip():
                st.error("To user is empty.")
                st.stop()

            field_map = get_cached_field_map()
            internal_reporter_field_id = field_map.get("Internal Reporter")
            waiting_info_field_id = field_map.get("Waiting information from")

            if not internal_reporter_field_id:
                st.error("Internal Reporter field id was not found. Add it in .streamlit/secrets.toml.")
                st.stop()
            if not waiting_info_field_id:
                st.error("Waiting information from field id was not found. Add it in .streamlit/secrets.toml.")
                st.stop()

            total_changes = len(selected_changes)
            results = []
            progress_text = st.empty()
            progress_bar = st.progress(0)
            live_results = st.empty()

            for index, change in enumerate(selected_changes, start=1):
                issue_key = change["Ticket"]
                field_group = change["Field"]
                progress_text.info(f"Updating {index}/{total_changes}: {issue_key} · {field_group}")
                try:
                    jira_apply_handover_change(
                        jira_base_url,
                        api_version,
                        auth_type,
                        username,
                        token,
                        issue_key,
                        field_group,
                        change.get("From"),
                        new_person,
                        user_payload_type,
                        internal_reporter_field_id,
                        waiting_info_field_id,
                    )
                    results.append({"#": index, "Ticket": issue_key, "Field": field_group, "Status": "Success"})
                except Exception as e:
                    results.append({"#": index, "Ticket": issue_key, "Field": field_group, "Status": "Failed", "Message": summarize_exception(e)})

                progress_bar.progress(index / max(total_changes, 1))
                live_results.dataframe(pd.DataFrame(results), hide_index=True, use_container_width=True)

            success_count = sum(1 for item in results if item.get("Status") == "Success")
            failed_count = sum(1 for item in results if item.get("Status") == "Failed")
            progress_text.success(f"Finished: {success_count}/{total_changes} updated, {failed_count} failed.")
        except Exception as e:
            st.error("Apply failed")
            st.code(str(e))

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# APP ENTRY
# =========================================================
if not st.session_state.get("logged_in") or not st.session_state.get("current_user"):
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.jira_me = None
    render_login()

page = sidebar_nav()

if page == "Dashboard":
    page_dashboard()
elif page == "AM Handover":
    page_am_handover()
elif page == "ROX Domain Grouper":
    page_domain_grouper()
elif page == "Excel Splitter":
    page_excel_splitter()
elif page == "Settings":
    page_settings()
