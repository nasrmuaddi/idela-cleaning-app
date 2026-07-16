# IDELA Cleaning App

Streamlit app for cleaning IDELA baseline/endline (pre/post) data and exporting Excel analysis outputs.

## Workflow (9 steps)

1. **Upload structure** — three supported layouts: one file with pre/post in the same row, two files (baseline + endline), or one file with duplicated pre/post rows.
2. **Map columns** — auto-suggested mapping of the case ID, round/status, essential-info, and question columns into the standard IDELA fields.
3. **Pair pre/post & drop unpaired** — keeps a child only if they have data on BOTH the pre and post side; shows how many are dropped and why. Pairing counts live here (they were removed from Step 2 to avoid duplication).
4. **Map questions into items** — 21 item boxes; drag questions into them. Defaults follow the standard IDELA structure.
5. **Map items into domains** — 4 domain boxes; drag items into them. Defaults follow the standard IDELA domains.
6. **Review rows** — per-child baseline/endline missing %, with row skipping. Text answers are not yet scored here, so a value like `no_response` is not yet counted as missing (blank/`---` are).
7. **Score text values** — assign numeric scores to any text answers; values are then finalized to numeric.
8. **Question missing actions** — per-question "change missing to 0" or "drop this question". Edits are made in a form and saved together when you press **Apply actions**, so there is no per-row delay.
9. **Preview & download** — BY QUESTION / BY ITEM / BY DOMAIN / IDELA outputs plus filterable dashboard sheets. Item and domain scores use your Step 4/5 mappings.

Steps 4 and 5 use the `streamlit-sortables` drag-and-drop component (in `requirements.txt`). If it is unavailable each step falls back to a dropdown editor automatically.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

Push the repo (including `requirements.txt`) to GitHub, point the app at `app.py`, and deploy/reboot so the requirements install.
