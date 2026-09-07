import sys
import types

try:
    import streamlit  # noqa: F401
except ModuleNotFoundError:
    fake = types.ModuleType("streamlit")
    fake.secrets = {}
    sys.modules["streamlit"] = fake

from io import BytesIO

from docx import Document

from tools.partner_type_sync import (
    build_partner_type_lookup,
    match_partner_type,
    parse_partner_type_rows_from_doc,
    parse_partner_type_rows_from_docx,
)


def test_partner_type_word_parser():
    doc = Document()
    table = doc.add_table(rows=3, cols=4)
    table.cell(0, 0).text = "Partner"
    table.cell(0, 1).text = "Project name"
    table.cell(0, 2).text = "Partner Category"
    table.cell(0, 3).text = "Partner Type"
    table.cell(1, 0).text = "1betpro"
    table.cell(1, 3).text = "B2B"
    table.cell(2, 0).text = "188bet"
    table.cell(2, 3).text = "White Label"

    buffer = BytesIO()
    doc.save(buffer)
    rows = parse_partner_type_rows_from_docx(buffer.getvalue())

    assert rows[0] == {"Partner": "1betpro", "Partner Type": "B2B"}
    assert rows[1]["Partner Type"] == "White Label"


def test_partner_type_matching_tolerates_spacing():
    lookup = build_partner_type_lookup([
        {"Partner": "1 Bet Pro", "Partner Type": "B2B"},
    ])
    entry, error, match = match_partner_type(lookup, "1BetPro")
    assert error == ""
    assert entry["partner_type"] == "B2B"
    assert match == "Normalized"


def test_empty_partner_type_is_blocked():
    lookup = build_partner_type_lookup([
        {"Partner": "188bet", "Partner Type": ""},
    ])
    entry, error, _ = match_partner_type(lookup, "188bet")
    assert entry is None
    assert "empty" in error.lower()


def test_conflicting_partner_types_are_blocked():
    lookup = build_partner_type_lookup([
        {"Partner": "Same Partner", "Partner Type": "B2B"},
        {"Partner": "Same Partner", "Partner Type": "White Label"},
    ])
    entry, error, _ = match_partner_type(lookup, "Same Partner")
    assert entry is None
    assert "Conflicting" in error


def test_partner_type_confluence_doc_html_export():
    data = b"""<html><body><table>
    <tr><th>Partner</th><th>Partner Category</th><th>Partner Type</th></tr>
    <tr><td>1betpro</td><td>Group 5</td><td>B2B</td></tr>
    <tr><td>188bet</td><td>Group 4</td><td>White Label</td></tr>
    </table></body></html>"""
    rows = parse_partner_type_rows_from_doc(data)
    assert rows[0] == {"Partner": "1betpro", "Partner Type": "B2B"}
    assert rows[1]["Partner Type"] == "White Label"
