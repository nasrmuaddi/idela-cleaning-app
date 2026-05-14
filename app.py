import io
from typing import Dict, List
import pandas as pd
import streamlit as st

st.set_page_config(page_title="IDELA Cleaning App", layout="wide")
st.title("IDELA Cleaning App")
st.caption("Upload raw IDELA Excel data, review missing values, choose actions, and download a cleaned workbook.")

BASELINE_START = "i1a_name_mark"
BASELINE_END = "i21_steps"
ENDLINE_START = "i1a_name_mark_post"
ENDLINE_END = "i21_steps_post"

META_COLUMNS = [
    "caseid", "IDELA_date", "idela_child_pwd", "If_yes_due_to_pwd",
    "sector", "program", "teacher_location", "d_childs_full_name",
    "e_childs_sex", "f_childs_age", "h_country", "child_status",
    "nationality", "district", "governorate", "sub_district"
]

QUESTION_LABELS = {
    "i1a_name_mark": "هل يمكنك أن تخبرني باسمك الأول واسم عائلتك؟ | Can you tell me your first and last/surname name?",
    "i1a_age_mark": "هل يمكنك أن تخبرني عن عمرك؟ | Can you tell me how old you are?",
    "i1a_sex_mark": "هل أنت صبي أم فتاة؟ | Are you a boy or a girl?",
    "i1a_caregiver_mark": "أخبرني باسم شخص واحد يعتني بك | Please tell me the name of one person who takes care of you",
    "i1a_neighborhood_mark": "اسم الحي/المجتمع/القرية التي تعيش فيها | Can you tell me the name of the neighborhood/community/village that you live in?",
    "i1a_state_mark": "اسم الولاية/الدولة التي تعيش فيها | Can you tell me the name of the state/country that you live in?",
    "i1a_country_mark": "هل من الممكن أن تخبرني عن اسم البلد أو المدينة التي تعيش به الآن؟ | Can you tell me the name of the state/country that you live in?",
    "country_from_mark": "من الممكن ان تخبرني عن اسم البلد الذي اتو منه اهلك؟ | Can you tell me the name of the state/country that you live in?",
    "i2a_biggest_circle_mark": "يحدد الدائرة الأكبر | Child identifies biggest circle",
    "i2b_smallest_circle_mark": "يحدد الدائرة الأصغر | Child identifies smallest circle",
    "i2c_longest_stick_mark": "يحدد العصا الأطول | Child identifies longest stick",
    "i2d_shortest_stick_mark": "يحدد العصا الأقصر | Child identifies shortest stick",
    "i3_sort_criterion1_mark": "صنف الطفل البطاقات حسب اللون أو الشكل/ طريقة واحدة فقط | Child sorts cards by first criterion",
    "i3_sort_criterion2_mark": "صنف الطفل البطاقات حسب اللون أو الشكل/ طريقة ثانية فقط | Child sorts cards by second criterion",
    "i4_circle_mark": "يتعرف على الدائرة | Child identifies circle",
    "i4_rectangle_mark": "يتعرف على المستطيل | Child identifies rectangle",
    "i4_triangle_mark": "يتعرف على المثلث | Child identifies triangle",
    "i4_square_mark": "يتعرف على المربع | Child identifies square",
    "i4_circle_env_mark": "حدد الطفل شيء يشبه الدائرة من محيطه | Child identifies circle in the environment",
    "i5_row12_correct_count": "الصفوف 1-2: عدد الأرقام الصحيحة (0-10) | Rows 1-2: Number of correct numbers (0-10)",
    "i5_row34_correct_count": "الصفوف 3-4: عدد الأرقام الصحيحة (0-10) | Rows 3-4: Number of correct numbers (0-10)",
    "i6_give3_mark": "يحدد 3 عناصر | Child identifies 3 items",
    "i6_give5_mark": "يحدد 5 عناصر | Child identifies 5 items",
    "i6_give8_mark": "يحدد 8 عناصر | Child identifies 8 items",
    "i6_focus_mark": "يظل مركزًا على المهمة؛ لا يتشتت بسهولة | Child stays concentrated on the task at hand; not easily distracted",
    "i6_eager_mark": "متحمس لإنجاز المهمة؛ لا يريد التوقف | Child is motivated to complete task; does not want to stop the task.",
    "i7_add3_2_mark": "يضيف 3 و 2 | Child adds 3 and 2",
    "i7_add2_2_mark": "يضيف 2 و 2 | Child adds 2 and 2",
    "i7_subtract1_from3_mark": "يطرح 1 من 3 | Child subtracts 1 from 3",
    "i8_friends_count": "عدد الأصدقاء المذكورين (0-10) | Number of friends named (0-10)",
    "i9_sad_trigger_mark": "يحدد شيئًا يجعله حزينًا | Child identifies something that makes them sad",
    "i9_regulate1_mark": "يعطي إجابة واحدة للتعامل مع الحزن | Child gives one response on dealing with sad feeling",
    "i9_regulate2_mark": "يعطي إجابة ثانية للتعامل مع الحزن | Child gives another response on dealing with sad feeling",
    "i9_happy_trigger_mark": "يحدد شيئًا يجعله سعيدًا | Child identifies something that makes them happy",
    "i10_understands_feeling_mark": "الطفل يدرك أن صديقه يشعر بالحزن/الألم/الضيق | Child identifies that friend is feeling sad/hurt/upset",
    "i10_help1_mark": "الطفل يعطي إجابة واحدة عن كيفية جعل صديقه يشعر بتحسن | Child gives one response for how to make friend feel better",
    "i10_help2_mark": "الطفل يعطي إجابة ثانية عن كيفية جعل صديقه يشعر بتحسن | Child gives second response for how to make friend feel better",
    "i11_conflict1_mark": "يعطي الطفل إجابة واحدة عن كيفية حل النزاع | Child gives one response for how to solve conflict",
    "i11_conflict2_mark": "يعطي الطفل إجابة ثانية عن كيفية حل النزاع | Child gives second response for how to solve conflict",
    "i12_seq1_mark": "سلسله الأرقام 1…6 | numbers sequence 1…6",
    "i12_seq2_mark": "5…2…9 سلسله الأرقام | numbers sequence 5…2…9",
    "i12_seq3_mark": "8…3…1…4 سلسله الأرقام | numbers sequence 8…3…1…4",
    "i12_seq4_mark": "1…2…4…7…3 سلسله الأرقام | numbers sequence 1…2…4…7…3",
    "i13_market_items_count": "عدد عناصر السوق المذكورة (0-10) | Number of market items named (0-10)",
    "i13_animals_count": "عدد الحيوانات المذكورة (0-10) | Number of animals named (0-10)",
    "i14_open_book_mark": "يفتح الطفل الكتاب بشكل صحيح | Child opens the book appropriately",
    "i14_point_text_mark": "يشير الطفل إلى النص الموجود على الصفحة | Child points to text on the page",
    "i14_text_direction_mark": "أشار الطفل الطريقة الصحيحة في القراءة | Child shows direction of text",
    "i15_row12_letters_count": "الصفوف 1-2: عدد الحروف الصحيحة | Rows 1-2: Number of correct letters",
    "i15_row34_letters_count": "الصفوف 3-4: عدد الحروف الصحيحة | Rows 3-4: Number of correct letters",
    "i16_s_pair_mark": "التعرف على زوج الأصوات /ب/ | Child identifies /s/ word pair",
    "i16_t_pair_mark": "التعرف على زوج الأصوات /س/ | Child identifies /t/ word pair",
    "i16_c_pair_mark": "التعرف على زوج الأصوات /ت/ | Child identifies /c/ word pair",
    "i17_writing_level": "مستوى الكتابة (0-4) | Writing level (0-4)",
    "i18_mouse_stole_hat_mark": "من سرق قبعة القطة؟ (الفأر) | Who stole the cat's hat? (the mouse)",
    "i18_hat_color_mark": "لون القبعة (أحمر) | Can you tell me the color of the hat? (red)",
    "i18_why_chased_mark": "لماذا طاردت القطة الفأر؟ | Why did the cat chase the mouse?",
    "i18_where_trapped_mark": "أين حوصر الفأر؟ | Where did the mouse get trapped?",
    "i18_why_spared_mark": "لماذا لم تأكل القطة الفأر؟ | Why did the cat spare/not eat the mouse?",
    "i18_focus_mark": "يظل مركزًا على المهمة؛ لا يتشتت بسهولة | Child stays concentrated on the task at hand; not easily distracted",
    "i18_eager_mark": "متحمس لإنجاز المهمة؛ لا يريد التوقف | Child is motivated to complete task; does not want to stop the task.",
    "i19_closed_corners": "عدد الزوايا المغلقة بدون فجوات (0-3) | Number of closed corners, no gaps (0, 1, 2, 3)",
    "i19_exited_mark": "الطفل متحمس لإتمام المهمة، لا يريد أن يتوقف عن العمل | The child is excited to complete the task and does not want to stop working.",
    "i20_head_mark": "يرسم رأسًا | Child draws a head",
    "i20_torso_mark": "يرسم جذعًا/جسمًا | Child draws a trunk/body",
    "i20_arms_mark": "يرسم الذراعين | Child draws arms",
    "i20_legs_mark": "يرسم الساقين | Child draws legs",
    "i20_face1_mark": "يرسم سمة واحدة من سمات الوجه | Child draws 1 facial feature",
    "i20_face2_mark": "يرسم سمتين من سمات الوجه | Child draws 2 facial features",
    "i20_hands_mark": "يرسم اليدين | Child draws hands",
    "i20_feet_mark": "يرسم القدمين | Child draws feet",
    "i20_focus_mark": "يبقى مركزًا على المهمة؛ لا يتشتت بسهولة | Child stays concentrated on the task at hand; not easily distracted",
    "i20_eager_mark": "متحمس لإنجاز المهمة؛ لا يريد التوقف | Child is motivated to complete task; does not want to stop the task.",
    "i21_steps": "عدد الخطوات التي قفزها (بحد أقصى 10) | Number of steps hopped (Maximum 10 steps.)",
}


def find_range_columns(df: pd.DataFrame, start_col: str, end_col: str) -> List[str]:
    cols = list(df.columns)
    if start_col not in cols or end_col not in cols:
        return []
    return cols[cols.index(start_col):cols.index(end_col) + 1]


def normalize_score_values(df: pd.DataFrame, question_cols: List[str]) -> pd.DataFrame:
    out = df.copy()
    for col in question_cols:
        out[col] = out[col].replace({"---": 999, "": pd.NA})
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
        target_cols = [c for c in [base_col, post_col] if c in out.columns]

        if action == "change missing to 0":
            for target in target_cols:
                out[target] = out[target].replace({999: 0}).fillna(0)

        elif action == "drop this question":
            out = out.drop(columns=target_cols, errors="ignore")
    return out


def create_by_question(clean_base: pd.DataFrame, actions: Dict[str, str]) -> pd.DataFrame:
    baseline_cols = find_range_columns(clean_base, BASELINE_START, BASELINE_END)
    out = clean_base[[c for c in META_COLUMNS if c in clean_base.columns]].copy()

    for base_col in baseline_cols:
        if actions.get(base_col, "No action") == "drop this question":
            continue

        post_col = f"{base_col}_post"
        if post_col not in clean_base.columns:
            continue

        out[base_col] = clean_base[base_col]
        out[post_col] = clean_base[post_col]

        comp_col = base_col.replace("_mark", "_mark_comparison")
        if comp_col == base_col:
            comp_col = f"{base_col}_comparison"

        out[comp_col] = (
            pd.to_numeric(clean_base[post_col], errors="coerce")
            - pd.to_numeric(clean_base[base_col], errors="coerce")
        )

    return out


def to_excel_bytes(sheets: Dict[str, pd.DataFrame]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for sheet_name, data in sheets.items():
            safe_name = sheet_name[:31]
            data.to_excel(writer, sheet_name=safe_name, index=False)

            workbook = writer.book
            worksheet = writer.sheets[safe_name]

            header_format = workbook.add_format({
                "bold": True,
                "bg_color": "#D9EAD3",
                "border": 1
            })

            for col_num, value in enumerate(data.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, min(max(len(str(value)) + 2, 12), 45))

            worksheet.autofilter(0, 0, max(len(data), 1), max(len(data.columns) - 1, 0))
            worksheet.freeze_panes(1, 0)
    return output.getvalue()


uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xlsm", "xls"])

if uploaded_file:
    xl = pd.ExcelFile(uploaded_file)
    sheet_name = st.selectbox("Select raw data sheet", xl.sheet_names)
    raw_df = pd.read_excel(uploaded_file, sheet_name=sheet_name)

    st.subheader("1) Raw Data Preview")
    st.dataframe(raw_df.head(20), use_container_width=True)

    if "IDELA_date" not in raw_df.columns:
        st.error("Column IDELA_date was not found.")
        st.stop()

    raw_df["IDELA_date_parsed"] = pd.to_datetime(raw_df["IDELA_date"], errors="coerce")
    filtered_df = raw_df[raw_df["IDELA_date_parsed"].notna()].drop(columns=["IDELA_date_parsed"]).copy()

    baseline_cols = find_range_columns(filtered_df, BASELINE_START, BASELINE_END)
    endline_cols = find_range_columns(filtered_df, ENDLINE_START, ENDLINE_END)
    all_question_cols = baseline_cols + endline_cols

    filtered_df = normalize_score_values(filtered_df, all_question_cols)

    filtered_df.insert(0, "Delete Action", "")
    filtered_df.insert(1, "baseline missing %", missing_pct(filtered_df, baseline_cols))
    filtered_df.insert(2, "endline missing %", missing_pct(filtered_df, endline_cols))

    st.subheader("2) Filtered on IDELA Date")
    st.write(f"Rows kept after IDELA_date validation: **{len(filtered_df)}**")

    high_missing = filtered_df[
        (filtered_df["baseline missing %"] > 0.30) |
        (filtered_df["endline missing %"] > 0.30)
    ].copy()

    st.warning(f"Rows with baseline or endline missing above 30%: {len(high_missing)}")

    delete_indices = []

    if len(high_missing) > 0:
        st.write("Select rows to delete. Unselected rows will be kept.")

        if "selected_delete_indices" not in st.session_state:
            st.session_state.selected_delete_indices = set()

        high_missing_display = high_missing.copy()
        high_missing_display["baseline missing %"] = high_missing_display["baseline missing %"] * 100
        high_missing_display["endline missing %"] = high_missing_display["endline missing %"] * 100

        display_cols = []
        important_cols = [
            "caseid",
            "d_childs_full_name",
            "child_name",
            "student_name",
            "e_childs_sex",
            "f_childs_age",
            "teacher_location",
        ]
        for col in important_cols:
            if col in high_missing_display.columns:
                display_cols.append(col)

        display_cols += ["baseline missing %", "endline missing %"]

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            page_size = st.selectbox("Rows per page", [50, 100, 200, 500], index=1)

        total_pages = max(1, (len(high_missing_display) - 1) // page_size + 1)

        with c2:
            page = st.number_input(
                "Page",
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1
            )

        start = (page - 1) * page_size
        end = start + page_size
        page_df = high_missing_display.iloc[start:end].copy()
        current_page_indices = set(page_df.index)

        with c3:
            if st.button("Select all on this page"):
                st.session_state.selected_delete_indices |= current_page_indices
                st.rerun()

        with c4:
            if st.button("Clear this page"):
                st.session_state.selected_delete_indices -= current_page_indices
                st.rerun()

        c5, c6 = st.columns(2)
        with c5:
            if st.button("Select ALL high-missing rows"):
                st.session_state.selected_delete_indices = set(high_missing_display.index)
                st.rerun()

        with c6:
            if st.button("Clear ALL selections"):
                st.session_state.selected_delete_indices = set()
                st.rerun()

        page_df["Select Delete"] = page_df.index.isin(st.session_state.selected_delete_indices)
        page_display_cols = ["Select Delete"] + display_cols

        edited_page = st.data_editor(
            page_df[page_display_cols],
            use_container_width=True,
            hide_index=False,
            key=f"delete_editor_page_{page}_{page_size}",
            column_config={
                "baseline missing %": st.column_config.NumberColumn(
                    "baseline missing %",
                    format="%.1f%%"
                ),
                "endline missing %": st.column_config.NumberColumn(
                    "endline missing %",
                    format="%.1f%%"
                )
            }
        )

        selected_on_page = set(
            edited_page.index[edited_page["Select Delete"] == True].tolist()
        )

        st.session_state.selected_delete_indices -= current_page_indices
        st.session_state.selected_delete_indices |= selected_on_page

        delete_indices = list(st.session_state.selected_delete_indices)

        st.info(
            f"Selected rows to delete: **{len(delete_indices)}** out of **{len(high_missing_display)}** high-missing rows. "
            f"Showing page **{page}** of **{total_pages}**."
        )

    clean_base = filtered_df.drop(index=delete_indices).copy()
    clean_base = clean_base.drop(columns=["Delete Action", "baseline missing %", "endline missing %"], errors="ignore")

    st.subheader("3) Question Missing Review and Actions")

    actions = {}
    action_options = ["No action", "change missing to 0", "drop this question"]

    if not baseline_cols:
        st.error("Baseline question columns were not found. Check column names.")
    else:
        question_review_rows = []
        for base_col in baseline_cols:
            post_col = f"{base_col}_post"
            question_name = QUESTION_LABELS.get(base_col, base_col)

            question_review_rows.append({
                "Baseline Code": base_col,
                "Baseline Question Name": question_name,
                "Baseline Missing %": question_missing_pct(clean_base, base_col),
                "Endline Code": post_col if post_col in clean_base.columns else "",
                "Endline Question Name": question_name if post_col in clean_base.columns else "",
                "Endline Missing %": question_missing_pct(clean_base, post_col) if post_col in clean_base.columns else 0.0,
                "Action": "No action"
            })

        question_review_df = pd.DataFrame(question_review_rows)

        edited_actions = st.data_editor(
            question_review_df,
            column_config={
                "Baseline Code": st.column_config.TextColumn("Baseline Code", disabled=True),
                "Baseline Question Name": st.column_config.TextColumn("Baseline Question Name", disabled=True),
                "Baseline Missing %": st.column_config.ProgressColumn(
                    "Baseline Missing %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=1
                ),
                "Endline Code": st.column_config.TextColumn("Endline Code", disabled=True),
                "Endline Question Name": st.column_config.TextColumn("Endline Question Name", disabled=True),
                "Endline Missing %": st.column_config.ProgressColumn(
                    "Endline Missing %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=1
                ),
                "Action": st.column_config.SelectboxColumn(
                    "Action",
                    options=action_options,
                    required=True
                )
            },
            disabled=[
                "Baseline Code",
                "Baseline Question Name",
                "Baseline Missing %",
                "Endline Code",
                "Endline Question Name",
                "Endline Missing %",
            ],
            hide_index=True,
            use_container_width=True,
            key="question_action_editor"
        )

        actions = dict(zip(edited_actions["Baseline Code"], edited_actions["Action"]))

        st.info("If you choose 'drop this question', both the baseline question and its matching post/endline question are removed.")

    clean_df = apply_actions(clean_base, actions)
    by_question_df = create_by_question(clean_base, actions)

    st.subheader("4) Clean Data Preview")
    st.dataframe(clean_df.head(20), use_container_width=True)

    sheets = {
        "filtered on Idela": filtered_df,
        "idela clean data set": clean_df,
        "BY QUESTION": by_question_df,
        "BY ITEM": pd.DataFrame(),
        "BY DOMAIN": pd.DataFrame(),
        "IDELA ANALYSIS": pd.DataFrame()
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
