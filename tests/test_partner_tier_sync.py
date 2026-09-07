import sys
import types
from io import BytesIO

from docx import Document

try:
    import streamlit  # noqa: F401
except ModuleNotFoundError:
    fake = types.ModuleType("streamlit")
    fake.secrets = {}
    sys.modules["streamlit"] = fake

from tools.partner_tier_sync import (
    build_partner_lookup,
    extract_tier_from_category,
    match_partner,
    normalize_partner,
    parse_partner_rows_from_html,
    parse_partner_rows_from_doc,
    parse_partner_rows_from_docx,
    partner_match_candidates,
)


def test_category_variations():
    cases = {
        "Group 4": 4,
        "Group 4(New)": 4,
        " group   4 ": 4,
        "GROUP 4": 4,
        "Tier 4": 4,
    }
    for raw, expected in cases.items():
        tier, error = extract_tier_from_category(raw)
        assert tier == expected
        assert error == ""


def test_empty_and_ambiguous_category_are_blocked():
    assert extract_tier_from_category("")[0] is None
    assert extract_tier_from_category("Group A")[0] is None
    assert extract_tier_from_category("4 / 5")[0] is None


def test_partner_matching_tolerates_spacing_but_not_ambiguity():
    lookup = build_partner_lookup([
        {"Partner": "1 Bet Pro", "Project name": "", "Partner Category": "Group 5"},
        {"Partner": "188bet", "Project name": "", "Partner Category": "Group 4(New)"},
    ])
    entry, error, match = match_partner(lookup, "1BetPro")
    assert error == ""
    assert entry["tier"] == 5
    assert match.startswith("Partner normalized")


def test_conflicting_duplicate_is_blocked():
    lookup = build_partner_lookup([
        {"Partner": "SamePartner", "Project name": "A", "Partner Category": "Group 3"},
        {"Partner": "SamePartner", "Project name": "B", "Partner Category": "Group 4"},
    ])
    entry, error, _ = match_partner(lookup, "SamePartner")
    assert entry is None
    assert "Conflicting" in error


def test_project_name_is_used_before_parent_partner():
    lookup = build_partner_lookup([
        {"Partner": "GrandPashaBet", "Project name": "Betsin", "Partner Category": "Group 4"},
        {"Partner": "GrandPashaBet", "Project name": "Solibet", "Partner Category": "Group 4(New)"},
    ])
    entry, error, match = match_partner(lookup, "Solibet")
    assert error == ""
    assert entry["partner"] == "GrandPashaBet"
    assert entry["project"] == "Solibet"
    assert entry["tier"] == 4
    assert match.startswith("Project exact")


def test_prefixed_jira_value_can_resolve_to_project_suffix():
    lookup = build_partner_lookup([
        {"Partner": "GrandPashaBet", "Project name": "Solibet", "Partner Category": "Group 4"},
    ])
    entry, error, match = match_partner(lookup, "albatross-Solibet")
    assert error == ""
    assert entry["project"] == "Solibet"
    assert "Suffix" in match


def test_all_suffix_uses_base_name_and_prefers_same_named_project():
    lookup = build_partner_lookup([
        {"Partner": "GrandPashaBet", "Project name": "Betsin", "Partner Category": "Group 4"},
        {"Partner": "GrandPashaBet", "Project name": "GrandPashaBet", "Partner Category": "Group 4(New)"},
        {"Partner": "GrandPashaBet", "Project name": "Solibet", "Partner Category": "Group 4"},
    ])
    entry, error, match = match_partner(lookup, "GrandPashaBet-ALL")
    assert error == ""
    assert entry["project"] == "GrandPashaBet"
    assert entry["tier"] == 4
    assert "ALL" in match


def test_all_suffix_can_fall_back_to_partner_when_tier_is_consistent():
    lookup = build_partner_lookup([
        {"Partner": "Umbrella", "Project name": "One", "Partner Category": "Group 2"},
        {"Partner": "Umbrella", "Project name": "Two", "Partner Category": "Group 2(New)"},
    ])
    entry, error, match = match_partner(lookup, "Umbrella-ALL")
    assert error == ""
    assert entry["partner"] == "Umbrella"
    assert entry["tier"] == 2
    assert match.startswith("Partner exact")


def test_duplicate_project_across_parents_is_blocked():
    lookup = build_partner_lookup([
        {"Partner": "Parent A", "Project name": "SharedProject", "Partner Category": "Group 2"},
        {"Partner": "Parent B", "Project name": "SharedProject", "Partner Category": "Group 2"},
    ])
    entry, error, _ = match_partner(lookup, "SharedProject")
    assert entry is None
    assert "multiple partners" in error


def test_candidate_generation():
    assert ("GrandPashaBet", "ALL → base") in partner_match_candidates("GrandPashaBet-ALL")
    assert ("Solibet", "Suffix") in partner_match_candidates("albatross-Solibet")


def test_html_table_parser():
    html = """
    <table>
      <tr><th>Partner</th><th>Project name</th><th>Partner Category</th></tr>
      <tr><td>1betpro</td><td>-</td><td> Group 5 </td></tr>
      <tr><td>188bet</td><td>-</td><td>Group 4(New)</td></tr>
    </table>
    """
    rows = parse_partner_rows_from_html(html)
    assert rows[0]["Partner"] == "1betpro"
    assert rows[0]["Project name"] == "-"
    assert rows[1]["Partner Category"] == "Group 4(New)"


def test_html_rowspan_keeps_partner_and_project_columns_aligned():
    html = """
    <table>
      <tr><th>Partner</th><th>Project name</th><th>Partner Category</th></tr>
      <tr><td rowspan="3">GrandPashaBet</td><td>Betsin</td><td>Group 4</td></tr>
      <tr><td>Solibet</td><td>Group 4(New)</td></tr>
      <tr><td>GrandPashaBet</td><td>Group 4</td></tr>
    </table>
    """
    rows = parse_partner_rows_from_html(html)
    assert rows[1]["Partner"] == "GrandPashaBet"
    assert rows[1]["Project name"] == "Solibet"
    assert rows[1]["Partner Category"] == "Group 4(New)"


def test_word_export_table_parser():
    doc = Document()
    table = doc.add_table(rows=3, cols=3)
    table.cell(0, 0).text = "Partner"
    table.cell(0, 1).text = "Project name"
    table.cell(0, 2).text = "Partner Category"
    table.cell(1, 0).text = "1betpro"
    table.cell(1, 1).text = "ProjectOne"
    table.cell(1, 2).text = "Group 5"
    table.cell(2, 0).text = "188bet"
    table.cell(2, 1).text = "ProjectTwo"
    table.cell(2, 2).text = "Group 4(New)"

    buffer = BytesIO()
    doc.save(buffer)
    rows = parse_partner_rows_from_docx(buffer.getvalue())
    assert rows[0] == {"Partner": "1betpro", "Project name": "ProjectOne", "Partner Category": "Group 5"}
    assert rows[1]["Project name"] == "ProjectTwo"
    assert rows[1]["Partner Category"] == "Group 4(New)"


def test_confluence_doc_html_export_parser():
    data = b"""<html><body><table>
    <tr><th>Partner</th><th>Project name</th><th>Partner Category</th><th>Partner Type</th></tr>
    <tr><td rowspan=\"2\">GrandPashaBet</td><td>Betsin</td><td>Group 4</td><td>Builder</td></tr>
    <tr><td>Solibet</td><td>Group 4(New)</td><td>Casweb</td></tr>
    </table></body></html>"""
    rows = parse_partner_rows_from_doc(data)
    assert rows[0] == {"Partner": "GrandPashaBet", "Project name": "Betsin", "Partner Category": "Group 4"}
    assert rows[1]["Partner"] == "GrandPashaBet"
    assert rows[1]["Project name"] == "Solibet"
    assert rows[1]["Partner Category"] == "Group 4(New)"
