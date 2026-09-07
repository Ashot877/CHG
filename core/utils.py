import re


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

def append_values_to_text_area(existing_text, values):
    existing = parse_projects(existing_text)
    seen = {item.lower() for item in existing}
    for value in values:
        value = (value or "").strip()
        if value and value.lower() not in seen:
            existing.append(value)
            seen.add(value.lower())
    return "\n".join(existing)
