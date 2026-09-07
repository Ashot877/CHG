import json
import re
import time

import requests
from requests.auth import HTTPBasicAuth

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

def jira_add_comment(
    base_url,
    api_version,
    auth_type,
    username,
    token,
    issue_key,
    body,
    max_retries=3,
):
    """Add an INTERNAL Jira Service Management comment via Jira issue API."""

    body = (body or "").strip()
    if not body:
        raise ValueError("Comment cannot be empty.")

    payload = {
        "body": body,
        "properties": [
            {
                "key": "sd.public.comment",
                "value": {
                    "internal": True
                },
            }
        ],
    }

    for attempt in range(max_retries):
        try:
            return jira_request(
                "POST",
                base_url,
                api_version,
                auth_type,
                username,
                token,
                f"/issue/{issue_key}/comment",
                json=payload,
            )
        except Exception as error:
            error_text = str(error)

            # Retry only temporary/rate-limit errors.
            if any(code in error_text for code in ["429:", "502:", "503:", "504:"]):
                if attempt < max_retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue

            raise

    raise Exception(
        f"Failed to add internal comment to {issue_key} "
        f"after {max_retries} attempts."
    )

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
        # Internal Reporter in this Jira is a single-user custom field.
        # Jira requires an object like {"name": "user"}, not a list.
        # Yes, the field looks innocent and still has opinions about JSON shapes.
        jira_update_issue_fields(
            base_url,
            api_version,
            auth_type,
            username,
            token,
            issue_key,
            {internal_reporter_field_id: user_payload},
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


def jira_get_issue_editmeta(base_url, api_version, auth_type, username, token, issue_key):
    return jira_request(
        "GET", base_url, api_version, auth_type, username, token,
        f"/issue/{issue_key}/editmeta",
    )


def jira_get_field_ids_by_name(base_url, api_version, auth_type, username, token, field_names):
    fields = jira_get_fields(base_url, api_version, auth_type, username, token)
    result = {}
    for field_name in field_names:
        result[field_name] = find_field_id_by_name(fields, field_name)
    return result
