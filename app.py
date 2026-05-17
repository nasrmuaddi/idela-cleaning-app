import io
import re
import difflib
from typing import Dict, List

import pandas as pd
import streamlit as st

st.set_page_config(page_title="IDELA Cleaning App", layout="wide")
st.title("IDELA Cleaning App")
st.caption("Upload, map columns, review missing values, choose actions, and download a cleaned workbook.")

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

BASELINE_QUESTION_COLS = list(QUESTION_LABELS.keys())
ENDLINE_QUESTION_COLS = [f"{c}_post" for c in BASELINE_QUESTION_COLS]


def question_mapping_label(question_col: str) -> str:
    """Show question IDs with English and Arabic descriptions during mapping."""
    base_col = question_col.replace("_post", "")
    label = QUESTION_LABELS.get(base_col, base_col)
    if " | " in label:
        arabic, english = label.split(" | ", 1)
        return f"{question_col} — {english.strip()} | {arabic.strip()}"
    return f"{question_col} — {label}"



def init_state():
    defaults = {
        "step": 1,
        "upload_type": None,
        "column_mapping": {},
        "mapped_df": None,
        "filtered_df": None,
        "clean_base": None,
        "scored_df": None,
        "value_recode_mapping": {},
        "actions": {},
        "selected_delete_indices": set(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_after_upload_type_change():
    st.session_state.column_mapping = {}
    st.session_state.mapped_df = None
    st.session_state.filtered_df = None
    st.session_state.clean_base = None
    st.session_state.scored_df = None
    st.session_state.value_recode_mapping = {}
    st.session_state.actions = {}
    st.session_state.selected_delete_indices = set()


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "", str(name).strip().lower())


def suggest_column(required_col: str, uploaded_cols: List[str], endline_hint: bool = False) -> str:
    """Suggest a source column. This avoids bad defaults like mapping caseid to row number."""
    if required_col in uploaded_cols:
        return required_col

    req_norm = normalize_name(required_col)
    norm_lookup = {normalize_name(c): c for c in uploaded_cols}

    # Strong ID preferences first
    if required_col in ["caseid", "dup_id", "base_id", "end_id"] or "caseid" in req_norm:
        preferred_tokens = ["caseid", "case_id", "case.case_id", "form.case.@case_id", "beneficiaryid", "beneficiary_id", "childid", "child_id"]
        for col in uploaded_cols:
            col_norm = normalize_name(col)
            if any(normalize_name(tok) in col_norm for tok in preferred_tokens):
                return col
        # Do NOT auto-select generic columns like number/formid/enumerator as an ID
        return ""

    # Round/status column preferences
    if required_col in ["round", "round_col"] or "round" in req_norm:
        for col in uploaded_cols:
            col_norm = normalize_name(col)
            if any(tok in col_norm for tok in ["surveytype", "assessmenttype", "round", "status", "baselineendline"]):
                return col
        return ""

    if req_norm in norm_lookup:
        return norm_lookup[req_norm]

    base_req = required_col.replace("_post", "")
    base_norm = normalize_name(base_req)

    candidates = uploaded_cols
    if endline_hint:
        hinted = [c for c in uploaded_cols if any(x in normalize_name(c) for x in ["post", "endline", "end", "followup", "el"])]
        if hinted:
            candidates = hinted

    # Match question label text when uploaded headers are long English/Arabic questions.
    label = QUESTION_LABELS.get(base_req, "")
    label_parts = []
    if label:
        label_parts = [part.strip() for part in label.split(" | ") if part.strip()]

    clean_lookup = {}
    candidate_norms = []
    for c in candidates:
        n = normalize_name(c)
        n_clean = n.replace("post", "").replace("endline", "").replace("followup", "").replace("baseline", "").replace("base", "")
        candidate_norms.append(n_clean)
        clean_lookup[n_clean] = c

    if base_norm in clean_lookup:
        return clean_lookup[base_norm]

    search_norms = [base_norm] + [normalize_name(x) for x in label_parts]
    best_match = ""
    best_ratio = 0
    for search_norm in search_norms:
        if not search_norm:
            continue
        for cand_norm in candidate_norms:
            ratio = difflib.SequenceMatcher(None, search_norm, cand_norm).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = cand_norm

    if best_ratio >= 0.55 and best_match in clean_lookup:
        return clean_lookup[best_match]

    matches = difflib.get_close_matches(base_norm, candidate_norms, n=1, cutoff=0.76)
    return clean_lookup.get(matches[0], "") if matches else ""


def read_excel_file(uploaded_file, sheet_name):
    return pd.read_excel(uploaded_file, sheet_name=sheet_name)


def is_missing_question_value(series: pd.Series) -> pd.Series:
    as_text = series.astype("string").str.strip()
    numeric = pd.to_numeric(series, errors="coerce")
    return series.isna() | as_text.isin(["---", "", "999"]) | numeric.eq(999)


def normalize_score_values(df: pd.DataFrame, question_cols: List[str]) -> pd.DataFrame:
    out = df.copy()
    for col in question_cols:
        if col in out.columns:
            out[col] = out[col].replace({"---": 999, "": pd.NA})
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def detect_unscored_values(df: pd.DataFrame, question_cols: List[str]) -> pd.DataFrame:
    """Find text values in question columns that cannot be converted to numbers."""
    rows = []
    for col in question_cols:
        if col not in df.columns:
            continue
        s = df[col]
        as_text = s.astype("string").str.strip()
        numeric = pd.to_numeric(s, errors="coerce")
        mask = (
            s.notna()
            & ~as_text.isin(["", "---", "999"])
            & ~numeric.notna()
        )
        if mask.any():
            for value, count in as_text[mask].value_counts(dropna=True).items():
                rows.append({
                    "Column": col,
                    "Uploaded value": str(value),
                    "Rows": int(count),
                })
    return pd.DataFrame(rows)


def default_score_suggestion(value: str):
    v = str(value).strip().lower()
    positive = {"correct", "yes", "true", "y", "صحيح", "نعم"}
    negative = {"incorrect", "wrong", "no", "false", "n", "خطأ", "غير صحيح", "لا"}
    missing = {"no response", "no_response", "noresponse", "missing", "na", "n/a", "null", "blank", "لا استجابة", "بدون استجابة"}
    if v in positive:
        return 1
    if v in negative:
        return 0
    if v in missing:
        return 999
    return None


def apply_value_recode(df: pd.DataFrame, question_cols: List[str], recode_mapping: Dict[str, object]) -> pd.DataFrame:
    """Replace non-numeric text answers in question fields with user-selected scores."""
    out = df.copy()
    clean_mapping = {}
    for value, score in recode_mapping.items():
        try:
            clean_mapping[str(value).strip().lower()] = float(score)
        except Exception:
            continue

    for col in question_cols:
        if col not in out.columns:
            continue
        def recode_cell(x):
            if pd.isna(x):
                return x
            key = str(x).strip().lower()
            return clean_mapping.get(key, x)
        out[col] = out[col].map(recode_cell)
    return out


def missing_pct(df: pd.DataFrame, cols: List[str]) -> pd.Series:
    existing = [c for c in cols if c in df.columns]
    if not existing:
        return pd.Series([0.0] * len(df), index=df.index)
    missing_flags = pd.concat([is_missing_question_value(df[col]) for col in existing], axis=1)
    return missing_flags.sum(axis=1) / len(existing)


def question_missing_pct(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns or len(df) == 0:
        return 0.0
    return float(is_missing_question_value(df[col]).sum() / len(df))


def get_remaining_missing_summary(df: pd.DataFrame, question_cols: List[str]) -> pd.DataFrame:
    rows = []
    for col in question_cols:
        if col not in df.columns:
            continue
        missing_count = int(is_missing_question_value(df[col]).sum())
        if missing_count > 0:
            rows.append({"Question ID": col, "Missing count": missing_count, "Missing %": missing_count / len(df) if len(df) else 0})
    return pd.DataFrame(rows)


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


def create_by_question(clean_df: pd.DataFrame, baseline_cols: List[str]) -> pd.DataFrame:
    out = clean_df[[c for c in META_COLUMNS if c in clean_df.columns]].copy()
    used_baseline_score_cols = []
    used_endline_score_cols = []

    for base_col in baseline_cols:
        post_col = f"{base_col}_post"
        if base_col not in clean_df.columns or post_col not in clean_df.columns:
            continue
        base_numeric = pd.to_numeric(clean_df[base_col], errors="coerce")
        post_numeric = pd.to_numeric(clean_df[post_col], errors="coerce")
        out[base_col] = base_numeric
        out[post_col] = post_numeric
        comp_col = base_col.replace("_mark", "_mark_comparison")
        if comp_col == base_col:
            comp_col = f"{base_col}_comparison"
        out[comp_col] = post_numeric - base_numeric
        used_baseline_score_cols.append(base_col)
        used_endline_score_cols.append(post_col)

    out["baseline idela score"] = clean_df[used_baseline_score_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1) if used_baseline_score_cols else 0
    out["endline idela score"] = clean_df[used_endline_score_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1) if used_endline_score_cols else 0
    out["idela score"] = out["endline idela score"] - out["baseline idela score"]
    return out


def to_excel_bytes(sheets: Dict[str, pd.DataFrame]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for sheet_name, data in sheets.items():
            safe_name = sheet_name[:31]
            data.to_excel(writer, sheet_name=safe_name, index=False)
            workbook = writer.book
            worksheet = writer.sheets[safe_name]
            header_format = workbook.add_format({"bold": True, "bg_color": "#D9EAD3", "border": 1})
            percent_format = workbook.add_format({"num_format": "0.0%"})
            for col_num, value in enumerate(data.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, min(max(len(str(value)) + 2, 12), 45))
                if "%" in str(value).lower():
                    worksheet.set_column(col_num, col_num, 18, percent_format)
            worksheet.autofilter(0, 0, max(len(data), 1), max(len(data.columns) - 1, 0))
            worksheet.freeze_panes(1, 0)
    return output.getvalue()


def go_next():
    st.session_state.step += 1
    st.rerun()


def go_back():
    st.session_state.step -= 1
    st.rerun()


def show_progress():
    labels = ["1. Upload Structure", "2. Map Columns", "3. Score Text Values", "4. Review Rows", "5. Question Actions", "6. Download"]
    current = st.session_state.step
    st.progress((current - 1) / (len(labels) - 1))
    st.write(" → ".join([f"**{x}**" if i + 1 == current else x for i, x in enumerate(labels)]))


def selectbox_mapping(label: str, req_col: str, uploaded_cols: List[str], key: str, mapping: Dict[str, str], endline_hint: bool = False):
    options = [""] + uploaded_cols
    suggested = mapping.get(key, suggest_column(req_col, uploaded_cols, endline_hint=endline_hint))
    index = options.index(suggested) if suggested in options else 0
    mapping[key] = st.selectbox(label, options=options, index=index, key=f"map_{key}")


def standard_output_columns() -> List[str]:
    return META_COLUMNS + BASELINE_QUESTION_COLS + ENDLINE_QUESTION_COLS


def keep_standard_columns(df: pd.DataFrame) -> pd.DataFrame:
    keep_cols = [c for c in standard_output_columns() if c in df.columns]
    return df[keep_cols].copy()


def build_same_row_df(raw_df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    # Rename mapped uploaded columns into the standard format, then discard all other columns.
    rename = {uploaded: standard for standard, uploaded in mapping.items() if uploaded}
    out = raw_df.rename(columns=rename).copy()
    out = out.loc[:, ~out.columns.duplicated()].copy()
    return keep_standard_columns(out)


def build_two_file_df(base_df: pd.DataFrame, end_df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    base_id_src = mapping["base_id"]
    end_id_src = mapping["end_id"]

    base_cols = {mapping[k]: k.replace("base_", "") for k in mapping if k.startswith("base_") and k not in ["base_id"] and mapping[k]}
    end_cols = {mapping[k]: k.replace("end_", "") + "_post" for k in mapping if k.startswith("end_") and k not in ["end_id"] and mapping[k]}

    base_keep = [base_id_src] + list(base_cols.keys())
    end_keep = [end_id_src] + list(end_cols.keys())

    base_part = base_df[base_keep].copy().rename(columns={base_id_src: "caseid", **base_cols})
    end_part = end_df[end_keep].copy().rename(columns={end_id_src: "caseid", **end_cols})

    base_part = base_part.drop_duplicates(subset=["caseid"], keep="first")
    end_part = end_part.drop_duplicates(subset=["caseid"], keep="first")

    merged = base_part.merge(end_part, on="caseid", how="inner")
    return keep_standard_columns(merged)


def build_duplicated_rows_df(raw_df: pd.DataFrame, mapping: Dict[str, str], baseline_value, endline_value) -> pd.DataFrame:
    id_src = mapping["dup_id"]
    round_src = mapping["round_col"]
    data = raw_df.copy()
    data["__round_text__"] = data[round_src].astype("string").str.strip().str.lower()
    base_val = str(baseline_value).strip().lower()
    end_val = str(endline_value).strip().lower()

    baseline_raw = data[data["__round_text__"] == base_val].copy()
    endline_raw = data[data["__round_text__"] == end_val].copy()

    question_cols = {mapping[k]: k.replace("q_", "") for k in mapping if k.startswith("q_") and mapping[k]}
    optional_cols = {mapping[k]: k.replace("meta_", "") for k in mapping if k.startswith("meta_") and mapping[k]}

    base_keep = [id_src] + list(optional_cols.keys()) + list(question_cols.keys())
    end_keep = [id_src] + list(question_cols.keys())

    baseline_part = baseline_raw[base_keep].copy().rename(columns={id_src: "caseid", **optional_cols, **question_cols})
    endline_part = endline_raw[end_keep].copy().rename(columns={id_src: "caseid", **{src: f"{std}_post" for src, std in question_cols.items()}})

    baseline_part = baseline_part.drop_duplicates(subset=["caseid"], keep="first")
    endline_part = endline_part.drop_duplicates(subset=["caseid"], keep="first")
    merged = baseline_part.merge(endline_part, on="caseid", how="inner")
    return keep_standard_columns(merged)


init_state()
show_progress()
st.divider()

# STEP 1: Upload structure and files
if st.session_state.step == 1:
    st.subheader("Step 1: Select upload structure")
    upload_type = st.radio(
        "How is your IDELA data uploaded?",
        [
            "One file: baseline and endline are in the same row",
            "Two files: one baseline file and one endline file",
            "One file: baseline and endline are duplicated rows",
        ],
        index=0,
        key="upload_type_radio",
    )
    if upload_type != st.session_state.upload_type:
        st.session_state.upload_type = upload_type
        reset_after_upload_type_change()

    if upload_type.startswith("One file: baseline and endline are in the same row"):
        uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xlsm", "xls"], key="same_file")
        if uploaded_file:
            xl = pd.ExcelFile(uploaded_file)
            sheet_name = st.selectbox("Select raw data sheet", xl.sheet_names, key="same_sheet")
            raw_df = read_excel_file(uploaded_file, sheet_name)
            st.session_state.raw_df = raw_df
            st.success(f"Loaded {len(raw_df)} rows and {len(raw_df.columns)} columns.")
            st.dataframe(raw_df.head(10), use_container_width=True)
            if st.button("Next: Map columns", type="primary"):
                go_next()

    elif upload_type.startswith("Two files"):
        col1, col2 = st.columns(2)
        with col1:
            base_file = st.file_uploader("Upload baseline Excel file", type=["xlsx", "xlsm", "xls"], key="base_file")
        with col2:
            end_file = st.file_uploader("Upload endline Excel file", type=["xlsx", "xlsm", "xls"], key="end_file")
        if base_file and end_file:
            base_xl = pd.ExcelFile(base_file)
            end_xl = pd.ExcelFile(end_file)
            c1, c2 = st.columns(2)
            with c1:
                base_sheet = st.selectbox("Baseline sheet", base_xl.sheet_names, key="base_sheet")
                base_df = read_excel_file(base_file, base_sheet)
                st.write("Baseline preview")
                st.dataframe(base_df.head(5), use_container_width=True)
            with c2:
                end_sheet = st.selectbox("Endline sheet", end_xl.sheet_names, key="end_sheet")
                end_df = read_excel_file(end_file, end_sheet)
                st.write("Endline preview")
                st.dataframe(end_df.head(5), use_container_width=True)
            st.session_state.base_df = base_df
            st.session_state.end_df = end_df
            if st.button("Next: Map columns", type="primary"):
                go_next()

    else:
        uploaded_file = st.file_uploader("Upload Excel file with baseline/endline duplicated rows", type=["xlsx", "xlsm", "xls"], key="dup_file")
        if uploaded_file:
            xl = pd.ExcelFile(uploaded_file)
            sheet_name = st.selectbox("Select raw data sheet", xl.sheet_names, key="dup_sheet")
            raw_df = read_excel_file(uploaded_file, sheet_name)
            st.session_state.raw_df = raw_df
            st.success(f"Loaded {len(raw_df)} rows and {len(raw_df.columns)} columns.")
            st.dataframe(raw_df.head(10), use_container_width=True)
            if st.button("Next: Map columns", type="primary"):
                go_next()

# STEP 2: Mapping
elif st.session_state.step == 2:
    st.subheader("Step 2: Map columns")
    upload_type = st.session_state.upload_type
    mapping = dict(st.session_state.column_mapping) if st.session_state.column_mapping else {}

    if upload_type.startswith("One file: baseline and endline are in the same row"):
        raw_df = st.session_state.raw_df
        uploaded_cols = list(raw_df.columns)
        st.write("Map the uploaded columns into the standard IDELA format.")
        tab_meta, tab_q, tab_preview = st.tabs(["Essential info columns", "Required question columns", "Preview"])
        with tab_meta:
            st.warning("Map these essential info columns. Any other uploaded columns will be discarded.")
            for col in META_COLUMNS:
                selectbox_mapping(col, col, uploaded_cols, col, mapping)
        with tab_q:
            st.warning("Map all baseline question columns and all endline/post question columns.")
            for base_col in BASELINE_QUESTION_COLS:
                c1, c2 = st.columns(2)
                with c1:
                    selectbox_mapping(question_mapping_label(base_col), base_col, uploaded_cols, base_col, mapping)
                with c2:
                    post_col = f"{base_col}_post"
                    selectbox_mapping(question_mapping_label(post_col), post_col, uploaded_cols, post_col, mapping, endline_hint=True)
        with tab_preview:
            st.dataframe(raw_df.head(20), use_container_width=True)

        required_keys = META_COLUMNS + BASELINE_QUESTION_COLS + ENDLINE_QUESTION_COLS

        if st.button("Next: Score text values", type="primary"):
            missing = [k for k in required_keys if not mapping.get(k)]
            selected = [mapping.get(k, "") for k in required_keys if mapping.get(k)]
            duplicates = sorted({x for x in selected if selected.count(x) > 1})
            if missing:
                st.error("Required columns still not mapped: " + ", ".join(missing))
            elif duplicates:
                st.error("Some uploaded columns are mapped more than once: " + ", ".join(duplicates))
            else:
                st.session_state.column_mapping = mapping
                st.session_state.mapped_df = build_same_row_df(raw_df, mapping)
                st.session_state.selected_delete_indices = set()
                go_next()

    elif upload_type.startswith("Two files"):
        base_df = st.session_state.base_df
        end_df = st.session_state.end_df
        base_cols = list(base_df.columns)
        end_cols = list(end_df.columns)
        st.write("Map baseline columns from the baseline file, and endline columns from the endline file.")
        tab_ids, tab_meta, tab_base, tab_end = st.tabs(["ID columns", "Essential baseline info", "Baseline questions", "Endline questions"])
        with tab_ids:
            selectbox_mapping("Baseline unique child/beneficiary ID", "caseid", base_cols, "base_id", mapping)
            selectbox_mapping("Endline unique child/beneficiary ID", "caseid", end_cols, "end_id", mapping)
        with tab_meta:
            st.warning("Map these essential info columns from the baseline file. Any other uploaded columns will be discarded.")
            selectbox_mapping("Baseline IDELA_date", "IDELA_date", base_cols, "base_IDELA_date", mapping)
            for col in [c for c in META_COLUMNS if c not in ["caseid", "IDELA_date"]]:
                selectbox_mapping(col, col, base_cols, f"base_{col}", mapping)
        with tab_base:
            for base_col in BASELINE_QUESTION_COLS:
                selectbox_mapping(question_mapping_label(base_col), base_col, base_cols, f"base_{base_col}", mapping)
        with tab_end:
            for base_col in BASELINE_QUESTION_COLS:
                selectbox_mapping(question_mapping_label(f"{base_col}_post"), base_col, end_cols, f"end_{base_col}", mapping, endline_hint=True)

        required_keys = ["base_id", "end_id", "base_IDELA_date"] + [f"base_{c}" for c in META_COLUMNS if c not in ["caseid", "IDELA_date"]] + [f"base_{c}" for c in BASELINE_QUESTION_COLS] + [f"end_{c}" for c in BASELINE_QUESTION_COLS]
        if st.button("Next: Score text values", type="primary"):
            missing = [k for k in required_keys if not mapping.get(k)]
            base_selected = [mapping.get(k, "") for k in required_keys if k.startswith("base_") and mapping.get(k)] + ([mapping.get("base_id")] if mapping.get("base_id") else [])
            end_selected = [mapping.get(k, "") for k in required_keys if k.startswith("end_") and mapping.get(k)] + ([mapping.get("end_id")] if mapping.get("end_id") else [])
            base_dups = sorted({x for x in base_selected if x and base_selected.count(x) > 1})
            end_dups = sorted({x for x in end_selected if x and end_selected.count(x) > 1})
            if missing:
                st.error("Required columns still not mapped: " + ", ".join(missing))
            elif base_dups or end_dups:
                st.error("Duplicate mappings found. Baseline: " + ", ".join(base_dups) + " Endline: " + ", ".join(end_dups))
            else:
                st.session_state.column_mapping = mapping
                st.session_state.mapped_df = build_two_file_df(base_df, end_df, mapping)
                st.session_state.selected_delete_indices = set()
                go_next()

    else:
        raw_df = st.session_state.raw_df
        uploaded_cols = list(raw_df.columns)
        st.write("Map the ID column, round column, then select which round value means baseline and endline.")
        tab_setup, tab_meta, tab_q, tab_preview = st.tabs(["ID and round", "Essential info columns", "Question columns", "Preview"])
        with tab_setup:
            selectbox_mapping("Unique child/beneficiary ID", "caseid", uploaded_cols, "dup_id", mapping)
            selectbox_mapping("Round/status column that says baseline/endline", "round", uploaded_cols, "round_col", mapping)
            round_values = []
            if mapping.get("round_col"):
                round_values = sorted([str(x) for x in raw_df[mapping["round_col"]].dropna().unique().tolist()])
            c1, c2 = st.columns(2)
            with c1:
                baseline_value = st.selectbox("Which value means baseline?", options=round_values, key="baseline_round_value") if round_values else None
            with c2:
                endline_value = st.selectbox("Which value means endline?", options=round_values, key="endline_round_value") if round_values else None
        with tab_q:
            for base_col in BASELINE_QUESTION_COLS:
                selectbox_mapping(question_mapping_label(base_col), base_col, uploaded_cols, f"q_{base_col}", mapping)
        with tab_meta:
            st.warning("Map these essential info columns. Any other uploaded columns will be discarded.")
            selectbox_mapping("IDELA_date", "IDELA_date", uploaded_cols, "meta_IDELA_date", mapping)
            for col in [c for c in META_COLUMNS if c not in ["caseid", "IDELA_date"]]:
                selectbox_mapping(col, col, uploaded_cols, f"meta_{col}", mapping)
        with tab_preview:
            st.dataframe(raw_df.head(20), use_container_width=True)

        required_keys = ["dup_id", "round_col", "meta_IDELA_date"] + [f"meta_{c}" for c in META_COLUMNS if c not in ["caseid", "IDELA_date"]] + [f"q_{c}" for c in BASELINE_QUESTION_COLS]
        if st.button("Next: Score text values", type="primary"):
            missing = [k for k in required_keys if not mapping.get(k)]
            selected = [mapping.get(k, "") for k in required_keys if mapping.get(k)]
            duplicates = sorted({x for x in selected if x and selected.count(x) > 1})
            if missing:
                st.error("Required columns still not mapped: " + ", ".join(missing))
            elif not baseline_value or not endline_value or baseline_value == endline_value:
                st.error("Select different baseline and endline values from the round column.")
            elif duplicates:
                st.error("Some uploaded columns are mapped more than once: " + ", ".join(duplicates))
            else:
                st.session_state.column_mapping = mapping
                st.session_state.mapped_df = build_duplicated_rows_df(raw_df, mapping, baseline_value, endline_value)
                st.session_state.selected_delete_indices = set()
                go_next()

    st.session_state.column_mapping = mapping
    if st.button("Back"):
        go_back()

# STEP 3: Score/recode text values
elif st.session_state.step == 3:
    st.subheader("Step 3: Score text values in question fields")
    mapped_df = st.session_state.mapped_df.copy()
    all_question_cols = [c for c in BASELINE_QUESTION_COLS + ENDLINE_QUESTION_COLS if c in mapped_df.columns]
    unscored_df = detect_unscored_values(mapped_df, all_question_cols)

    if unscored_df.empty:
        st.success("All question fields are already numeric, or contain only recognized missing values.")
        st.session_state.scored_df = mapped_df
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back"):
                go_back()
        with c2:
            if st.button("Next: Review rows", type="primary"):
                go_next()
    else:
        st.warning("Some question values are text/not scored. Choose the numeric score for each uploaded value.")
        st.caption("This page is now using direct input boxes instead of a table editor, so every value can be changed reliably.")

        unique_values = (
            unscored_df.groupby("Uploaded value", as_index=False)
            .agg({"Rows": "sum", "Column": lambda x: ", ".join(sorted(set(x))[:5]) + ("..." if len(set(x)) > 5 else "")})
            .rename(columns={"Column": "Example columns", "Rows": "Total rows"})
        )

        saved = st.session_state.value_recode_mapping or {}
        recode_mapping = {}

        st.markdown("#### Enter scoring rules")
        st.info("Recommended: correct/true/yes = 1, incorrect/not_true/no = 0, no_response/---/blank = 999 if you want to handle missing later.")

        header = st.columns([2, 1, 1, 4])
        header[0].markdown("**Uploaded value**")
        header[1].markdown("**Score**")
        header[2].markdown("**Rows**")
        header[3].markdown("**Example columns**")

        for i, row in unique_values.iterrows():
            uploaded_value = str(row["Uploaded value"])
            suggestion = saved.get(uploaded_value, default_score_suggestion(uploaded_value))
            if suggestion is None:
                suggestion = 999

            c1, c2, c3, c4 = st.columns([2, 1, 1, 4])
            with c1:
                st.code(uploaded_value, language=None)
            with c2:
                score = st.number_input(
                    label=f"Score for {uploaded_value}",
                    value=float(suggestion),
                    step=1.0,
                    key=f"score_value_{i}_{normalize_name(uploaded_value)[:30]}",
                    label_visibility="collapsed",
                )
                # Store as int when possible
                recode_mapping[uploaded_value] = int(score) if float(score).is_integer() else score
            with c3:
                st.write(int(row["Total rows"]))
            with c4:
                st.caption(str(row["Example columns"]))

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back"):
                go_back()
        with c2:
            if st.button("Apply scores and continue", type="primary"):
                st.session_state.value_recode_mapping = recode_mapping
                scored_df = apply_value_recode(mapped_df, all_question_cols, recode_mapping)
                remaining_unscored = detect_unscored_values(scored_df, all_question_cols)
                if len(remaining_unscored) > 0:
                    st.error("Some text values are still not scored. Please review the list again.")
                    st.dataframe(remaining_unscored, use_container_width=True)
                else:
                    st.session_state.scored_df = scored_df
                    go_next()

# STEP 4: Row review
elif st.session_state.step == 4:
    st.subheader("Step 4: Review rows with high missing percentage")
    mapped_df = st.session_state.scored_df.copy() if st.session_state.scored_df is not None else st.session_state.mapped_df.copy()

    if "IDELA_date" not in mapped_df.columns:
        st.error("IDELA_date is missing. Go back and map it.")
        st.stop()

    mapped_df["IDELA_date_parsed"] = pd.to_datetime(mapped_df["IDELA_date"], errors="coerce")
    filtered_df = mapped_df[mapped_df["IDELA_date_parsed"].notna()].drop(columns=["IDELA_date_parsed"]).copy()
    all_question_cols = [c for c in BASELINE_QUESTION_COLS + ENDLINE_QUESTION_COLS if c in filtered_df.columns]
    filtered_df = normalize_score_values(filtered_df, all_question_cols)

    filtered_df.insert(0, "Delete Action", "")
    filtered_df.insert(1, "baseline missing %", missing_pct(filtered_df, BASELINE_QUESTION_COLS))
    filtered_df.insert(2, "endline missing %", missing_pct(filtered_df, ENDLINE_QUESTION_COLS))
    st.session_state.filtered_df = filtered_df

    st.write(f"Rows after merge and IDELA_date validation: **{len(filtered_df)}**")
    high_missing = filtered_df[(filtered_df["baseline missing %"] > 0.30) | (filtered_df["endline missing %"] > 0.30)].copy()
    st.warning(f"Rows with baseline or endline missing above 30%: {len(high_missing)}")

    delete_indices = []
    if len(high_missing) > 0:
        high_missing_display = high_missing.copy()
        high_missing_display["baseline missing %"] *= 100
        high_missing_display["endline missing %"] *= 100
        display_cols = [c for c in ["caseid", "d_childs_full_name", "child_name", "student_name", "e_childs_sex", "f_childs_age", "teacher_location"] if c in high_missing_display.columns]
        display_cols += ["baseline missing %", "endline missing %"]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            page_size = st.selectbox("Rows per page", [50, 100, 200, 500], index=1)
        total_pages = max(1, (len(high_missing_display) - 1) // page_size + 1)
        with c2:
            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
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
        edited_page = st.data_editor(
            page_df[["Select Delete"] + display_cols],
            use_container_width=True,
            hide_index=False,
            key=f"delete_editor_page_{page}_{page_size}",
            column_config={
                "baseline missing %": st.column_config.NumberColumn("baseline missing %", format="%.1f%%"),
                "endline missing %": st.column_config.NumberColumn("endline missing %", format="%.1f%%"),
            },
        )
        selected_on_page = set(edited_page.index[edited_page["Select Delete"] == True].tolist())
        st.session_state.selected_delete_indices -= current_page_indices
        st.session_state.selected_delete_indices |= selected_on_page
        delete_indices = list(st.session_state.selected_delete_indices)
        st.info(f"Selected rows to delete: **{len(delete_indices)}** out of **{len(high_missing_display)}** high-missing rows. Showing page **{page}** of **{total_pages}**.")

    clean_base = filtered_df.drop(index=delete_indices).copy()
    clean_base = clean_base.drop(columns=["Delete Action", "baseline missing %", "endline missing %"], errors="ignore")
    st.session_state.clean_base = clean_base

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back"):
            go_back()
    with c2:
        if st.button("Next: Question actions", type="primary"):
            go_next()

# STEP 5: Question actions
elif st.session_state.step == 5:
    st.subheader("Step 5: Question Missing Review and Actions")
    clean_base = st.session_state.clean_base.copy()
    action_options = ["No action", "change missing to 0", "drop this question"]

    question_review_rows = []
    for base_col in BASELINE_QUESTION_COLS:
        post_col = f"{base_col}_post"
        question_name = QUESTION_LABELS.get(base_col, base_col)
        arabic_name, english_name = question_name.split(" | ", 1) if " | " in question_name else ("", question_name)
        question_review_rows.append({
            "Baseline ID": base_col,
            "Endline ID": post_col,
            "Arabic": arabic_name,
            "English": english_name,
            "% Missing Baseline": question_missing_pct(clean_base, base_col),
            "% Missing Endline": question_missing_pct(clean_base, post_col),
            "Action": st.session_state.actions.get(base_col, "No action"),
        })

    question_review_df = pd.DataFrame(question_review_rows)
    edited_actions = st.data_editor(
        question_review_df,
        column_config={
            "Baseline ID": st.column_config.TextColumn("Baseline ID", disabled=True),
            "Endline ID": st.column_config.TextColumn("Endline ID", disabled=True),
            "Arabic": st.column_config.TextColumn("Arabic", disabled=True),
            "English": st.column_config.TextColumn("English", disabled=True),
            "% Missing Baseline": st.column_config.ProgressColumn("% Missing Baseline", format="%.1f%%", min_value=0, max_value=1),
            "% Missing Endline": st.column_config.ProgressColumn("% Missing Endline", format="%.1f%%", min_value=0, max_value=1),
            "Action": st.column_config.SelectboxColumn("Action", options=action_options, required=True),
        },
        disabled=["Baseline ID", "Endline ID", "Arabic", "English", "% Missing Baseline", "% Missing Endline"],
        hide_index=True,
        use_container_width=True,
        key="question_action_editor",
    )

    st.session_state.actions = dict(zip(edited_actions["Baseline ID"], edited_actions["Action"]))
    st.info("If you choose 'drop this question', both the baseline question and its matching endline question are removed.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back"):
            go_back()
    with c2:
        if st.button("Next: Download", type="primary"):
            go_next()

# STEP 6: Download
elif st.session_state.step == 6:
    st.subheader("Step 6: Preview and Download")
    clean_base = st.session_state.clean_base.copy()
    filtered_df = st.session_state.filtered_df.copy()
    actions = st.session_state.actions

    clean_df = apply_actions(clean_base, actions)
    by_question_df = create_by_question(clean_df, BASELINE_QUESTION_COLS)

    st.write("Clean data preview")
    st.dataframe(clean_df.head(20), use_container_width=True)

    remaining_question_cols = [c for c in BASELINE_QUESTION_COLS + ENDLINE_QUESTION_COLS if c in clean_df.columns]
    remaining_missing_summary = get_remaining_missing_summary(clean_df, remaining_question_cols)

    if len(remaining_missing_summary) > 0:
        missing_columns = sorted(remaining_missing_summary["Question ID"].tolist())
        st.error("Download is blocked. Missing is still in these columns:\n\n" + "\n".join(missing_columns))
        st.warning("Go back to Step 4 and choose an action for these question columns, such as changing missing to 0 or dropping the question.")
    else:
        sheets = {
            "filtered on Idela": filtered_df,
            "idela clean data set": clean_df,
            "BY QUESTION": by_question_df,
            "BY ITEM": pd.DataFrame(),
            "BY DOMAIN": pd.DataFrame(),
            "IDELA ANALYSIS": pd.DataFrame(),
        }
        excel_bytes = to_excel_bytes(sheets)
        st.success("No 999, ---, blank, or null values remain in the question columns. You can download the cleaned workbook.")
        st.download_button(
            label="Download cleaned IDELA workbook",
            data=excel_bytes,
            file_name="idela_cleaned_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

    if st.button("Back"):
        go_back()
