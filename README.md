# Change Helper — refactored

The original single-file Streamlit app was split by responsibility without changing the working logic of AM Handover, ROX Domain Grouper, Excel Splitter, or the existing Weekly Follow-up flow.

## New structure

- `app.py` — entry point and routing
- `core/` — config, Jira API, session/auth, shared UI/styles, generic formatters
- `pages/` — Dashboard and Settings
- `tools/am_handover.py` — existing AM Handover
- `tools/weekly_tasks.py` — Weekly Tasks shell + existing Follow-up flow
- `tools/partner_tier_sync.py` — new Data Maintenance → Partner Tier Sync
- `tools/rox_domain_grouper.py` — existing ROX tool
- `tools/excel_splitter.py` — existing Excel tool

Run it with:

```bash
streamlit run app.py
```

## Partner Tier Sync behavior

1. Runs the configured JQL and finds Jira tickets whose `Partner tier` should be empty.
2. Reads the configured Confluence page and finds the table containing `Partner` and `Partner Category`.
3. Matches `Partner / Project` safely:
   - exact normalized match first;
   - then a whitespace/separator-insensitive match only when that match is unique.
4. Extracts the tier number from Partner Category:
   - `Group 4`
   - `Group 4(New)`
   - ` group   4 `
   - `GROUP 4`
   all resolve to tier `4`.
5. It **does not update** a ticket when:
   - `Partner / Project` is empty;
   - the partner is not found in Confluence;
   - the Confluence partner match is ambiguous;
   - `Partner Category` is empty;
   - no clear tier number can be extracted;
   - duplicate Confluence rows contain conflicting tiers;
   - the Jira ticket unexpectedly already has Partner tier filled.
6. Shows two preview tables: `Ready to update` and `Blocked / needs manual check`.
7. Jira writes happen only after selecting rows and checking the explicit confirmation box.

## Confluence access

Add the `[partner_tier]` section from `.streamlit/secrets.example.toml` to your real `.streamlit/secrets.toml`.

If Jira and Confluence accept the same PAT, keep:

```toml
inherit_jira_credentials = true
```

Otherwise configure a dedicated Confluence token in the real secrets file. The token is never placed in the source code.

## Notes

The Confluence loader supports common page-ID URLs (`pageId=...` and `/pages/<id>/...`) and falls back to reading the page URL directly. It also has a conservative table heuristic if the rendered Confluence table headers are unusual.
