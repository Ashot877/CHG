import re
from collections import defaultdict
from io import BytesIO

import pandas as pd
from docx import Document
import streamlit as st

from core.config import PARTNER_TYPE_CONFIG
from core.jira import (
    clean_base_url,
    jira_get_field_ids_by_name,
    jira_get_issue_editmeta,
    jira_search,
    jira_update_issue_fields,
    summarize_exception,
)
from core.session import current_jira_context, require_jira_settings
from core.utils import compact, field_to_text
from tools.partner_tier_sync import (
    extract_legacy_word_table_matrices,
    is_docx_bytes,
    normalize_header,
    normalize_partner,
    normalize_partner_loose,
    normalize_space,
    partner_match_candidates,
)


PARTNER_FIELD_NAME = str(PARTNER_TYPE_CONFIG.get("partner_field_name", "Partner / Project") or "Partner / Project")
PARTNER_TYPE_FIELD_NAME = str(PARTNER_TYPE_CONFIG.get("partner_type_field_name", "Partner Type") or "Partner Type")
PARTNER_COLUMN_NAME = str(PARTNER_TYPE_CONFIG.get("partner_column_name", "Partner") or "Partner")
PROJECT_COLUMN_NAME = str(PARTNER_TYPE_CONFIG.get("project_column_name", "Project name") or "Project name")
TYPE_COLUMN_NAME = str(PARTNER_TYPE_CONFIG.get("type_column_name", "Partner Type") or "Partner Type")

DEFAULT_PARTNER_TYPE_JQL = f'''project = "Change Management"
AND issuetype in (Change)
AND "{PARTNER_TYPE_FIELD_NAME}" is EMPTY
AND status NOT IN ("Internal Review", "On Hold", Draft)
AND "Partner / Project" NOT IN (Digitain, "Account Management")
AND created > 2025-01-01
AND (resolution NOT IN ("Wrong ticket", "Not Actual") OR resolution IS EMPTY)
AND "Product Change Category (Partner)" != "Partner Request - Onboarding"
AND approvers IS NOT EMPTY
AND Approvers NOT IN inactiveUsers()
AND status WAS Open'''


def _find_columns(
    matrix,
    partner_header=PARTNER_COLUMN_NAME,
    type_header=TYPE_COLUMN_NAME,
    project_header=PROJECT_COLUMN_NAME,
):
    wanted_partner = normalize_header(partner_header)
    wanted_type = normalize_header(type_header)
    wanted_project = normalize_header(project_header)

    for row_index, row in enumerate(matrix[:20]):
        headers = [normalize_header(cell) for cell in row]
        partner_indexes = [i for i, value in enumerate(headers) if value == wanted_partner]
        type_indexes = [i for i, value in enumerate(headers) if value == wanted_type]
        if partner_indexes and type_indexes:
            project_indexes = [i for i, value in enumerate(headers) if value == wanted_project]
            return row_index, partner_indexes[0], type_indexes[0], (project_indexes[0] if project_indexes else None)
    return None


def _rows_from_matrix(
    matrix,
    partner_header=PARTNER_COLUMN_NAME,
    type_header=TYPE_COLUMN_NAME,
    project_header=PROJECT_COLUMN_NAME,
):
    clean_matrix = []
    for row in matrix:
        clean_row = [normalize_space(cell) for cell in row]
        if any(clean_row):
            clean_matrix.append(clean_row)

    if not clean_matrix:
        return []

    found = _find_columns(clean_matrix, partner_header, type_header, project_header)
    if not found:
        return []

    header_row, partner_col, type_col, project_col = found
    result = []
    current_partner = ""
    for row in clean_matrix[header_row + 1:]:
        partner = row[partner_col] if partner_col < len(row) else ""
        if partner:
            current_partner = partner
        else:
            partner = current_partner
        project = row[project_col] if project_col is not None and project_col < len(row) else ""
        partner_type = row[type_col] if type_col < len(row) else ""
        if partner or project or partner_type:
            result.append({"Partner": partner, "Project name": project, "Partner Type": partner_type})
    return result


def parse_partner_type_rows_from_docx(
    data,
    partner_header=PARTNER_COLUMN_NAME,
    type_header=TYPE_COLUMN_NAME,
    project_header=PROJECT_COLUMN_NAME,
):
    document = Document(BytesIO(data))
    best_rows = []

    for table in document.tables:
        matrix = [[cell.text for cell in row.cells] for row in table.rows]
        parsed = _rows_from_matrix(matrix, partner_header, type_header, project_header)
        if len(parsed) > len(best_rows):
            best_rows = parsed

    if not best_rows:
        raise ValueError(
            f'Could not find a Word table with "{partner_header}" and "{type_header}" columns.'
        )
    return best_rows


def parse_partner_type_rows_from_doc(
    data,
    partner_header=PARTNER_COLUMN_NAME,
    type_header=TYPE_COLUMN_NAME,
    project_header=PROJECT_COLUMN_NAME,
):
    # Confluence commonly exports Word as HTML/MHTML with a .doc extension.
    # Some systems may also give DOCX bytes under a .doc filename.
    if is_docx_bytes(data):
        return parse_partner_type_rows_from_docx(data, partner_header, type_header, project_header)

    best_rows = []
    for matrix in extract_legacy_word_table_matrices(data):
        parsed = _rows_from_matrix(matrix, partner_header, type_header, project_header)
        if len(parsed) > len(best_rows):
            best_rows = parsed

    if not best_rows:
        raise ValueError(
            f'Could not find a Word table with "{partner_header}" and "{type_header}" columns.'
        )
    return best_rows


def _dataframe_matrix(df):
    return [["" if pd.isna(value) else str(value) for value in row] for row in df.values.tolist()]


def parse_partner_type_rows_from_excel(
    data,
    partner_header=PARTNER_COLUMN_NAME,
    type_header=TYPE_COLUMN_NAME,
    project_header=PROJECT_COLUMN_NAME,
):
    book = pd.ExcelFile(BytesIO(data))
    best_rows = []
    best_sheet = ""

    for sheet_name in book.sheet_names:
        df = pd.read_excel(book, sheet_name=sheet_name, header=None, dtype=object)
        parsed = _rows_from_matrix(_dataframe_matrix(df), partner_header, type_header, project_header)
        if len(parsed) > len(best_rows):
            best_rows = parsed
            best_sheet = str(sheet_name)

    if not best_rows:
        raise ValueError(
            f'Could not find an Excel sheet with "{partner_header}" and "{type_header}" columns.'
        )
    return best_rows, best_sheet


def parse_partner_type_rows_from_csv(
    data,
    partner_header=PARTNER_COLUMN_NAME,
    type_header=TYPE_COLUMN_NAME,
    project_header=PROJECT_COLUMN_NAME,
):
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            df = pd.read_csv(
                BytesIO(data),
                header=None,
                dtype=object,
                sep=None,
                engine="python",
                encoding=encoding,
            )
            parsed = _rows_from_matrix(_dataframe_matrix(df), partner_header, type_header, project_header)
            if parsed:
                return parsed
        except Exception as error:
            last_error = error

    raise ValueError(
        f'Could not find CSV columns "{partner_header}" and "{type_header}".'
        + (f" Details: {last_error}" if last_error else "")
    )


def load_partner_type_rows_from_upload(uploaded_file):
    if uploaded_file is None:
        raise ValueError("Source file is not uploaded.")

    name = str(getattr(uploaded_file, "name", "") or "source").strip()
    suffix = name.lower().rsplit(".", 1)[-1] if "." in name else ""
    data = uploaded_file.getvalue()

    if suffix == "doc":
        rows = parse_partner_type_rows_from_doc(data)
        return rows, f"{name} · Confluence Word export"
    if suffix == "docx":
        rows = parse_partner_type_rows_from_docx(data)
        return rows, f"{name} · Word export"
    if suffix in ("xlsx", "xlsm"):
        rows, sheet = parse_partner_type_rows_from_excel(data)
        title = f"{name} · sheet: {sheet}" if sheet else name
        return rows, title
    if suffix == "csv":
        rows = parse_partner_type_rows_from_csv(data)
        return rows, name

    raise ValueError("Unsupported source file. Upload .doc, .docx, .xlsx, .xlsm, or .csv.")


def _normalized_value(value):
    return normalize_space(value).casefold()


def _collapse_entries(entries):
    valid = [entry for entry in entries if entry.get("partner_type")]
    if not valid:
        return None, "missing_type"

    distinct_values = {_normalized_value(entry["partner_type"]) for entry in valid}
    if len(distinct_values) > 1:
        return None, "conflict"
    return valid[0], "ok"


def build_partner_type_lookup(rows):
    partner_exact = defaultdict(list)
    partner_loose = defaultdict(list)
    project_exact = defaultdict(list)
    project_loose = defaultdict(list)
    prepared = []

    for row in rows:
        partner = normalize_space(row.get("Partner"))
        project = normalize_space(row.get("Project name"))
        partner_type = normalize_space(row.get("Partner Type"))
        if not partner and not project:
            continue

        entry = {
            "partner": partner,
            "project": project,
            "partner_type": partner_type,
        }
        prepared.append(entry)
        if partner:
            partner_exact[normalize_partner(partner)].append(entry)
            partner_loose[normalize_partner_loose(partner)].append(entry)
        if project and project not in {"-", "—", "–"}:
            project_exact[normalize_partner(project)].append(entry)
            project_loose[normalize_partner_loose(project)].append(entry)

    return {
        "partner_exact": partner_exact,
        "partner_loose": partner_loose,
        "project_exact": project_exact,
        "project_loose": project_loose,
        "rows": prepared,
    }


def _resolve_partner_type_match(entries, source_kind, match_name):
    if not entries:
        return None, "", match_name

    if source_kind == "Project":
        parent_partners = {normalize_partner(entry.get("partner")) for entry in entries if entry.get("partner")}
        if len(parent_partners) > 1:
            return None, "Project name match is ambiguous across multiple partners", match_name
    else:
        source_partners = {normalize_partner(entry.get("partner")) for entry in entries if entry.get("partner")}
        if len(source_partners) > 1:
            return None, "Partner match is ambiguous in the source file", match_name

    entry, state = _collapse_entries(entries)
    if state == "conflict":
        return None, f"Conflicting Partner Type values for matched {source_kind.lower()}", match_name
    if state == "missing_type":
        return None, "Partner Type is empty in the source file", match_name
    return entry, "", match_name


def match_partner_type(lookup, partner_value):
    partner_value = normalize_space(partner_value)
    if not partner_value:
        return None, "Partner / Project is empty", ""

    found_errors = []
    for candidate, origin in partner_match_candidates(partner_value):
        exact_key = normalize_partner(candidate)
        loose_key = normalize_partner_loose(candidate)
        origin_suffix = "" if origin == "Original" else f" · {origin}"

        checks = [
            (lookup["project_exact"].get(exact_key, []), "Project", f"Project exact{origin_suffix}"),
            (lookup["partner_exact"].get(exact_key, []), "Partner", f"Partner exact{origin_suffix}"),
            (lookup["project_loose"].get(loose_key, []), "Project", f"Project normalized{origin_suffix}"),
            (lookup["partner_loose"].get(loose_key, []), "Partner", f"Partner normalized{origin_suffix}"),
        ]

        for entries, source_kind, match_name in checks:
            if not entries:
                continue
            entry, error, resolved_match = _resolve_partner_type_match(entries, source_kind, match_name)
            if not error:
                return entry, "", resolved_match
            found_errors.append((error, resolved_match))

    if found_errors:
        return None, found_errors[0][0], found_errors[0][1]
    return None, "Partner / Project not found in Partner or Project name columns", ""


def _field_values(value):
    if value is None:
        return []
    if isinstance(value, list):
        result = []
        for item in value:
            text = field_to_text(item).strip()
            if text:
                result.append(text)
        return result
    text = field_to_text(value).strip()
    return [text] if text else []


def _is_empty_field(value):
    return value is None or value == "" or value == [] or value == {}


def build_partner_type_preview_rows(issues, base_url, partner_field_id, type_field_id, lookup):
    actionable = []
    blocked = []

    for issue in issues:
        fields = issue.get("fields", {}) or {}
        key = issue.get("key", "")
        common = {
            "Key": key,
            "Open": f"{clean_base_url(base_url)}/browse/{key}",
            "Summary": compact(fields.get("summary", ""), 160),
            "Status": field_to_text(fields.get("status")),
        }

        current_type = fields.get(type_field_id)
        if not _is_empty_field(current_type):
            blocked.append({
                **common,
                "Partner": field_to_text(fields.get(partner_field_id)),
                "Reason": "Partner Type is already filled",
            })
            continue

        partner_values = _field_values(fields.get(partner_field_id))
        if not partner_values:
            blocked.append({**common, "Partner": "", "Reason": "Partner / Project is empty"})
            continue
        if len(partner_values) != 1:
            blocked.append({
                **common,
                "Partner": ", ".join(partner_values),
                "Reason": "Partner / Project has multiple values; automatic choice is disabled",
            })
            continue

        partner_value = partner_values[0]
        entry, error, match_type = match_partner_type(lookup, partner_value)
        if error:
            blocked.append({**common, "Partner": partner_value, "Reason": error})
            continue

        actionable.append({
            "Select": True,
            **common,
            "Partner": partner_value,
            "Source Partner": entry["partner"],
            "Source Project": entry.get("project", ""),
            "New Partner Type": entry["partner_type"],
            "Match": match_type,
        })

    return actionable, blocked


def _allowed_value_payload(field_meta, partner_type):
    allowed = field_meta.get("allowedValues") or [] if isinstance(field_meta, dict) else []
    wanted = _normalized_value(partner_type)

    for item in allowed:
        if not isinstance(item, dict):
            continue
        raw = str(item.get("value") or item.get("name") or "").strip()
        if _normalized_value(raw) != wanted:
            continue
        if item.get("id") is not None:
            return {"id": str(item.get("id"))}
        if item.get("value") is not None:
            return {"value": item.get("value")}
        if item.get("name") is not None:
            return {"name": item.get("name")}
    return None


def candidate_partner_type_payloads(editmeta, field_id, partner_type):
    field_meta = (((editmeta or {}).get("fields") or {}).get(field_id) or {}) if isinstance(editmeta, dict) else {}
    allowed_payload = _allowed_value_payload(field_meta, partner_type)
    schema = field_meta.get("schema") or {}
    schema_type = str(schema.get("type") or "").lower()
    custom = str(schema.get("custom") or "").lower()

    candidates = []
    if schema_type == "array":
        if allowed_payload is not None:
            candidates.append([allowed_payload])
        candidates.extend([[{"value": partner_type}], [partner_type]])
    else:
        if allowed_payload is not None:
            candidates.append(allowed_payload)
        if schema_type == "string":
            candidates.append(partner_type)
        elif schema_type == "option" or "select" in custom:
            candidates.append({"value": partner_type})
        else:
            candidates.extend([{"value": partner_type}, partner_type])

    deduped = []
    seen = set()
    for candidate in candidates:
        marker = repr(candidate)
        if marker not in seen:
            seen.add(marker)
            deduped.append(candidate)
    return deduped


def update_partner_type(base_url, api_version, auth_type, username, token, issue_key, field_id, partner_type):
    editmeta = None
    try:
        editmeta = jira_get_issue_editmeta(base_url, api_version, auth_type, username, token, issue_key)
    except Exception:
        editmeta = None

    errors = []
    for payload in candidate_partner_type_payloads(editmeta, field_id, partner_type):
        try:
            jira_update_issue_fields(
                base_url,
                api_version,
                auth_type,
                username,
                token,
                issue_key,
                {field_id: payload},
            )
            return
        except Exception as error:
            errors.append(summarize_exception(error))

    raise RuntimeError(errors[-1] if errors else "Jira rejected the Partner Type update")


def _clear_partner_type_state():
    for key in [
        "partner_type_actionable",
        "partner_type_blocked",
        "partner_type_source_title",
        "partner_type_source_rows",
        "partner_type_field_ids",
        "partner_type_apply_results",
        "partner_type_confirm",
    ]:
        st.session_state.pop(key, None)


def render_partner_type_maintenance():
    st.markdown(
        """<div class="feature-panel">
        <div class="step-kicker">Data maintenance · Partner master data</div>
        <div class="feature-title">Partner Type Sync</div>
        <div class="feature-text">Use the same weekly Word export. The helper finds each partner, reads Partner Type, blocks missing or conflicting values, and updates Jira only after preview and confirmation.</div>
        </div>""",
        unsafe_allow_html=True,
    )

    jira_base_url, api_version, auth_type, username, token, _ = current_jira_context()
    default_jql = str(PARTNER_TYPE_CONFIG.get("jql", "") or DEFAULT_PARTNER_TYPE_JQL)

    step1, step2, step3 = st.columns(3)
    with step1:
        st.markdown(
            """<div class="mini-card"><div class="step-kicker">Step 01</div><div class="tool-card-title">Upload source</div><div class="tool-card-text">Use the same fresh Partner Information Word export (.doc or .docx).</div></div>""",
            unsafe_allow_html=True,
        )
    with step2:
        st.markdown(
            """<div class="mini-card"><div class="step-kicker">Step 02</div><div class="tool-card-title">Match Partner Type</div><div class="tool-card-text">Partner names are normalized, but ambiguous matches are never guessed.</div></div>""",
            unsafe_allow_html=True,
        )
    with step3:
        st.markdown(
            """<div class="mini-card"><div class="step-kicker">Step 03</div><div class="tool-card-title">Confirm update</div><div class="tool-card-text">Only selected safe rows are written to Jira.</div></div>""",
            unsafe_allow_html=True,
        )

    st.write("")
    source_col, action_col = st.columns([4.2, 1.1])
    with source_col:
        st.markdown("### Source file")
        st.caption(f'The file must contain columns **{PARTNER_COLUMN_NAME}** and **{TYPE_COLUMN_NAME}**.')
        uploaded_file = st.file_uploader(
            "Partner Information file",
            type=["doc", "docx", "xlsx", "xlsm", "csv"],
            key="partner_type_source_file",
            help="Upload the same Confluence Word export (.doc or .docx) used for Partner Tier Sync.",
            label_visibility="collapsed",
        )
    with action_col:
        st.write("")
        st.write("")
        clear_clicked = st.button("Clear preview", use_container_width=True, key="partner_type_clear")

    if uploaded_file is not None:
        st.success(f"Source selected: {uploaded_file.name}")

    with st.expander("JQL used to find empty Partner Type tickets", expanded=False):
        jql = st.text_area(
            "JQL",
            value=default_jql,
            height=260,
            key="partner_type_jql",
            label_visibility="collapsed",
        )

    c1, c2, c3 = st.columns([1.2, 1.2, 3])
    preview_clicked = c1.button("Preview sync", type="primary", use_container_width=True, key="partner_type_preview")
    c2.caption("Preview never changes Jira.")
    c3.caption("Missing Partner Type, partner mismatches, and conflicting source rows are blocked.")

    if clear_clicked:
        _clear_partner_type_state()
        st.rerun()

    if preview_clicked:
        _clear_partner_type_state()
        if not require_jira_settings():
            return
        if uploaded_file is None:
            st.error("Upload the Partner Information Word (.doc/.docx), Excel, or CSV file first.")
            return
        if not jql.strip():
            st.error("JQL is empty.")
            return

        try:
            with st.spinner("Reading Partner Type from the source and building a safe Jira preview..."):
                rows, source_title = load_partner_type_rows_from_upload(uploaded_file)
                lookup = build_partner_type_lookup(rows)

                field_ids = jira_get_field_ids_by_name(
                    jira_base_url,
                    api_version,
                    auth_type,
                    username,
                    token,
                    [PARTNER_FIELD_NAME, PARTNER_TYPE_FIELD_NAME],
                )
                partner_field_id = field_ids.get(PARTNER_FIELD_NAME)
                type_field_id = field_ids.get(PARTNER_TYPE_FIELD_NAME)
                if not partner_field_id:
                    raise RuntimeError(f'Jira field "{PARTNER_FIELD_NAME}" was not found.')
                if not type_field_id:
                    raise RuntimeError(
                        f'Jira field "{PARTNER_TYPE_FIELD_NAME}" was not found. '
                        'If your Jira field has a different name, set partner_type_field_name under [partner_type] in Secrets.'
                    )

                issues = jira_search(
                    jira_base_url,
                    api_version,
                    auth_type,
                    username,
                    token,
                    jql,
                    ["summary", "status", "updated", partner_field_id, type_field_id],
                )
                actionable, blocked = build_partner_type_preview_rows(
                    issues,
                    jira_base_url,
                    partner_field_id,
                    type_field_id,
                    lookup,
                )

                st.session_state.partner_type_actionable = actionable
                st.session_state.partner_type_blocked = blocked
                st.session_state.partner_type_source_title = source_title
                st.session_state.partner_type_source_rows = len(rows)
                st.session_state.partner_type_field_ids = {
                    "partner": partner_field_id,
                    "type": type_field_id,
                }
        except Exception as error:
            st.error("Preview failed")
            st.code(summarize_exception(error, limit=1200))
            return

    actionable = st.session_state.get("partner_type_actionable")
    blocked = st.session_state.get("partner_type_blocked")
    if actionable is None and blocked is None:
        st.info("Upload the current source file and load a preview. Nothing is changed in Jira until final confirmation.")
        return

    actionable = actionable or []
    blocked = blocked or []
    total = len(actionable) + len(blocked)
    source_rows = int(st.session_state.get("partner_type_source_rows", 0))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Jira tickets", total)
    m2.metric("Ready to update", len(actionable))
    m3.metric("Blocked", len(blocked))
    m4.metric("Source rows", source_rows)
    st.caption(f'Source: **{st.session_state.get("partner_type_source_title", "Uploaded file")}**')

    if actionable:
        st.subheader("Ready to update")
        st.caption("Matches are checked against both Partner and Project name. Only one safe source value is eligible.")
        action_df = st.data_editor(
            pd.DataFrame(actionable),
            hide_index=True,
            use_container_width=True,
            key="partner_type_editor",
            disabled=[
                "Key",
                "Open",
                "Summary",
                "Status",
                "Partner",
                "Source Partner",
                "Source Project",
                "New Partner Type",
                "Match",
            ],
            column_config={
                "Select": st.column_config.CheckboxColumn("Select", default=True),
                "Open": st.column_config.LinkColumn("Open", display_text="Open"),
                "Summary": st.column_config.TextColumn("Summary", width="large"),
                "New Partner Type": st.column_config.TextColumn("New Partner Type", width="medium"),
            },
        )
    else:
        action_df = pd.DataFrame()
        st.warning("No safe automatic updates found.")

    if blocked:
        with st.expander(f"Blocked / needs manual check ({len(blocked)})", expanded=True):
            st.dataframe(
                pd.DataFrame(blocked),
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Open": st.column_config.LinkColumn("Open", display_text="Open"),
                    "Summary": st.column_config.TextColumn("Summary", width="large"),
                    "Reason": st.column_config.TextColumn("Reason", width="large"),
                },
            )

    selected_rows = []
    if not action_df.empty:
        selected_rows = action_df.loc[action_df["Select"] == True].to_dict("records")

    st.divider()
    confirmed = st.checkbox(
        f"I checked the preview and want to update {len(selected_rows)} selected ticket(s)",
        key="partner_type_confirm",
    )
    apply_clicked = st.button(
        f"Update Partner Type ({len(selected_rows)})",
        type="primary",
        use_container_width=True,
        disabled=not confirmed or not selected_rows,
        key="partner_type_apply",
    )

    if apply_clicked:
        type_field_id = (st.session_state.get("partner_type_field_ids") or {}).get("type")
        if not type_field_id:
            st.error("Partner Type field id is missing. Reload the preview.")
            return

        results = []
        progress = st.progress(0)
        status_box = st.empty()

        for index, row in enumerate(selected_rows, start=1):
            key = str(row.get("Key", "")).strip()
            partner_type = normalize_space(row.get("New Partner Type"))
            status_box.info(f"Updating {index}/{len(selected_rows)} · {key} → {partner_type}")
            try:
                update_partner_type(
                    jira_base_url,
                    api_version,
                    auth_type,
                    username,
                    token,
                    key,
                    type_field_id,
                    partner_type,
                )
                results.append({
                    "Key": key,
                    "Partner Type": partner_type,
                    "Status": "Success",
                    "Details": "Partner Type updated",
                })
            except Exception as error:
                results.append({
                    "Key": key,
                    "Partner Type": partner_type,
                    "Status": "Failed",
                    "Details": summarize_exception(error),
                })
            progress.progress(index / len(selected_rows))

        st.session_state.partner_type_apply_results = results
        success_count = sum(item["Status"] == "Success" for item in results)
        failed_count = len(results) - success_count
        if failed_count:
            status_box.warning(f"Finished: {success_count} updated, {failed_count} failed.")
        else:
            status_box.success(f"Finished: {success_count} ticket(s) updated successfully.")

    results = st.session_state.get("partner_type_apply_results")
    if results:
        st.subheader("Update results")
        st.dataframe(pd.DataFrame(results), hide_index=True, use_container_width=True)
