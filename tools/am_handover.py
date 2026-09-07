import base64
import re

import pandas as pd
import requests
import streamlit as st

from core.jira import (
    build_auth, clean_base_url, jira_apply_handover_change, jira_jql_field_suggestions,
    jira_search, jira_user_picker_search, summarize_exception, suggestion_label,
    user_identifier_for_payload, user_suggestion_label,
)
from core.session import current_jira_context, get_cached_field_map, require_jira_settings
from core.ui import render_hero
from core.utils import append_values_to_text_area, compact, field_to_text, jql_value, parse_projects, user_display

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

def safe_widget_suffix(value):
    return re.sub(r"[^a-zA-Z0-9_]+", "_", str(value or "")).strip("_")

def handover_editor_key(group_name, version=None):
    if version is None:
        version = int(st.session_state.get("handover_editor_version", 0))
    return f"handover_editor_{safe_widget_suffix(group_name)}_{version}"

def collect_selection_changes_from_editor_state(group_order, groups, version):
    unchecked_keys = set()
    checked_keys = set()

    for group_name in group_order:
        editor_key = handover_editor_key(group_name, version)
        editor_state = st.session_state.get(editor_key)
        if not isinstance(editor_state, dict):
            continue

        edited_rows = editor_state.get("edited_rows", {}) or {}
        if not edited_rows:
            continue

        base_df = groups.get(group_name, pd.DataFrame())
        if base_df is None or base_df.empty or "Key" not in base_df.columns:
            continue

        base_df = base_df.reset_index(drop=True)
        for row_index, changes in edited_rows.items():
            if not isinstance(changes, dict) or "Select" not in changes:
                continue

            try:
                row_position = int(row_index)
            except Exception:
                continue

            if row_position < 0 or row_position >= len(base_df):
                continue

            ticket_key = str(base_df.iloc[row_position].get("Key", "")).upper().strip()
            if not ticket_key:
                continue

            if changes.get("Select") is True:
                checked_keys.add(ticket_key)
            elif changes.get("Select") is False:
                unchecked_keys.add(ticket_key)

    return checked_keys, unchecked_keys

def apply_synced_selection_to_df(df, excluded_keys):
    result = df.copy().reset_index(drop=True)
    if excluded_keys and not result.empty and "Key" in result.columns and "Select" in result.columns:
        result.loc[result["Key"].astype(str).str.upper().isin(excluded_keys), "Select"] = False
    return result


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
                    st.session_state.handover_synced_excluded_keys = []
                    st.session_state.handover_editor_version = 0
                    for key in list(st.session_state.keys()):
                        if str(key).startswith("handover_editor_"):
                            st.session_state.pop(key, None)

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

    filtered_groups = {group_name: df.copy().reset_index(drop=True) for group_name, df in handover_groups.items()}

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

    st.write("")
    selection_col1, selection_col2, selection_col3 = st.columns([1.15, 2.65, 1.15])
    with selection_col1:
        sync_unchecked = st.checkbox(
            "Sync selection",
            value=True,
            key="sync_unchecked_tickets",
            help="When enabled, if you uncheck a ticket in one column, the same ticket is unchecked in all handover columns.",
        )
    with selection_col2:
        st.caption(
            "When sync is ON, removing a ticket from Reporter also removes it from Internal Reporter, Assignee, and Waiting Information From. "
            "Tiny mercy for duplicate rows, since Jira apparently enjoys hide-and-seek."
        )
    with selection_col3:
        if st.button("Reset selection", use_container_width=True, key="reset_handover_selection"):
            st.session_state.handover_synced_excluded_keys = []
            st.session_state.handover_editor_version = int(st.session_state.get("handover_editor_version", 0)) + 1
            for key in list(st.session_state.keys()):
                if str(key).startswith("handover_editor_"):
                    st.session_state.pop(key, None)
            st.rerun()

    group_order = ["Reporter", "Internal Reporter", "Assignee", "Waiting Information From"]

    previous_version = int(st.session_state.get("handover_editor_version", 0))
    stored_excluded_keys = set(st.session_state.get("handover_synced_excluded_keys", []))

    if sync_unchecked:
        checked_keys, unchecked_keys = collect_selection_changes_from_editor_state(group_order, filtered_groups, previous_version)
        updated_excluded_keys = (stored_excluded_keys | unchecked_keys) - checked_keys
        if updated_excluded_keys != stored_excluded_keys:
            st.session_state.handover_synced_excluded_keys = sorted(updated_excluded_keys)
            st.session_state.handover_editor_version = previous_version + 1
            for key in list(st.session_state.keys()):
                if str(key).startswith("handover_editor_"):
                    st.session_state.pop(key, None)
            st.rerun()
    else:
        updated_excluded_keys = set()

    sync_excluded_keys = set(st.session_state.get("handover_synced_excluded_keys", [])) if sync_unchecked else set()

    if sync_unchecked and sync_excluded_keys:
        st.info(f"Sync is ON: {len(sync_excluded_keys)} ticket key(s) are unchecked in all columns: {', '.join(sorted(sync_excluded_keys))}")
    elif not sync_unchecked:
        st.warning("Sync is OFF: unchecked tickets affect only the column where you changed them.")

    cols = st.columns(4)
    edited_groups = {}
    current_editor_version = int(st.session_state.get("handover_editor_version", 0))

    for col, group_name in zip(cols, group_order):
        with col:
            df = filtered_groups.get(group_name, pd.DataFrame())
            st.markdown(f'<div class="group-title">{group_name}</div><div class="group-subtitle">{len(df)} rows found</div>', unsafe_allow_html=True)

            if df.empty:
                st.info("No tickets found")
                edited_groups[group_name] = pd.DataFrame()
                continue

            visible_columns = ["Select", "T", "Key", "Open", "Summary", "Status", "Assignee", "Reporter"]
            if group_name == "Internal Reporter":
                visible_columns.append("Internal Reporter")
            if group_name == "Waiting Information From":
                visible_columns.append("Waiting information from")

            editor_input_df = apply_synced_selection_to_df(df[visible_columns], sync_excluded_keys)

            edited_df = st.data_editor(
                editor_input_df,
                hide_index=True,
                use_container_width=True,
                height=460,
                key=handover_editor_key(group_name, current_editor_version),
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

            edited_groups[group_name] = edited_df.copy()
            local_selected_count = int((edited_df["Select"] == True).sum())
            st.caption(f"Selected here: {local_selected_count} / {len(edited_df)}")

    selected_changes = []

    for group_name in group_order:
        edited_df = edited_groups.get(group_name, pd.DataFrame())
        if edited_df.empty:
            continue

        selected_df = edited_df[edited_df["Select"] == True].copy()
        if sync_unchecked and sync_excluded_keys:
            selected_df = selected_df[~selected_df["Key"].astype(str).str.upper().isin(sync_excluded_keys)]

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
