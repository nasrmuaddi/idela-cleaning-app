import io
from typing import Dict, List
import pandas as pd
import streamlit as st

st.set_page_config(page_title="IDELA Cleaning App", layout="wide")

st.title("IDELA Cleaning App")
st.caption(
    "Upload raw IDELA Excel data, review missing values, choose actions, and download a cleaned workbook."
)

BASELINE_START = "i1a_name_mark"
BASELINE_END = "i21_steps"

ENDLINE_START = "i1a_name_mark_post"
ENDLINE_END = "i21_steps_post"

META_COLUMNS = [
    "caseid",
    "IDELA_date",
    "idela_child_pwd",
    "If_yes_due_to_pwd",
    "sector",
    "program",
    "teacher_location",
    "d_childs_full_name",
    "e_childs_sex",
    "f_childs_age",
    "h_country",
    "child_status",
    "nationality",
    "district",
    "governorate",
    "sub_district"
]


def find_range_columns(df: pd.DataFrame, start_col: str, end_col: str) -> List[str]:

    cols = list(df.columns)

    if start_col not in cols or end_col not in cols:
        return []

    return cols[cols.index(start_col): cols.index(end_col) + 1]


def normalize_score_values(df: pd.DataFrame, question_cols: List[str]) -> pd.DataFrame:

    out = df.copy()

    for col in question_cols:

        out[col] = out[col].replace({
            "---": 999,
            "": pd.NA
        })

        out[col] = pd.to_numeric(out[col], errors="coerce")

    return out


def missing_pct(df: pd.DataFrame, cols: List[str]) -> pd.Series:

    if not cols:
        return pd.Series([0.0] * len(df), index=df.index)

    return df[cols].isin([999]).sum(axis=1) / len(cols)


def question_missing_pct(df: pd.DataFrame, col: str) -> float:

    if col not in df.columns or len(df) == 0:
        return 0.0

    return float(df[col].isin([999]).sum() / len(df))


def apply_actions(df: pd.DataFrame, actions: Dict[str, str]) -> pd.DataFrame:

    out = df.copy()

    for base_col, action in actions.items():

        post_col = f"{base_col}_post"

        target_cols = [
            c for c in [base_col, post_col]
            if c in out.columns
        ]

        if action == "change missing to 0":

            for target in target_cols:

                out[target] = (
                    out[target]
                    .replace({999: 0})
                    .fillna(0)
                )

        elif action == "drop this question":

            out = out.drop(
                columns=target_cols,
                errors="ignore"
            )

    return out


def create_by_question(clean_base: pd.DataFrame,
                       actions: Dict[str, str]) -> pd.DataFrame:

    baseline_cols = find_range_columns(
        clean_base,
        BASELINE_START,
        BASELINE_END
    )

    out = clean_base[
        [c for c in META_COLUMNS if c in clean_base.columns]
    ].copy()

    for base_col in baseline_cols:

        if actions.get(base_col, "No action") == "drop this question":
            continue

        post_col = f"{base_col}_post"

        if post_col not in clean_base.columns:
            continue

        out[base_col] = clean_base[base_col]
        out[post_col] = clean_base[post_col]

        comp_col = base_col.replace(
            "_mark",
            "_mark_comparison"
        )

        if comp_col == base_col:
            comp_col = f"{base_col}_comparison"

        out[comp_col] = (
            pd.to_numeric(clean_base[post_col], errors="coerce")
            -
            pd.to_numeric(clean_base[base_col], errors="coerce")
        )

    return out


def to_excel_bytes(sheets: Dict[str, pd.DataFrame]) -> bytes:

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

        for sheet_name, data in sheets.items():

            safe_name = sheet_name[:31]

            data.to_excel(
                writer,
                sheet_name=safe_name,
                index=False
            )

            workbook = writer.book
            worksheet = writer.sheets[safe_name]

            header_format = workbook.add_format({
                "bold": True,
                "bg_color": "#D9EAD3",
                "border": 1
            })

            for col_num, value in enumerate(data.columns.values):

                worksheet.write(
                    0,
                    col_num,
                    value,
                    header_format
                )

                worksheet.set_column(
                    col_num,
                    col_num,
                    min(max(len(str(value)) + 2, 12), 45)
                )

            worksheet.autofilter(
                0,
                0,
                max(len(data), 1),
                max(len(data.columns) - 1, 0)
            )

            worksheet.freeze_panes(1, 0)

    return output.getvalue()


uploaded_file = st.file_uploader(
    "Upload Excel file",
    type=["xlsx", "xlsm", "xls"]
)

if uploaded_file:

    xl = pd.ExcelFile(uploaded_file)

    sheet_name = st.selectbox(
        "Select raw data sheet",
        xl.sheet_names
    )

    raw_df = pd.read_excel(
        uploaded_file,
        sheet_name=sheet_name
    )

    st.subheader("1) Raw Data Preview")

    st.dataframe(
        raw_df.head(20),
        use_container_width=True
    )

    if "IDELA_date" not in raw_df.columns:

        st.error("Column IDELA_date was not found.")
        st.stop()

    raw_df["IDELA_date_parsed"] = pd.to_datetime(
        raw_df["IDELA_date"],
        errors="coerce"
    )

    filtered_df = raw_df[
        raw_df["IDELA_date_parsed"].notna()
    ].drop(
        columns=["IDELA_date_parsed"]
    ).copy()

    baseline_cols = find_range_columns(
        filtered_df,
        BASELINE_START,
        BASELINE_END
    )

    endline_cols = find_range_columns(
        filtered_df,
        ENDLINE_START,
        ENDLINE_END
    )

    all_question_cols = baseline_cols + endline_cols

    filtered_df = normalize_score_values(
        filtered_df,
        all_question_cols
    )

    filtered_df.insert(0, "Delete Action", "")

    filtered_df.insert(
        1,
        "baseline missing %",
        missing_pct(filtered_df, baseline_cols)
    )

    filtered_df.insert(
        2,
        "endline missing %",
        missing_pct(filtered_df, endline_cols)
    )

    st.subheader("2) Filtered on IDELA Date")

    st.write(
        f"Rows kept after IDELA_date validation: **{len(filtered_df)}**"
    )

    high_missing = filtered_df[
        (filtered_df["baseline missing %"] > 0.30)
        |
        (filtered_df["endline missing %"] > 0.30)
    ].copy()

    st.warning(
        f"Rows with baseline or endline missing above 30%: {len(high_missing)}"
    )

    delete_indices = []

    if len(high_missing) > 0:

        st.write(
            "Select rows to delete. Unselected rows will be kept."
        )

        high_missing_display = high_missing.copy()

        high_missing_display["Select Delete"] = False

        high_missing_display["baseline missing %"] = (
            high_missing_display["baseline missing %"] * 100
        )

        high_missing_display["endline missing %"] = (
            high_missing_display["endline missing %"] * 100
        )

        display_cols = ["Select Delete"]

        if "caseid" in high_missing_display.columns:
            display_cols.append("caseid")

        display_cols += [
            "baseline missing %",
            "endline missing %"
        ]

        edited = st.data_editor(
            high_missing_display[display_cols],

            use_container_width=True,

            hide_index=False,

            column_config={

                "baseline missing %":
                st.column_config.NumberColumn(
                    "baseline missing %",
                    format="%.1f%%"
                ),

                "endline missing %":
                st.column_config.NumberColumn(
                    "endline missing %",
                    format="%.1f%%"
                )
            }
        )

        delete_indices = edited.index[
            edited["Select Delete"] == True
        ].tolist()

    clean_base = filtered_df.drop(
        index=delete_indices
    ).copy()

    clean_base = clean_base.drop(
        columns=[
            "Delete Action",
            "baseline missing %",
            "endline missing %"
        ],
        errors="ignore"
    )

    st.subheader(
        "3) Question Missing Review and Actions"
    )

    actions = {}

    action_options = [
        "No action",
        "change missing to 0",
        "drop this question"
    ]

    if not baseline_cols:

        st.error(
            "Baseline question columns were not found."
        )

    else:

        question_review_rows = []

        for base_col in baseline_cols:

            post_col = f"{base_col}_post"

            question_review_rows.append({

                "Baseline Question": base_col,

                "Baseline Missing %":
                question_missing_pct(
                    clean_base,
                    base_col
                ) * 100,

                "Endline Question":
                post_col if post_col in clean_base.columns else "",

                "Endline Missing %":
                (
                    question_missing_pct(
                        clean_base,
                        post_col
                    ) * 100
                    if post_col in clean_base.columns
                    else 0.0
                ),

                "Action": "No action"
            })

        question_review_df = pd.DataFrame(
            question_review_rows
        )

        edited_actions = st.data_editor(

            question_review_df,

            hide_index=True,

            use_container_width=True,

            column_config={

                "Baseline Missing %":
                st.column_config.ProgressColumn(
                    "Baseline Missing %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                ),

                "Endline Missing %":
                st.column_config.ProgressColumn(
                    "Endline Missing %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                ),

                "Action":
                st.column_config.SelectboxColumn(
                    "Action",
                    options=action_options,
                    required=True
                )
            }
        )

        actions = dict(zip(
            edited_actions["Baseline Question"],
            edited_actions["Action"]
        ))

        st.info(
            "If you choose 'drop this question', "
            "both the baseline question and its matching "
            "post/endline question are removed."
        )

    clean_df = apply_actions(
        clean_base,
        actions
    )

    by_question_df = create_by_question(
        clean_base,
        actions
    )

    st.subheader("4) Clean Data Preview")

    st.dataframe(
        clean_df.head(20),
        use_container_width=True
    )

    sheets = {

        "filtered on Idela":
        filtered_df,

        "idela clean data set":
        clean_df,

        "BY QUESTION":
        by_question_df,

        "BY ITEM":
        pd.DataFrame(),

        "BY DOMAIN":
        pd.DataFrame(),

        "IDELA ANALYSIS":
        pd.DataFrame()
    }

    excel_bytes = to_excel_bytes(sheets)

    st.download_button(

        label="Download cleaned IDELA workbook",

        data=excel_bytes,

        file_name="idela_cleaned_output.xlsx",

        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:

    st.info("Upload your Excel file to start.")