# IDELA Cleaning & Analysis App

Streamlit app for cleaning IDELA baseline/endline (pre/post) data and exporting an Excel analysis workbook.

## Workflow (10 steps)

1. **Upload structure** — one file (pre/post same row), two files, or one file with duplicated pre/post rows. No IDELA-date field is required anymore.
2. **Map columns** — auto-suggested mapping of case ID, round/status, essential info, and question columns.
3. **Pair pre/post & drop unpaired** — keeps a child only if they have data on BOTH sides. Pairing is on case ID + presence of question data (no date filter).
4. **Score text values** — assign numeric scores to any text answers; finalized to numeric.
5. **Map questions into items** — 21 colored drag boxes (4 restful colors).
6. **Max scores for count questions** — detects count/level questions (not 0/1) and asks for each maximum. Defaults: i5_row12/i5_row34 = 10 each (item 5 combined 20), i8 = 10, i13_market/i13_animals = 10 each, i15_row12/i15_row34 = 10 each (item 15 combined 20), i17 = 4, i19 = 4, i21 = 10.
7. **Map items into domains** — 4 colored drag boxes.
8. **Review rows** — per-child missing %, skip high-missing children.
9. **Question actions** — per-question change-missing-to-0 or drop (form-based, no lag).
10. **Preview & download** — the analysis workbook.

## Output workbook (8 sheets)

Cohort summaries:
1. **raw data** — the uploaded file(s).
2. **Cleaned data** — essential fields + question values (pre/post) + a per-child IDELA % (achieved / max).
3. **Question Analysis** — one row per question (bilingual name): Pre score, Post score, Pre %, Post %, Post − Pre %. 0/1 questions use % of 1s (max = 1); count questions use score / max. Rows alternate two restful colors.
4. **Item Analysis** — per item: score = mean of the sum of its question values; max = (#0/1 questions) + (sum of count maxima); % = score / max.
5. **Domain Analysis** — per domain: average of the pre/post % of its questions; plus an IDELA row = average of the four domain %s.

Row-level (one row per child, with AVERAGE / MALE AVERAGE / FEMALE AVERAGE / MINIMUM / MAXIMUM summary rows on top):
6. **Questions (per child)** — each question's raw pre & post value.
7. **Items (per child)** — each item's pre % and post % (child sum ÷ item max).
8. **Domains (per child)** — each domain's pre % and post % (average of that child's question %s) plus IDELA pre / post / change %.

## Calculation assumptions (tell me to change any)

- "Score" is the average per child; missing is resolved to 0 or the question dropped in step 9 before calculating.
- Domain % = average of its **questions'** %s (your literal wording). If you meant average of item %s instead, it's a one-line change.
- Item 19 default max = 4 as you specified, though its label reads 0–3 (editable in step 6).
- The charts sheet is not built yet (to be defined later).

## Run / deploy

Local: `pip install -r requirements.txt` then `streamlit run app.py`.
Cloud: push the repo including `requirements.txt` (has `streamlit-sortables`) and reboot.
