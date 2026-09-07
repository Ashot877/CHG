import streamlit as st

from core.session import current_jira_context
from core.ui import render_hero

def page_dashboard():
    render_hero(
        "Change Helper",
        "One internal workspace for Change Management: handovers, weekly follow-up, safe data maintenance, ROX domains, and Excel utilities.",
        ["AM Handover", "Follow-up", "Data Maintenance", "ROX", "Excel"],
    )

    c1, c2, c3, c4 = st.columns(4)
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
              <div class="tool-card-title">⏱️ Weekly Tasks Helper</div>
              <div class="tool-card-text">Run SLA follow-up and safe weekly data-maintenance tasks, including Partner Tier synchronization.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="mini-card">
              <div class="tool-card-title">📡 ROX Domain Grouper</div>
              <div class="tool-card-text">Paste domains, auto-detect projects, remove duplicates, and produce a clean ready-to-copy message.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
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
