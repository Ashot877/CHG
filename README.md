# Change Helper

Internal Streamlit workspace for recurring Change Management tasks.

## Structure

- `app.py` — single app entry point and routing
- `core/` — Jira API, auth/session, shared UI and helpers
- `tools/weekly_tasks.py` — Weekly Operations shell + existing Follow-up flow
- `tools/partner_tier_sync.py` — Data Maintenance → Partner Tier Sync
- `tools/partner_type_sync.py` — Data Maintenance → Partner Type Sync
- `tools/am_handover.py` — AM Handover
- `tools/rox_domain_grouper.py` — ROX Domains
- `tools/excel_splitter.py` — Excel Splitter

Run:

```bash
streamlit run app.py
```

## Weekly Operations → Data Maintenance

There are now two separate maintenance tools.

### Partner Tier Sync

The helper:

1. Finds Jira tickets where `Partner tier` is empty.
2. Reads `Partner` + `Partner Category` from the weekly Partner Information export.
3. Matches the Jira `Partner / Project` safely.
4. Extracts the numeric tier from values such as `Group 4`, `Group 4(New)`, `GROUP 4`, or ` group   4 `.
5. Shows `Ready to update` and `Blocked / needs manual check` before any Jira write.
6. Updates only selected rows after explicit confirmation.

It never guesses when the partner is missing, ambiguous, duplicated with conflicting values, or the category does not contain one clear tier number.

### Partner Type Sync

The second maintenance tool uses the same Partner Information export but reads the `Partner Type` column.

It:

1. Finds Jira tickets where `Partner Type` is empty.
2. Matches by `Partner / Project` using the same safe exact/normalized logic.
3. Blocks missing, ambiguous, or conflicting source values.
4. Shows the proposed `New Partner Type` before writing anything.
5. Uses Jira edit metadata where available so select-option fields can be updated correctly.

## Supported source files

Both Partner Tier and Partner Type accept:

- `.doc` — including the Word-compatible HTML/MHTML format commonly produced by Confluence Export to Word
- `.docx`
- `.xlsx`
- `.xlsm`
- `.csv`

The app detects content rather than trusting only the extension, so a DOCX payload named `.doc` is also handled.

For safety, a true old binary Word 97-2003 OLE `.doc` is not parsed by guessing table boundaries. If such a file is encountered, the UI gives a clear message to Save As `.docx` instead.

## Dashboard / Settings cleanup

Dashboard and Settings are not part of the app anymore.

Two protections prevent old stale `pages/dashboard.py` / `pages/settings.py` files from appearing in Streamlit navigation:

- `app.py` runs the application through a hidden `st.navigation` page on modern Streamlit versions, which disables legacy `pages/` routing.
- `.streamlit/config.toml` also sets `client.showSidebarNavigation = false` as a fallback before the first render.

For a clean repository, delete old `pages/dashboard.py` and `pages/settings.py` once. They are not included in this project.

## Secrets

Keep the real `.streamlit/secrets.toml` outside Git. The included `.streamlit/secrets.example.toml` only documents optional configuration keys.
