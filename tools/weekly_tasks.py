import re
import time
from collections import defaultdict
from urllib.parse import quote

import pandas as pd
import streamlit as st

from core.config import MANUAL_FIELD_IDS
from core.jira import clean_base_url, get_field_map, jira_add_comment, jira_search, summarize_exception
from core.session import current_jira_context, require_jira_settings
from core.ui import render_hero
from core.utils import compact, field_to_text, user_display
from tools.partner_tier_sync import render_partner_tier_maintenance

WEEKLY_TASKS = {
    "AM Time to Review": {
        "group_field": "Internal Reporter",
        "subtasks": {
            "Breached": {
                "jql": '''issuetype in (Change, "Configuration Change", Questions)
AND statusCategory != Done
AND (
    (status = "Internal Review" AND slaFunction = isBreached("AM_Time to review"))
    OR
    (status = "In review by AM" AND slaFunction = isBreached("In_review by AM"))
)''',
                "comment": "Contacted {name} to inform that the ticket is breached",
            },
            "Critical Zone": {
                "jql": '''issuetype in (Change, "Configuration Change", Questions)
AND statusCategory != Done
AND (
    (status = "Internal Review" AND slaFunction = isInCriticalZone("AM_Time to review"))
    OR
    (status = "In review by AM" AND slaFunction = isInCriticalZone("In_review by AM"))
)''',
                "comment": "Contacted {name} to inform that the ticket will be breached",
            },
        },
    },
    "Change Approval": {
        "group_field": "Assignee",
        "subtasks": {
            "Breached": {
                "jql": '''project = "Change Management"
AND status = "Change Approval"
AND (
    slaFunction = isBreached("Change_Time to Approve")
    OR
    slaFunction = isBreached("Config Change_Time to approve")
)''',
                "comment": "Contacted {name} to inform them that the ticket has breached",
            },
        },
    },
    "Config Change Resolution": {
        "group_field": "Assignee",
        "subtasks": {
            "Breached": {
                "jql": '''issuetype = "Configuration Change"
AND slaFunction = isBreached("Config Change_Resolution time")
AND statusCategory != Done
AND component NOT IN ("design_request_SLA")
AND status NOT IN (
    "Blocked", "On Hold", "Waiting for Provider response",
    "Waiting for information", "Waiting for Partner's Verification"
)''',
                "comment": "Contacted {name} to inform that the ticket is breached",
            },
            "Critical Zone": {
                "jql": '''issuetype = "Configuration Change"
AND (
    slaFunction = isInCriticalZone("Config Change_Resolution time")
    OR slaFunction = isInCriticalZone("Config Change_Time to Resolution_Casino Games")
)
AND statusCategory != Done
AND status NOT IN (
    "Blocked", "On Hold", "Waiting for Provider response",
    "Waiting for information", "Waiting for Partner's Verification"
)''',
                "comment": "Contacted {name} to inform that the ticket will be breached",
            },
        },
    },
}

def weekly_task_state_key(task_name, subtask_name):
    safe = re.sub(r"[^a-zA-Z0-9]+", "_", f"{task_name}_{subtask_name}").strip("_").lower()
    return f"weekly_tasks_{safe}"

def weekly_issue_row(issue, base_url, group_field_id=None):
    fields = issue.get("fields", {}) or {}
    key = issue.get("key", "")
    group_value = fields.get(group_field_id) if group_field_id else fields.get("assignee")
    group_name = user_display(group_value) or "Unassigned"
    return {
        "Select": True,
        "Key": key,
        "Open": f"{clean_base_url(base_url)}/browse/{key}",
        "Summary": compact(fields.get("summary", ""), 170),
        "Status": field_to_text(fields.get("status")),
        "Responsible": group_name,
        "Updated": fields.get("updated", ""),
    }

def render_follow_up_tasks():
    jira_base_url, api_version, auth_type, username, token, _ = current_jira_context()
    top1, top2 = st.columns(2)
    task_name = top1.selectbox("Task", list(WEEKLY_TASKS.keys()), key="weekly_task_name")
    task_config = WEEKLY_TASKS[task_name]
    subtask_name = top2.selectbox(
        "Category", list(task_config["subtasks"].keys()), key=f"weekly_subtask_{task_name}"
    )
    subtask_config = task_config["subtasks"][subtask_name]
    state_key = weekly_task_state_key(task_name, subtask_name)

    with st.expander("JQL", expanded=False):
        st.code(subtask_config["jql"], language="sql")

    load_col, clear_col, info_col = st.columns([1, 1, 3])
    load_clicked = load_col.button("Load tickets", type="primary", use_container_width=True)
    clear_clicked = clear_col.button("Clear", use_container_width=True)
    info_col.caption(f"Grouped by: **{task_config['group_field']}**")

    if clear_clicked:
        st.session_state.pop(state_key, None)
        st.rerun()

    if load_clicked:
        if not require_jira_settings():
            return
        try:
            with st.spinner("Loading Jira tickets..."):
                group_field_id = None
                if task_config["group_field"] == "Internal Reporter":
                    field_map = get_field_map(
                        jira_base_url, api_version, auth_type, username, token, MANUAL_FIELD_IDS
                    )
                    group_field_id = field_map.get("Internal Reporter")
                    if not group_field_id:
                        raise Exception(
                            "Internal Reporter field id was not found. Add it under "
                            "[manual_field_ids] in .streamlit/secrets.toml or verify the Jira field name."
                        )

                fields = ["summary", "status", "assignee", "updated"]
                if group_field_id:
                    fields.append(group_field_id)
                issues = jira_search(
                    jira_base_url, api_version, auth_type, username, token,
                    subtask_config["jql"], fields
                )
                st.session_state[state_key] = [
                    weekly_issue_row(issue, jira_base_url, group_field_id) for issue in issues
                ]
        except Exception as error:
            st.error(f"Jira search failed: {summarize_exception(error)}")

    rows = st.session_state.get(state_key)
    if rows is None:
        st.info("Choose a task and load tickets.")
        return
    if not rows:
        st.success("No matching tickets found.")
        return

    groups = defaultdict(list)
    for row in rows:
        groups[row.get("Responsible") or "Unassigned"].append(row)

    total_people = len(groups)
    metric1, metric2 = st.columns(2)
    metric1.metric("Total tickets", len(rows))
    metric2.metric("Responsible people", total_people)

    summary_rows = []
    for person_name, person_rows in sorted(
        groups.items(), key=lambda item: (-len(item[1]), item[0].lower())
    ):
        keys = [row["Key"] for row in person_rows if row.get("Key")]
        key_jql = "key in (" + ", ".join(keys) + ")"
        filter_url = f"{clean_base_url(jira_base_url)}/issues/?jql={quote(key_jql)}"
        summary_rows.append({
            "Responsible": person_name,
            "Tickets": len(person_rows),
            "Open all in Jira": filter_url,
        })

    st.subheader("Choose a responsible person")
    st.caption("Click a name to open that person's tickets, Jira filter, and comment controls.")

    selected_key = f"{state_key}_selected_person"
    valid_people = [item["Responsible"] for item in summary_rows]
    if st.session_state.get(selected_key) not in valid_people:
        st.session_state[selected_key] = None

    # Compact, clickable people list. Three cards per row keeps the overview readable
    # without turning the page into a chart nobody asked for.
    for row_start in range(0, len(summary_rows), 3):
        columns = st.columns(3)
        for column, item in zip(columns, summary_rows[row_start:row_start + 3]):
            person_name = item["Responsible"]
            ticket_count = item["Tickets"]
            is_selected = st.session_state.get(selected_key) == person_name
            label = f"{'✓ ' if is_selected else ''}{person_name} · {ticket_count}"
            safe_person = re.sub(r"[^a-zA-Z0-9]+", "_", person_name).strip("_")
            if column.button(
                label,
                key=f"{state_key}_person_{safe_person}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            ):
                st.session_state[selected_key] = person_name
                st.rerun()

    selected_person = st.session_state.get(selected_key)
    if not selected_person:
        st.info("Select a person above to manage their tickets.")
        return

    st.divider()
    group_rows = groups[selected_person]
    selected_summary = next(item for item in summary_rows if item["Responsible"] == selected_person)

    st.divider()
    header_col, jira_col = st.columns([4, 1])
    header_col.subheader(f"{selected_person} · {len(group_rows)} ticket(s)")
    jira_col.link_button(
        "Open all in Jira",
        selected_summary["Open all in Jira"],
        use_container_width=True,
    )

    editor_key = f"{state_key}_editor_{re.sub(r'[^a-zA-Z0-9]+', '_', selected_person)}"
    edited_df = st.data_editor(
        pd.DataFrame(group_rows),
        key=editor_key,
        hide_index=True,
        use_container_width=True,
        disabled=["Key", "Open", "Summary", "Status", "Responsible", "Updated"],
        column_config={
            "Select": st.column_config.CheckboxColumn("Select", default=True),
            "Open": st.column_config.LinkColumn("Open", display_text="Open"),
            "Summary": st.column_config.TextColumn("Summary", width="large"),
            "Updated": st.column_config.DatetimeColumn("Updated", format="DD/MM/YYYY HH:mm"),
        },
    )
    selected_keys = edited_df.loc[edited_df["Select"] == True, "Key"].tolist()
    default_comment = subtask_config["comment"].format(name=selected_person)
    comment_text = st.text_area(
        "Comment to add",
        value=default_comment,
        key=f"{state_key}_comment_{re.sub(r'[^a-zA-Z0-9]+', '_', selected_person)}",
        height=90,
    )
    confirmed = st.checkbox(
        f"Confirm adding this comment to {len(selected_keys)} selected ticket(s)",
        key=f"{state_key}_confirm_{re.sub(r'[^a-zA-Z0-9]+', '_', selected_person)}",
    )
    if st.button(
        f"Add comment to selected ({len(selected_keys)})",
        key=f"{state_key}_send_{re.sub(r'[^a-zA-Z0-9]+', '_', selected_person)}",
        disabled=not selected_keys or not confirmed or not comment_text.strip(),
        use_container_width=True,
        type="primary",
    ):
        results = []
        progress = st.progress(0)

        selected_keys = list(dict.fromkeys(
            str(key).strip()
            for key in selected_keys
            if str(key).strip()
        ))

        for index, issue_key in enumerate(selected_keys, start=1):
            try:
                jira_add_comment(
                    jira_base_url, api_version, auth_type, username, token,
                    issue_key, comment_text
                )
                results.append({
                    "Key": issue_key,
                    "Status": "Success",
                    "Details": "Internal comment added",
                })
            except Exception as error:
                results.append({
                    "Key": issue_key,
                    "Status": "Failed",
                    "Details": summarize_exception(error),
                })

            progress.progress(index / len(selected_keys))

            if index < len(selected_keys):
                time.sleep(0.7)

        result_df = pd.DataFrame(results)
        success_count = int((result_df["Status"] == "Success").sum())
        failed_count = len(result_df) - success_count
        if failed_count:
            st.warning(f"Finished: {success_count} succeeded, {failed_count} failed.")
        else:
            st.success(f"Internal comment added to {success_count} ticket(s).")
        st.dataframe(result_df, hide_index=True, use_container_width=True)

def page_weekly_tasks_helper():
    render_hero(
        "Weekly Operations",
        "One place for recurring Change Management work: SLA follow-up and controlled Jira data maintenance.",
        ["SLA follow-up", "Partner Tier Sync", "Safe bulk actions"],
        eyebrow="Digitain · Change Management · Weekly Operations",
    )

    st.markdown('<div class="step-kicker">Choose workspace</div>', unsafe_allow_html=True)
    mode = st.radio(
        "Workspace",
        ["Follow-up", "Data Maintenance"],
        horizontal=True,
        key="weekly_workspace_mode",
        label_visibility="collapsed",
        help="Follow-up keeps the existing SLA/comment workflow. Data Maintenance contains controlled field synchronization tasks.",
    )

    if mode == "Follow-up":
        st.markdown(
            '<div class="feature-panel"><div class="step-kicker">SLA workspace</div><div class="feature-title">Follow-up queues</div>'
            '<div class="feature-text">Load breached or critical-zone tickets, open a responsible person’s queue, review the selection, and add the existing internal follow-up comment.</div></div>',
            unsafe_allow_html=True,
        )
        render_follow_up_tasks()
        return

    render_partner_tier_maintenance()
