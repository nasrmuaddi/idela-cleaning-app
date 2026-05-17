# IDELA Cleaning App

Streamlit app for cleaning IDELA baseline/endline data and exporting Excel analysis outputs.

## Features

- Supports three upload structures:
  1. One file: baseline and endline in the same row
  2. Two files: one baseline file and one endline file
  3. One file: baseline and endline duplicated rows
- Column mapping for ID, round/status, essential info columns, and question columns
- Text-value scoring step before numeric analysis
- Row review and question missing actions
- BY QUESTION, BY ITEM, BY DOMAIN, and IDELA score outputs
- Dashboard sheets for Question, Item, Domain, and IDELA score analysis
- Dashboard sheets now use filterable Excel tables and charts instead of unstable dynamic formulas

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Upload this project to GitHub.
2. In Streamlit Cloud, select the repository.
3. Set the main file path to `app.py`.
4. Deploy.

