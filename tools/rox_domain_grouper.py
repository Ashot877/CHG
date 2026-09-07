import re
from collections import defaultdict

import streamlit as st

from core.ui import render_hero

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

