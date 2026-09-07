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
3. Matches the Jira `Partner / Project` against **both** source columns: `Partner` and `Project name`.
4. Extracts the numeric tier from values such as `Group 4`, `Group 4(New)`, `GROUP 4`, or ` group   4 `.
5. Shows `Ready to update` and `Blocked / needs manual check` before any Jira write.
6. Updates only selected rows after explicit confirmation.

It never guesses when the partner/project is missing, ambiguous, duplicated with conflicting values, or the category does not contain one clear tier number.

Matching rules are intentionally conservative:

- `Solibet` can match `Project name = Solibet` even when its parent `Partner = GrandPashaBet`.
- `albatross-Solibet` can safely fall back to the `Solibet` suffix, but only when that suffix resolves uniquely in `Partner` or `Project name`.
- `GrandPashaBet-ALL` first becomes `GrandPashaBet`. If a same-named project exists, that exact project row is preferred. Otherwise Partner Tier may use the parent partner only when all matching source rows resolve to the same tier.
- Duplicate project names under different parent partners are blocked instead of guessed.

### Partner Type Sync

The second maintenance tool uses the same Partner Information export, reads the source column `Solution type`, and writes that value to the Jira field `Partner Type`.

It:

1. Finds Jira tickets where `Partner Type` is empty.
2. Matches by `Partner / Project` against both `Partner` and `Project name`, using the same safe exact/normalized/prefix-suffix logic.
3. Reads `Solution type` from the matched source row and blocks missing, ambiguous, or conflicting source values.
4. Shows the proposed `New Partner Type` before writing anything.
5. Uses Jira edit metadata where available so select-option fields can be updated correctly.

For Jira Partner Type, `Solution type` from the project-level source row wins over parent-level data. This matters for partner families such as GrandPashaBet where different projects can have different types. For an `-ALL` value, a same-named project is used when present; otherwise mixed child types remain blocked.

## Supported source files

Both Partner Tier and Partner Type Sync accept:

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

## v5 matching fix

- Jira values rendered as `Partner - Project` now handle repeated pairs safely, e.g. `Festwin - Festwin` -> `Festwin`.
- Common Unicode dash characters are treated as separators as well.
- The rule is deterministic: only two identical normalized sides are collapsed, so `GrandPashaBet - Solibet` is not reduced to the parent partner.
