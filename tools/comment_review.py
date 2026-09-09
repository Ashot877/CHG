import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from core.jira import clean_base_url, jira_request, jira_search, summarize_exception
from core.session import current_jira_context, require_jira_settings
from core.ui import render_hero
from core.utils import compact, field_to_text, user_display


BASE_JQL = """project = "Change Management"
AND (
    "Comment Reviewed" = no
    OR "Comment Reviewed" is EMPTY
)"""

MAX_RANGES = 4
COMMENT_PAGE_SIZE = 100
MAX_WORKERS = 4

BOT_IDENTITIES = {
    "changemanagementbot",
    "change.management",
    "change management bot",
}

PROPAGATED_MARKERS = (
    "this internal message was originally posted by",
    "this public message was originally posted by",
)

PROPAGATED_METADATA_HINTS = (
    "propagat",
    "originally posted",
    "sourceissue",
    "source issue",
    "copiedcomment",
    "copied comment",
    "commentcopy",
    "comment copy",
    "mirroredcomment",
    "mirrored comment",
)


def _normalize_space(value):
    return " ".join(str(value or "").split())


def _body_to_text(body):
    if body is None:
        return ""
    if isinstance(body, str):
        text = re.sub(r"<[^>]+>", " ", body)
        return _normalize_space(text)
    if isinstance(body, dict):
        chunks = []
        if isinstance(body.get("text"), str):
            chunks.append(body["text"])
        for value in body.values():
            if isinstance(value, (dict, list)):
                nested = _body_to_text(value)
                if nested:
                    chunks.append(nested)
        return _normalize_space(" ".join(chunks))
    if isinstance(body, list):
        return _normalize_space(" ".join(_body_to_text(item) for item in body))
    return _normalize_space(body)


def _author_values(author):
    if not isinstance(author, dict):
        return []
    result = []
    for key in ("name", "key", "accountId", "displayName", "emailAddress"):
        value = author.get(key)
        if value:
            result.append(str(value).strip().lower())
    return result


def _is_bot_comment(comment):
    author_values = _author_values(comment.get("author") or {})
    for value in author_values:
        compact_value = re.sub(r"[^a-z0-9]+", "", value)
        if value in BOT_IDENTITIES:
            return True
        if compact_value == "changemanagementbot":
            return True
        if value.startswith("change.management@"):
            return True
    return False


def _metadata_indicates_propagated(comment):
    properties = comment.get("properties")
    if not properties:
        return False

    try:
        blob = json.dumps(properties, ensure_ascii=False, default=str).lower()
    except Exception:
        blob = str(properties).lower()

    return any(hint in blob for hint in PROPAGATED_METADATA_HINTS)


def _text_indicates_propagated(comment):
    body = _body_to_text(comment.get("body"))
    normalized = body.lower()
    return any(marker in normalized for marker in PROPAGATED_MARKERS)


def _is_propagated_comment(comment):
    return _metadata_indicates_propagated(comment) or _text_indicates_propagated(comment)


def _is_original_human_comment(comment):
    return not _is_bot_comment(comment) and not _is_propagated_comment(comment)


def _request_comment_page(
    jira_base_url,
    api_version,
    auth_type,
    username,
    token,
    issue_key,
    start_at,
    max_results=COMMENT_PAGE_SIZE,
):
    params = {
        "startAt": start_at,
        "maxResults": max_results,
        "orderBy": "-created",
        "expand": "properties",
    }

    for attempt in range(3):
        try:
            return jira_request(
                "GET",
                jira_base_url,
                api_version,
                auth_type,
                username,
                token,
                f"/issue/{issue_key}/comment",
                params=params,
            )
        except Exception as error:
            error_text = str(error)

            if attempt == 0 and ("400:" in error_text or "404:" in error_text):
                params.pop("expand", None)
                continue

            if any(code in error_text for code in ("429:", "502:", "503:", "504:")) and attempt < 2:
                time.sleep(1.25 * (attempt + 1))
                continue
            raise

    raise Exception(f"Could not load comments for {issue_key}.")


def jira_get_last_original_human_comment(
    jira_base_url,
    api_version,
    auth_type,
    username,
    token,
    issue_key,
    profile_timezone,
):
    """Read Jira comments newest-first and stop at the first original human comment.

    Jira's comment endpoint supports orderBy=created. Using orderBy=-created makes
    pagination explicit and deterministic: page 1 contains the newest comments,
    then page 2 contains the next older comments, and so on.
    """
    start_at = 0

    while True:
        data = _request_comment_page(
            jira_base_url,
            api_version,
            auth_type,
            username,
            token,
            issue_key,
            start_at,
            max_results=COMMENT_PAGE_SIZE,
        )

        if not isinstance(data, dict):
            return None

        page_comments = data.get("comments", []) or []
        if not page_comments:
            return None

        # Jira is asked for newest-first ordering. Sorting the returned page again
        # by created is a harmless extra guard against odd plugin behavior.
        parsed_comments = []
        for comment in page_comments:
            created = _to_review_clock(comment.get("created"), profile_timezone)
            if created is not None:
                parsed_comments.append((created, comment))

        parsed_comments.sort(key=lambda item: item[0], reverse=True)

        for created, comment in parsed_comments:
            if not _is_original_human_comment(comment):
                continue

            return {
                "created": created,
                "comment": comment,
                "body": _body_to_text(comment.get("body")),
                "author": user_display(comment.get("author")) or "Unknown",
            }

        total = int(data.get("total", 0) or 0)
        start_at += len(page_comments)

        if start_at >= total:
            return None

def _parse_jira_datetime(value):
    if not value:
        return None

    text = str(value).strip()

    if re.search(r"[+-]\d{4}$", text):
        text = text[:-5] + text[-5:-2] + ":" + text[-2:]

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
        ):
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
    return None


def _jira_profile_timezone():
    me = st.session_state.get("jira_me") or {}
    timezone_name = me.get("timeZone") or me.get("timezone")
    if not timezone_name:
        return None
    try:
        return ZoneInfo(str(timezone_name))
    except Exception:
        return None


def _to_review_clock(value, profile_timezone):
    parsed = _parse_jira_datetime(value)
    if parsed is None:
        return None

    if parsed.tzinfo is not None and profile_timezone is not None:
        parsed = parsed.astimezone(profile_timezone)

    return parsed.replace(tzinfo=None)


def _matched_range_labels(comment_datetime, ranges):
    labels = []
    for index, (start_value, end_value) in enumerate(ranges, start=1):
        if start_value <= comment_datetime <= end_value:
            labels.append(f"Range {index}")
    return labels


def _analyze_issue(
    issue,
    jira_base_url,
    api_version,
    auth_type,
    username,
    token,
    ranges,
    profile_timezone,
):
    key = issue.get("key", "")
    latest = jira_get_last_original_human_comment(
        jira_base_url,
        api_version,
        auth_type,
        username,
        token,
        key,
        profile_timezone,
    )
    if not latest:
        return None

    matched_labels = _matched_range_labels(latest["created"], ranges)
    if not matched_labels:
        return None

    fields = issue.get("fields", {}) or {}
    return {
        "Key": key,
        "Open": f"{clean_base_url(jira_base_url)}/browse/{key}",
        "Summary": compact(fields.get("summary", ""), 180),
        "Status": field_to_text(fields.get("status")),
        "Author": latest["author"],
        "Last Original Human Comment": compact(latest["body"], 500),
        "Comment Date": latest["created"],
        "Matched Range": ", ".join(matched_labels),
    }


def _default_first_range():
    now = datetime.now().replace(second=0, microsecond=0)
    start = now.replace(hour=9, minute=0)
    if now < start:
        start = now - timedelta(hours=1)
    return start, now


def _ensure_range_state():
    if "comment_review_range_count" not in st.session_state:
        st.session_state.comment_review_range_count = 1

    count = int(st.session_state.comment_review_range_count)
    first_from, first_to = _default_first_range()

    for index in range(count):
        from_key = f"comment_review_from_{index}"
        to_key = f"comment_review_to_{index}"

        if from_key not in st.session_state or to_key not in st.session_state:
            if index == 0:
                default_from, default_to = first_from, first_to
            else:
                prev_from = st.session_state.get(
                    f"comment_review_from_{index - 1}",
                    first_from + timedelta(days=index - 1),
                )
                prev_to = st.session_state.get(
                    f"comment_review_to_{index - 1}",
                    first_to + timedelta(days=index - 1),
                )
                default_from = prev_from + timedelta(days=1)
                default_to = prev_to + timedelta(days=1)

            st.session_state.setdefault(from_key, default_from)
            st.session_state.setdefault(to_key, default_to)


def _add_range():
    count = int(st.session_state.get("comment_review_range_count", 1))
    if count >= MAX_RANGES:
        return

    previous_index = count - 1
    previous_from = st.session_state.get(f"comment_review_from_{previous_index}")
    previous_to = st.session_state.get(f"comment_review_to_{previous_index}")

    if previous_from is None or previous_to is None:
        previous_from, previous_to = _default_first_range()

    st.session_state[f"comment_review_from_{count}"] = previous_from + timedelta(days=1)
    st.session_state[f"comment_review_to_{count}"] = previous_to + timedelta(days=1)
    st.session_state.comment_review_range_count = count + 1


def _remove_last_range():
    count = int(st.session_state.get("comment_review_range_count", 1))
    if count <= 1:
        return

    last_index = count - 1
    st.session_state.pop(f"comment_review_from_{last_index}", None)
    st.session_state.pop(f"comment_review_to_{last_index}", None)
    st.session_state.comment_review_range_count = count - 1


def _clear_results():
    st.session_state.pop("comment_review_results", None)
    st.session_state.pop("comment_review_errors", None)
    st.session_state.pop("comment_review_candidate_count", None)


def _render_range_controls():
    if not hasattr(st, "datetime_input"):
        st.error(
            "Comment Review requires Streamlit 1.52.0 or newer because it uses "
            "the combined date + time picker."
        )
        return None

    _ensure_range_state()
    count = int(st.session_state.comment_review_range_count)

    ranges = []
    for index in range(count):
        st.markdown(f"**Date range {index + 1}**")
        from_col, arrow_col, to_col = st.columns([1, 0.08, 1])

        with from_col:
            start_value = st.datetime_input(
                "From",
                key=f"comment_review_from_{index}",
                format="DD/MM/YYYY",
                step=timedelta(minutes=5),
                width="stretch",
            )

        with arrow_col:
            st.markdown(
                '<div style="text-align:center;padding-top:2.2rem;font-size:1.25rem;">→</div>',
                unsafe_allow_html=True,
            )

        with to_col:
            end_value = st.datetime_input(
                "To",
                key=f"comment_review_to_{index}",
                format="DD/MM/YYYY",
                step=timedelta(minutes=5),
                width="stretch",
            )

        ranges.append((start_value, end_value))

    add_col, remove_col, spacer = st.columns([1, 1, 4])
    add_col.button(
        "+ Add date range",
        on_click=_add_range,
        disabled=count >= MAX_RANGES,
        use_container_width=True,
        key="comment_review_add_range",
    )
    remove_col.button(
        "Remove last",
        on_click=_remove_last_range,
        disabled=count <= 1,
        use_container_width=True,
        key="comment_review_remove_range",
    )

    if count >= MAX_RANGES:
        st.caption("Maximum 4 date ranges.")

    return ranges


def _build_candidate_jql(ranges):
    earliest_date = min(start for start, _ in ranges).strftime("%Y/%m/%d")
    return f"""{BASE_JQL}
AND updated >= "{earliest_date}"
ORDER BY updated DESC"""


def _render_results(jira_base_url):
    rows = st.session_state.get("comment_review_results")
    if rows is None:
        return

    candidate_count = st.session_state.get("comment_review_candidate_count", 0)
    errors = st.session_state.get("comment_review_errors", [])

    if not rows:
        st.success(
            f"No matching tickets found. Checked {candidate_count} candidate ticket(s)."
        )
        if errors:
            with st.expander(f"Could not read {len(errors)} ticket(s)"):
                st.dataframe(pd.DataFrame(errors), hide_index=True, use_container_width=True)
        return

    rows = sorted(rows, key=lambda row: row["Comment Date"], reverse=True)
    keys = list(dict.fromkeys(row["Key"] for row in rows if row.get("Key")))
    key_jql = "key in (" + ", ".join(keys) + ")"
    filter_url = f"{clean_base_url(jira_base_url)}/issues/?jql={quote(key_jql)}"

    metric_col, jira_col = st.columns([4, 1])
    metric_col.metric("Matching tickets", len(rows))
    jira_col.link_button(
        "Open all in Jira",
        filter_url,
        use_container_width=True,
    )

    st.caption(
        f"Checked {candidate_count} candidate ticket(s). "
        "Bot and propagated comments do not affect the calculated last human comment."
    )

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_order=[
            "Key",
            "Open",
            "Summary",
            "Status",
            "Author",
            "Last Original Human Comment",
            "Comment Date",
            "Matched Range",
        ],
        column_config={
            "Open": st.column_config.LinkColumn("Open", display_text="Open"),
            "Summary": st.column_config.TextColumn("Summary", width="medium"),
            "Last Original Human Comment": st.column_config.TextColumn(
                "Last Original Human Comment",
                width="large",
            ),
            "Comment Date": st.column_config.DatetimeColumn(
                "Comment Date",
                format="DD/MM/YYYY HH:mm",
            ),
        },
    )

    if errors:
        with st.expander(f"Could not read {len(errors)} ticket(s)"):
            st.dataframe(pd.DataFrame(errors), hide_index=True, use_container_width=True)


def page_comment_review():
    render_hero(
        "Comment Review",
        "Find Change Management tickets by their last original human comment, without relying on ScriptRunner lastHumanComment().",
        ["1–4 date ranges", "Bot-safe", "Propagated-safe"],
        eyebrow="Comment Review",
    )

    if not require_jira_settings():
        return

    jira_base_url, api_version, auth_type, username, token, _ = current_jira_context()

    st.markdown(
        '<div class="feature-panel"><div class="step-kicker">Last human comment</div>'
        '<div class="feature-title">Review by date and time</div>'
        '<div class="feature-text">Only Change Management tickets with Comment Reviewed = No or Empty are checked. '
        'Add up to four independent date ranges; ranges are combined with OR.</div></div>',
        unsafe_allow_html=True,
    )

    ranges = _render_range_controls()
    if ranges is None:
        return

    validation_errors = []
    for index, (start_value, end_value) in enumerate(ranges, start=1):
        if start_value is None or end_value is None:
            validation_errors.append(f"Range {index}: both From and To are required.")
        elif start_value > end_value:
            validation_errors.append(f"Range {index}: From must be earlier than To.")

    with st.expander("Applied Jira pre-filter", expanded=False):
        if not validation_errors:
            st.code(_build_candidate_jql(ranges), language="sql")
        else:
            st.code(BASE_JQL, language="sql")
        st.caption(
            "The date logic itself is calculated by Change Helper. "
            "The Jira pre-filter only reduces the number of tickets that must be inspected."
        )

    search_col, clear_col, info_col = st.columns([1, 1, 3])
    search_clicked = search_col.button(
        "Search comments",
        type="primary",
        use_container_width=True,
        disabled=bool(validation_errors),
        key="comment_review_search",
    )
    clear_clicked = clear_col.button(
        "Clear results",
        use_container_width=True,
        key="comment_review_clear",
    )
    info_col.caption(
        'Fixed scope: project = "Change Management" · Comment Reviewed = No/Empty'
    )

    if validation_errors:
        for message in validation_errors:
            st.error(message)

    if clear_clicked:
        _clear_results()
        st.rerun()

    if search_clicked:
        _clear_results()

        candidate_jql = _build_candidate_jql(ranges)
        profile_timezone = _jira_profile_timezone()

        try:
            with st.spinner("Loading candidate Jira tickets..."):
                issues = jira_search(
                    jira_base_url,
                    api_version,
                    auth_type,
                    username,
                    token,
                    candidate_jql,
                    ["summary", "status", "updated"],
                )
        except Exception as error:
            st.error(f"Jira search failed: {summarize_exception(error)}")
            return

        st.session_state.comment_review_candidate_count = len(issues)

        if not issues:
            st.session_state.comment_review_results = []
            st.session_state.comment_review_errors = []
            st.rerun()

        results = []
        errors = []
        progress = st.progress(0)
        status_placeholder = st.empty()
        total = len(issues)

        status_placeholder.caption(
            f"Checking comments for {total} candidate ticket(s)..."
        )

        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, max(1, total))) as executor:
            future_map = {
                executor.submit(
                    _analyze_issue,
                    issue,
                    jira_base_url,
                    api_version,
                    auth_type,
                    username,
                    token,
                    ranges,
                    profile_timezone,
                ): issue.get("key", "")
                for issue in issues
            }

            completed = 0
            for future in as_completed(future_map):
                issue_key = future_map[future]
                completed += 1
                try:
                    row = future.result()
                    if row:
                        results.append(row)
                except Exception as error:
                    errors.append({
                        "Key": issue_key,
                        "Error": summarize_exception(error),
                    })

                progress.progress(completed / total)
                status_placeholder.caption(
                    f"Checked {completed}/{total} ticket(s) · found {len(results)} match(es)"
                )

        progress.empty()
        status_placeholder.empty()

        st.session_state.comment_review_results = results
        st.session_state.comment_review_errors = errors
        st.rerun()

    _render_results(jira_base_url)
