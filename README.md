# Change Helper — internal operations workspace

The original single-file Streamlit app was split by responsibility without changing the working logic of AM Handover, ROX Domain Grouper, Excel Splitter, or the existing Weekly Follow-up flow.

## New structure

- `app.py` — entry point and routing
- `core/` — config, Jira API, session/auth, shared UI/styles, generic formatters
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
2. Loads the weekly Partner Information source. Recommended: Confluence → **Export to Word** → upload the `.docx`. `.xlsx`, `.xlsm`, and `.csv` are also supported. Direct Confluence URL remains optional for environments that can reach the corporate network.
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
   - the partner is not found in the uploaded source;
   - the normalized source match is ambiguous;
   - `Partner Category` is empty;
   - no clear tier number can be extracted;
   - duplicate source rows contain conflicting tiers;
   - the Jira ticket unexpectedly already has Partner tier filled.
6. Shows two preview tables: `Ready to update` and `Blocked / needs manual check`.
7. Jira writes happen only after selecting rows and checking the explicit confirmation box.

## Weekly source flow

The recommended flow for Streamlit Cloud is:

1. Open the Partner Information page in Confluence.
2. Choose **Export to Word**.
3. Upload the exported `.docx` in `Weekly Tasks Helper → Data Maintenance → Partner Tier Sync`.
4. Click `Preview sync`.
5. Review `Ready to update` and `Blocked / needs manual check`.
6. Confirm and update only the selected safe rows.

The uploader scans Word tables for `Partner` and `Partner Category`. Excel files are scanned across all sheets and tolerate title rows above the actual header.

## Optional Confluence access

Direct Confluence URL mode is still available for installations running inside the corporate network. Add the `[partner_tier]` section from `.streamlit/secrets.example.toml` only if you want that mode. Streamlit Cloud usually cannot resolve internal-only Confluence hosts.

## 2026 UI refresh

The sidebar now contains only the four real working tools: **Weekly Tasks**, **AM Handover**, **ROX Domains**, and **Excel Splitter**. The empty Dashboard and Settings destinations were removed from navigation.

The visual system was refreshed for a darker premium internal-product feel: graphite navigation, warm Digitain-inspired accent, compact page headers, segmented workspace controls, cleaner cards, metrics, upload zones, tables, and confirmation actions.

For Partner Tier Sync, the recommended source is now the weekly **Confluence → Export to Word → upload `.docx`** flow. Direct Confluence remains under an Advanced section for future use from an internal network.
