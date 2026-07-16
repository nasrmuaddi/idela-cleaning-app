import io
import re
import difflib
from typing import Dict, List

import pandas as pd
import streamlit as st

try:
    from streamlit_sortables import sort_items
    _HAS_SORTABLES = True
except Exception:
    _HAS_SORTABLES = False

st.set_page_config(page_title="IDELA Cleaning App", layout="wide")
st.title("IDELA Cleaning App")
st.caption("Upload, map columns, review missing values, choose actions, and download a cleaned workbook.")

META_COLUMNS = [
    "caseid", "idela_child_pwd", "If_yes_due_to_pwd",
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

# Questions whose answer is a count/level rather than 0/1. Values are the DEFAULT max score
# (each question individually). The user can override these in the max-score step.
# Item 5 = i5_row12 + i5_row34 (10 + 10 = 20 combined); Item 15 likewise.
COUNT_QUESTION_DEFAULT_MAX = {
    "i5_row12_correct_count": 10,
    "i5_row34_correct_count": 10,
    "i8_friends_count": 10,
    "i13_market_items_count": 10,
    "i13_animals_count": 10,
    "i15_row12_letters_count": 10,
    "i15_row34_letters_count": 10,
    "i17_writing_level": 4,
    "i19_closed_corners": 4,
    "i21_steps": 10,
}

# Four eye-restful colors, each with light / medium / dark variants.
RESTFUL_COLORS = {
    "slate_blue": {"light": "#EAF1F7", "medium": "#C6D8E8", "dark": "#4E6E8E"},
    "sage_green": {"light": "#EBF3EC", "medium": "#CBE3D0", "dark": "#5C8768"},
    "warm_sand":  {"light": "#FAF3E7", "medium": "#EEDFC2", "dark": "#B08E52"},
    "soft_mauve": {"light": "#F2ECF4", "medium": "#DFD1E6", "dark": "#846A99"},
}
RESTFUL_ORDER = ["slate_blue", "sage_green", "warm_sand", "soft_mauve"]

SORTABLE_CSS = """
.sortable-component { gap: 10px; }
.sortable-container { border-radius: 8px; border: 1px solid #d9d9d9; margin-bottom: 6px; }
.sortable-container-header { font-weight: 600; padding: 6px 10px; border-radius: 8px 8px 0 0; }
.sortable-container-body { padding: 6px; min-height: 40px; border-radius: 0 0 8px 8px; }
.sortable-item { background: #ffffff; color: #243b53; border: 1px solid #cfcfcf; border-radius: 6px; padding: 5px 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; cursor: grab; }
.sortable-item:hover { white-space: normal; overflow: visible; background: #fffdf5; box-shadow: 0 3px 12px rgba(0,0,0,.22); position: relative; z-index: 20; }
.sortable-container:nth-child(4n+1) .sortable-container-header { background: #C6D8E8; }
.sortable-container:nth-child(4n+2) .sortable-container-header { background: #CBE3D0; }
.sortable-container:nth-child(4n+3) .sortable-container-header { background: #EEDFC2; }
.sortable-container:nth-child(4n+4) .sortable-container-header { background: #DFD1E6; }
.sortable-container:nth-child(4n+1) .sortable-container-body { background: #EAF1F7; }
.sortable-container:nth-child(4n+2) .sortable-container-body { background: #EBF3EC; }
.sortable-container:nth-child(4n+3) .sortable-container-body { background: #FAF3E7; }
.sortable-container:nth-child(4n+4) .sortable-container-body { background: #F2ECF4; }
"""

ITEM_MAPPING = {
    "i1a_name_mark": "ITEM_1",
    "i1a_age_mark": "ITEM_1",
    "i1a_sex_mark": "ITEM_1",
    "i1a_caregiver_mark": "ITEM_1",
    "i1a_neighborhood_mark": "ITEM_1",
    "i1a_state_mark": "ITEM_1",
    "i1a_country_mark": "ITEM_1",
    "country_from_mark": "ITEM_1",
    "i2a_biggest_circle_mark": "ITEM_2",
    "i2b_smallest_circle_mark": "ITEM_2",
    "i2c_longest_stick_mark": "ITEM_2",
    "i2d_shortest_stick_mark": "ITEM_2",
    "i3_sort_criterion1_mark": "ITEM_3",
    "i3_sort_criterion2_mark": "ITEM_3",
    "i4_circle_mark": "ITEM_4",
    "i4_rectangle_mark": "ITEM_4",
    "i4_triangle_mark": "ITEM_4",
    "i4_square_mark": "ITEM_4",
    "i4_circle_env_mark": "ITEM_4",
    "i5_row12_correct_count": "ITEM_5",
    "i5_row34_correct_count": "ITEM_5",
    "i6_give3_mark": "ITEM_6",
    "i6_give5_mark": "ITEM_6",
    "i6_give8_mark": "ITEM_6",
    "i6_focus_mark": "ITEM_6",
    "i6_eager_mark": "ITEM_6",
    "i7_add3_2_mark": "ITEM_7",
    "i7_add2_2_mark": "ITEM_7",
    "i7_subtract1_from3_mark": "ITEM_7",
    "i8_friends_count": "ITEM_8",
    "i9_sad_trigger_mark": "ITEM_9",
    "i9_regulate1_mark": "ITEM_9",
    "i9_regulate2_mark": "ITEM_9",
    "i9_happy_trigger_mark": "ITEM_9",
    "i10_understands_feeling_mark": "ITEM_10",
    "i10_help1_mark": "ITEM_10",
    "i10_help2_mark": "ITEM_10",
    "i11_conflict1_mark": "ITEM_11",
    "i11_conflict2_mark": "ITEM_11",
    "i12_seq1_mark": "ITEM_12",
    "i12_seq2_mark": "ITEM_12",
    "i12_seq3_mark": "ITEM_12",
    "i12_seq4_mark": "ITEM_12",
    "i13_market_items_count": "ITEM_13",
    "i13_animals_count": "ITEM_13",
    "i14_open_book_mark": "ITEM_14",
    "i14_point_text_mark": "ITEM_14",
    "i14_text_direction_mark": "ITEM_14",
    "i15_row12_letters_count": "ITEM_15",
    "i15_row34_letters_count": "ITEM_15",
    "i16_s_pair_mark": "ITEM_16",
    "i16_t_pair_mark": "ITEM_16",
    "i16_c_pair_mark": "ITEM_16",
    "i17_writing_level": "ITEM_17",
    "i18_mouse_stole_hat_mark": "ITEM_18",
    "i18_hat_color_mark": "ITEM_18",
    "i18_why_chased_mark": "ITEM_18",
    "i18_where_trapped_mark": "ITEM_18",
    "i18_why_spared_mark": "ITEM_18",
    "i18_focus_mark": "ITEM_18",
    "i18_eager_mark": "ITEM_18",
    "i19_closed_corners": "ITEM_19",
    "i19_exited_mark": "ITEM_19",
    "i20_head_mark": "ITEM_20",
    "i20_torso_mark": "ITEM_20",
    "i20_arms_mark": "ITEM_20",
    "i20_legs_mark": "ITEM_20",
    "i20_face1_mark": "ITEM_20",
    "i20_face2_mark": "ITEM_20",
    "i20_hands_mark": "ITEM_20",
    "i20_feet_mark": "ITEM_20",
    "i20_focus_mark": "ITEM_20",
    "i20_eager_mark": "ITEM_20",
    "i21_steps": "ITEM_21",
}

ITEM_NAMES = {
    "ITEM_1": "Personal Awareness",
    "ITEM_2": "Comparison by Size and Length",
    "ITEM_3": "Sorting and Classification",
    "ITEM_4": "Shape Identification",
    "ITEM_5": "Number ID",
    "ITEM_6": "Number Sense – One to one Correspondence",
    "ITEM_7": "Addition and Subtraction",
    "ITEM_8": "Friends",
    "ITEM_9": "Emotional Awareness/Regulation",
    "ITEM_10": "Empathy/Perspective Taking",
    "ITEM_11": "Sharing/Solving Conflict",
    "ITEM_12": "Short-Term Memory",
    "ITEM_13": "Oral Vocabulary",
    "ITEM_14": "Print Awareness",
    "ITEM_15": "Letter Identification",
    "ITEM_16": "First Letter Sounds",
    "ITEM_17": "Emergent Writing",
    "ITEM_18": "Oral Comprehension",
    "ITEM_19": "Copying a Shape",
    "ITEM_20": "Drawing a Person",
    "ITEM_21": "Hopping",
}

DOMAIN_MAPPING = {
    "Motor Skills": ["ITEM_19", "ITEM_20", "ITEM_21"],
    "Early Literacy Skills": ["ITEM_13", "ITEM_14", "ITEM_15", "ITEM_16", "ITEM_17", "ITEM_18"],
    "Early Numeracy Skills": ["ITEM_2", "ITEM_3", "ITEM_4", "ITEM_5", "ITEM_6", "ITEM_7"],
    "Social Emotional Skills": ["ITEM_1", "ITEM_8", "ITEM_9", "ITEM_10", "ITEM_11", "ITEM_12"],
}


def question_mapping_label(question_col: str) -> str:
    """Show question IDs with English and Arabic descriptions during mapping."""
    base_col = question_col.replace("_post", "")
    label = QUESTION_LABELS.get(base_col, base_col)
    if " | " in label:
        arabic, english = label.split(" | ", 1)
        return f"{question_col} — {english.strip()} | {arabic.strip()}"
    return f"{question_col} — {label}"


def question_excel_name(base_col: str, language: str = "both") -> str:
    """Return readable question names for Excel sheets instead of question IDs."""
    label = QUESTION_LABELS.get(base_col.replace("_post", ""), base_col)
    if " | " not in label:
        return label
    arabic, english = [x.strip() for x in label.split(" | ", 1)]
    if language == "english":
        return english
    if language == "arabic":
        return arabic
    return f"{english} | {arabic}"


def comparison_status(series: pd.Series) -> pd.Series:
    """Convert numeric comparison values to Improved / Decreased / No change."""
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.apply(lambda x: "Improved" if x > 0 else ("Decreased" if x < 0 else "No change"))


def init_state():
    defaults = {
        "step": 1,
        "upload_type": None,
        "column_mapping": {},
        "mapped_df": None,
        "download_raw_df": None,
        "filtered_df": None,
        "clean_base": None,
        "scored_df": None,
        "paired_df": None,
        "pairing_summary": {},
        "item_mapping": dict(ITEM_MAPPING),
        "domain_mapping": {k: list(v) for k, v in DOMAIN_MAPPING.items()},
        "qa_ready": False,
        "max_scores": {},
        "value_recode_mapping": {},
        "actions": {},
        "selected_delete_indices": set(),
        "idela_date_filter_column": None,
        "idela_date_filter_summary": {},
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
    st.session_state.idela_date_filter_column = None
    st.session_state.idela_date_filter_summary = {}


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


BLANK_VALUE_LABEL = "[blank / empty cell]"


def is_missing_question_value(series: pd.Series) -> pd.Series:
    as_text = series.astype("string").str.strip().str.lower()
    numeric = pd.to_numeric(series, errors="coerce")
    return (
        series.isna()
        | as_text.isin(["---", "", "999", "nan", "none", "null"])
        | numeric.eq(999)
    )


def normalize_score_values(df: pd.DataFrame, question_cols: List[str]) -> pd.DataFrame:
    out = df.copy()
    for col in question_cols:
        if col in out.columns:
            out[col] = out[col].replace({"---": 999, "": pd.NA, " ": pd.NA})
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out




def replace_question_nulls_with_dash(df: pd.DataFrame, question_cols: List[str]) -> pd.DataFrame:
    """Convert real nulls/blanks in question fields to --- before scoring detection."""
    out = df.copy()
    for col in question_cols:
        if col not in out.columns:
            continue
        out[col] = out[col].astype("object")
        out[col] = out[col].where(~out[col].isna(), "---")
        out[col] = out[col].replace({
            "": "---",
            " ": "---",
            "nan": "---",
            "NaN": "---",
            "NONE": "---",
            "None": "---",
            "null": "---",
            "NULL": "---",
            "<NA>": "---",
            "<na>": "---",
        })
    return out

def detect_unscored_values(df: pd.DataFrame, question_cols: List[str]) -> pd.DataFrame:
    """
    Find uploaded TEXT values in question columns that still need scoring.

    Important behavior:
    - Real blanks/nulls are shown as blank / empty cell.
    - --- is shown so the user can score missing values.
    - Numeric values such as 0, 1, 2, and 999 are NOT shown again.
      This prevents 999 from reappearing after the user already scored --- or no_response as 999.
    """
    rows = []

    for col in question_cols:
        if col not in df.columns:
            continue

        s = df[col]
        as_text = s.astype("string").str.strip()
        as_text_lower = as_text.str.lower()
        numeric = pd.to_numeric(as_text, errors="coerce")

        # 1) Ask about real blank/null cells. In normal flow these are converted to --- before Step 3,
        # but this stays here as a safety net.
        blank_mask = s.isna() | as_text_lower.isin(["", "nan", "none", "null", "<na>"])
        if blank_mask.any():
            rows.append({
                "Column": col,
                "Uploaded value": BLANK_VALUE_LABEL,
                "Rows": int(blank_mask.sum()),
            })

        # 2) Ask about --- only. Do NOT ask about 999 because 999 is a valid numeric missing score.
        dash_mask = ~blank_mask & as_text_lower.eq("---")
        if dash_mask.any():
            rows.append({
                "Column": col,
                "Uploaded value": "---",
                "Rows": int(dash_mask.sum()),
            })

        # 3) Ask about non-numeric text values only. Numeric values, including 999, are skipped.
        text_mask = (
            ~blank_mask
            & ~dash_mask
            & ~numeric.notna()
        )
        if text_mask.any():
            for value, count in as_text[text_mask].value_counts(dropna=True).items():
                rows.append({
                    "Column": col,
                    "Uploaded value": str(value),
                    "Rows": int(count),
                })

    return pd.DataFrame(rows)


def default_score_suggestion(value: str):
    v = str(value).strip().lower()
    v_norm = v.replace("-", "_").replace(" ", "_")
    positive = {"correct", "yes", "true", "y", "appropriate_response", "صحيح", "نعم"}
    negative = {"incorrect", "not_correct", "wrong", "no", "false", "not_true", "n", "خطأ", "غير صحيح", "لا"}
    if v == BLANK_VALUE_LABEL.lower():
        return 999
    if v_norm in positive:
        return 1
    if v_norm in negative:
        return 0
    # Missing-style values should default to 999, but user can change them.
    if v_norm in {"999", "999.0", "---", "missing", "na", "n/a", "null", "blank", "none", "nan", "<na>"}:
        return 999
    # Any no-response typo/variant should default to missing.
    if "response" in v_norm or "resonse" in v_norm or "rsponse" in v_norm:
        return 999
    return 999


def apply_value_recode(df: pd.DataFrame, question_cols: List[str], recode_mapping: Dict[str, object]) -> pd.DataFrame:
    """Replace text answers and blank/missing-code cells in question fields with user-selected scores."""
    out = df.copy()
    clean_mapping = {}
    blank_score = recode_mapping.get(BLANK_VALUE_LABEL, None)
    try:
        blank_score = float(blank_score) if blank_score is not None else None
    except Exception:
        blank_score = None

    for value, score in recode_mapping.items():
        try:
            clean_mapping[str(value).strip().lower()] = float(score)
        except Exception:
            continue

    for col in question_cols:
        if col not in out.columns:
            continue

        def recode_cell(x):
            raw = str(x).strip().lower()
            if pd.isna(x) or raw in ["", "nan", "none", "null", "<na>"]:
                return blank_score if blank_score is not None else x
            if raw == "999.0" and "999" in clean_mapping:
                return clean_mapping["999"]
            return clean_mapping.get(raw, x)

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
    """Create question-level sheet using question names instead of IDs."""
    out = clean_df[[c for c in META_COLUMNS if c in clean_df.columns]].copy()
    used_baseline_score_cols = []
    used_endline_score_cols = []

    for base_col in baseline_cols:
        post_col = f"{base_col}_post"
        if base_col not in clean_df.columns or post_col not in clean_df.columns:
            continue

        question_name = question_excel_name(base_col, language="both")
        base_numeric = pd.to_numeric(clean_df[base_col], errors="coerce")
        post_numeric = pd.to_numeric(clean_df[post_col], errors="coerce")

        out[f"{question_name} - baseline"] = base_numeric
        out[f"{question_name} - endline"] = post_numeric
        comp_col = f"{question_name} - comparison"
        out[comp_col] = post_numeric - base_numeric
        out[f"{question_name} - comparison status"] = comparison_status(out[comp_col])

        used_baseline_score_cols.append(base_col)
        used_endline_score_cols.append(post_col)

    out["baseline idela score"] = clean_df[used_baseline_score_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1) if used_baseline_score_cols else 0
    out["endline idela score"] = clean_df[used_endline_score_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1) if used_endline_score_cols else 0
    out["idela score"] = out["endline idela score"] - out["baseline idela score"]
    out["idela score status"] = comparison_status(out["idela score"])
    return out



def create_by_item(clean_df: pd.DataFrame, item_mapping=None) -> pd.DataFrame:
    """Create item-level baseline/endline/comparison scores per row."""
    if item_mapping is None:
        item_mapping = ITEM_MAPPING
    out = clean_df[[c for c in META_COLUMNS if c in clean_df.columns]].copy()
    item_score_cols_base = []
    item_score_cols_end = []

    ordered_items = [f"ITEM_{i}" for i in range(1, 22)]
    for item_id in ordered_items:
        item_name = ITEM_NAMES.get(item_id, item_id)
        base_questions = [q for q, item in item_mapping.items() if item == item_id and q in clean_df.columns]
        end_questions = [f"{q}_post" for q, item in item_mapping.items() if item == item_id and f"{q}_post" in clean_df.columns]

        base_col_name = f"{item_id} {item_name} baseline"
        end_col_name = f"{item_id} {item_name} endline"
        comp_col_name = f"{item_id} {item_name} comparison"

        if base_questions:
            out[base_col_name] = clean_df[base_questions].apply(pd.to_numeric, errors="coerce").sum(axis=1)
        else:
            out[base_col_name] = 0

        if end_questions:
            out[end_col_name] = clean_df[end_questions].apply(pd.to_numeric, errors="coerce").sum(axis=1)
        else:
            out[end_col_name] = 0

        out[comp_col_name] = out[end_col_name] - out[base_col_name]
        out[f"{item_id} {item_name} comparison status"] = comparison_status(out[comp_col_name])
        item_score_cols_base.append(base_col_name)
        item_score_cols_end.append(end_col_name)

    out["baseline idela score"] = out[item_score_cols_base].sum(axis=1) if item_score_cols_base else 0
    out["endline idela score"] = out[item_score_cols_end].sum(axis=1) if item_score_cols_end else 0
    out["idela score"] = out["endline idela score"] - out["baseline idela score"]
    out["idela score status"] = comparison_status(out["idela score"])
    return out


def create_by_domain(by_item_df: pd.DataFrame, domain_mapping=None) -> pd.DataFrame:
    """Create domain-level baseline/endline/comparison scores using item scores."""
    if domain_mapping is None:
        domain_mapping = DOMAIN_MAPPING
    out = by_item_df[[c for c in META_COLUMNS if c in by_item_df.columns]].copy()
    domain_base_cols = []
    domain_end_cols = []

    for domain_name, items in domain_mapping.items():
        item_base_cols = []
        item_end_cols = []
        for item_id in items:
            item_name = ITEM_NAMES.get(item_id, item_id)
            base_col = f"{item_id} {item_name} baseline"
            end_col = f"{item_id} {item_name} endline"
            if base_col in by_item_df.columns:
                item_base_cols.append(base_col)
            if end_col in by_item_df.columns:
                item_end_cols.append(end_col)

        base_domain_col = f"{domain_name} baseline"
        end_domain_col = f"{domain_name} endline"
        comp_domain_col = f"{domain_name} comparison"

        out[base_domain_col] = by_item_df[item_base_cols].sum(axis=1) if item_base_cols else 0
        out[end_domain_col] = by_item_df[item_end_cols].sum(axis=1) if item_end_cols else 0
        out[comp_domain_col] = out[end_domain_col] - out[base_domain_col]
        out[f"{domain_name} comparison status"] = comparison_status(out[comp_domain_col])

        domain_base_cols.append(base_domain_col)
        domain_end_cols.append(end_domain_col)

    out["baseline idela score"] = out[domain_base_cols].sum(axis=1) if domain_base_cols else 0
    out["endline idela score"] = out[domain_end_cols].sum(axis=1) if domain_end_cols else 0
    out["idela score"] = out["endline idela score"] - out["baseline idela score"]
    out["idela score status"] = comparison_status(out["idela score"])
    return out


def create_status_dashboard(df: pd.DataFrame, analysis_columns: Dict[str, str], dashboard_type: str) -> pd.DataFrame:
    """
    Create an Excel-friendly interactive dashboard source table.

    Each row summarizes the comparison status distribution for one analysis column
    by one essential-info column/value. Users can filter this sheet in Excel by
    essential column, category value, item/domain, or status percentages.
    """
    essential_cols = [
        c for c in META_COLUMNS
        if c in df.columns and c not in ["caseid", "IDELA_date"]
    ]
    statuses = ["Improved", "No change", "Decreased"]
    rows = []

    for analysis_name, status_col in analysis_columns.items():
        if status_col not in df.columns:
            continue

        status_series = df[status_col].fillna("No change").astype(str)

        # Overall row, useful when no demographic/filter split is needed.
        overall_counts = status_series.value_counts()
        overall_total = int(overall_counts.reindex(statuses, fill_value=0).sum())
        row = {
            "Dashboard Type": dashboard_type,
            "Essential info column": "Overall",
            "Essential info value": "All children",
            "Analysis": analysis_name,
            "Total counted": overall_total,
        }
        for status in statuses:
            count = int(overall_counts.get(status, 0))
            row[f"{status} count"] = count
            row[f"{status} %"] = count / overall_total if overall_total else 0
        rows.append(row)

        for essential_col in essential_cols:
            grouped = pd.DataFrame({
                "group_value": df[essential_col].fillna("[blank]").astype(str).str.strip().replace({"": "[blank]"}),
                "status": status_series,
            })

            for group_value, group_df in grouped.groupby("group_value", dropna=False):
                counts = group_df["status"].value_counts()
                total = int(counts.reindex(statuses, fill_value=0).sum())
                row = {
                    "Dashboard Type": dashboard_type,
                    "Essential info column": essential_col,
                    "Essential info value": group_value,
                    "Analysis": analysis_name,
                    "Total counted": total,
                }
                for status in statuses:
                    count = int(counts.get(status, 0))
                    row[f"{status} count"] = count
                    row[f"{status} %"] = count / total if total else 0
                rows.append(row)

    return pd.DataFrame(rows)


def question_max_score(qid, max_scores=None):
    """Max achievable for a question: user/known value for count questions, else 1 (a 0/1 item)."""
    if max_scores and qid in max_scores:
        try:
            return float(max_scores[qid])
        except Exception:
            pass
    if qid in COUNT_QUESTION_DEFAULT_MAX:
        return float(COUNT_QUESTION_DEFAULT_MAX[qid])
    return 1.0


def detect_count_questions(df, question_cols):
    """Return {qid: observed_max} for baseline question columns whose values exceed 1."""
    found = {}
    for q in question_cols:
        if q not in df.columns:
            continue
        vals = pd.to_numeric(df[q], errors="coerce")
        vals = vals[vals.notna() & (vals != 999)]
        if len(vals) and float(vals.max()) > 1:
            found[q] = int(vals.max())
    return found


def analysis_by_question(clean_df, max_scores=None):
    """Per-question: mean pre/post score and pre/post % (= score / max), plus the change."""
    rows = []
    for base_col in BASELINE_QUESTION_COLS:
        post_col = f"{base_col}_post"
        if base_col not in clean_df.columns or post_col not in clean_df.columns:
            continue
        mx = question_max_score(base_col, max_scores)
        pre = pd.to_numeric(clean_df[base_col], errors="coerce")
        post = pd.to_numeric(clean_df[post_col], errors="coerce")
        pre_score = float(pre.mean()) if len(pre) else 0.0
        post_score = float(post.mean()) if len(post) else 0.0
        pre_pct = (pre_score / mx * 100) if mx else 0.0
        post_pct = (post_score / mx * 100) if mx else 0.0
        rows.append({
            "Question": question_excel_name(base_col, "both"),
            "Question ID": base_col,
            "Max score": mx,
            "Pre score": round(pre_score, 3),
            "Post score": round(post_score, 3),
            "Pre %": round(pre_pct, 1),
            "Post %": round(post_pct, 1),
            "Post - Pre %": round(post_pct - pre_pct, 1),
        })
    return pd.DataFrame(rows)


def analysis_by_item(clean_df, item_mapping=None, max_scores=None):
    """Per-item: item score = mean over children of (sum of its question values);
    item max = sum of its question maxima; item % = score / max."""
    if item_mapping is None:
        item_mapping = ITEM_MAPPING
    ordered = [f"ITEM_{i}" for i in range(1, 22)]
    rows = []
    for item_id in ordered:
        qs = [q for q, it in item_mapping.items()
              if it == item_id and q in clean_df.columns and f"{q}_post" in clean_df.columns]
        if not qs:
            continue
        item_max = sum(question_max_score(q, max_scores) for q in qs)
        pre_sum = pd.Series(0.0, index=clean_df.index)
        post_sum = pd.Series(0.0, index=clean_df.index)
        for q in qs:
            pre_sum = pre_sum + pd.to_numeric(clean_df[q], errors="coerce").fillna(0)
            post_sum = post_sum + pd.to_numeric(clean_df[f"{q}_post"], errors="coerce").fillna(0)
        pre_score = float(pre_sum.mean()) if len(pre_sum) else 0.0
        post_score = float(post_sum.mean()) if len(post_sum) else 0.0
        pre_pct = (pre_score / item_max * 100) if item_max else 0.0
        post_pct = (post_score / item_max * 100) if item_max else 0.0
        rows.append({
            "Item": f"{item_id} - {ITEM_NAMES.get(item_id, item_id)}",
            "Item ID": item_id,
            "Questions": len(qs),
            "Max score": item_max,
            "Pre score": round(pre_score, 3),
            "Post score": round(post_score, 3),
            "Pre %": round(pre_pct, 1),
            "Post %": round(post_pct, 1),
            "Post - Pre %": round(post_pct - pre_pct, 1),
        })
    return pd.DataFrame(rows)


def analysis_by_domain(question_analysis_df, item_mapping=None, domain_mapping=None):
    """Per-domain: average of the pre/post % of the questions that belong to the domain.
    IDELA score = average of the four domain %s."""
    if item_mapping is None:
        item_mapping = ITEM_MAPPING
    if domain_mapping is None:
        domain_mapping = DOMAIN_MAPPING
    item_to_domain = {}
    for d, items in domain_mapping.items():
        for it in items:
            item_to_domain[it] = d
    q_to_domain = {}
    for q, it in item_mapping.items():
        d = item_to_domain.get(it)
        if d:
            q_to_domain[q] = d
    qa = question_analysis_df.set_index("Question ID") if len(question_analysis_df) else question_analysis_df
    rows = []
    pre_vals, post_vals = [], []
    for d in domain_mapping.keys():
        qids = [q for q, dd in q_to_domain.items() if dd == d and len(qa) and q in qa.index]
        if qids:
            pre_pct = float(qa.loc[qids, "Pre %"].mean())
            post_pct = float(qa.loc[qids, "Post %"].mean())
        else:
            pre_pct = post_pct = 0.0
        pre_vals.append(pre_pct)
        post_vals.append(post_pct)
        rows.append({
            "Domain": d,
            "Questions": len(qids),
            "Pre %": round(pre_pct, 1),
            "Post %": round(post_pct, 1),
            "Post - Pre %": round(post_pct - pre_pct, 1),
        })
    idela_pre = sum(pre_vals) / len(pre_vals) if pre_vals else 0.0
    idela_post = sum(post_vals) / len(post_vals) if post_vals else 0.0
    rows.append({
        "Domain": "IDELA SCORE (average of domains)",
        "Questions": "",
        "Pre %": round(idela_pre, 1),
        "Post %": round(idela_post, 1),
        "Post - Pre %": round(idela_post - idela_pre, 1),
    })
    return pd.DataFrame(rows)


def build_cleaned_data_sheet(clean_df, max_scores=None):
    """Essential info + question values (pre/post) + a per-child IDELA % score."""
    meta = [c for c in META_COLUMNS if c in clean_df.columns and c != "IDELA_date"]
    out = clean_df[meta].copy()
    q_used = [q for q in BASELINE_QUESTION_COLS
              if q in clean_df.columns and f"{q}_post" in clean_df.columns]
    total_max = sum(question_max_score(q, max_scores) for q in q_used)
    pre_ach = pd.Series(0.0, index=clean_df.index)
    post_ach = pd.Series(0.0, index=clean_df.index)
    for q in q_used:
        pre = pd.to_numeric(clean_df[q], errors="coerce").fillna(0)
        post = pd.to_numeric(clean_df[f"{q}_post"], errors="coerce").fillna(0)
        pre_ach = pre_ach + pre
        post_ach = post_ach + post
        name = question_excel_name(q, "english")
        out[f"{name} (pre)"] = pre
        out[f"{name} (post)"] = post
    out["IDELA pre %"] = (pre_ach / total_max * 100).round(1) if total_max else 0.0
    out["IDELA post %"] = (post_ach / total_max * 100).round(1) if total_max else 0.0
    out["IDELA change %"] = (out["IDELA post %"] - out["IDELA pre %"]).round(1)
    return out


def create_question_dashboard(by_question_df: pd.DataFrame) -> pd.DataFrame:
    question_status_cols = {}
    suffix = " - comparison status"
    for col in by_question_df.columns:
        if col.endswith(suffix):
            question_name = col[:-len(suffix)]
            question_status_cols[question_name] = col
    return create_status_dashboard(by_question_df, question_status_cols, "Question analysis")


def create_item_dashboard(by_item_df: pd.DataFrame) -> pd.DataFrame:
    item_status_cols = {}
    for item_id in [f"ITEM_{i}" for i in range(1, 22)]:
        item_name = ITEM_NAMES.get(item_id, item_id)
        status_col = f"{item_id} {item_name} comparison status"
        if status_col in by_item_df.columns:
            item_status_cols[f"{item_id} - {item_name}"] = status_col
    return create_status_dashboard(by_item_df, item_status_cols, "Item analysis")


def create_domain_dashboard(by_domain_df: pd.DataFrame) -> pd.DataFrame:
    domain_status_cols = {}
    for domain_name in DOMAIN_MAPPING.keys():
        status_col = f"{domain_name} comparison status"
        if status_col in by_domain_df.columns:
            domain_status_cols[domain_name] = status_col
    return create_status_dashboard(by_domain_df, domain_status_cols, "Domain analysis")


def create_idela_dashboard(by_item_df: pd.DataFrame) -> pd.DataFrame:
    return create_status_dashboard(by_item_df, {"IDELA score": "idela score status"}, "IDELA score analysis")


def write_standard_sheet(writer, workbook, sheet_name: str, data: pd.DataFrame):
    safe_name = sheet_name[:31]
    data.to_excel(writer, sheet_name=safe_name, index=False)
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


def write_filterable_dashboard(writer, workbook, sheet_name: str, source_df: pd.DataFrame, dashboard_title: str):
    """Create a dashboard sheet that works like a Pivot Chart using Excel filters.

    NOTE: Python libraries used in Streamlit cannot reliably create native Excel
    PivotTables/PivotCharts. This design avoids formulas and #N/A problems by
    writing a clean summary table and linking the chart directly to that table.
    Users interact by filtering the table headers: Essential info column and Analysis.
    Excel charts automatically ignore filtered/hidden rows, so the chart updates.
    """
    safe_name = sheet_name[:31]
    df = source_df.copy()

    # Keep only dashboard rows with real category values.
    if "Essential info column" in df.columns:
        df = df[df["Essential info column"].astype(str).ne("Overall")].copy()

    # Rename to clean pivot-style names.
    rename_map = {
        "Essential info column": "Filter: Essential info column",
        "Essential info value": "Category",
        "Analysis": "Filter: Analysis",
        "Total counted": "Total counted",
        "Improved %": "Improved",
        "No change %": "No change",
        "Decreased %": "Decreased",
        "Improved count": "Improved count",
        "No change count": "No change count",
        "Decreased count": "Decreased count",
    }
    keep_cols = [c for c in rename_map if c in df.columns]
    df = df[keep_cols].rename(columns=rename_map)

    # Put important fields first and percentages last for charting.
    ordered_cols = [
        "Filter: Essential info column",
        "Filter: Analysis",
        "Category",
        "Total counted",
        "Improved count",
        "No change count",
        "Decreased count",
        "Improved",
        "No change",
        "Decreased",
    ]
    df = df[[c for c in ordered_cols if c in df.columns]]

    # Default filter selection: prefer gender if available, otherwise first essential column.
    default_essential = None
    if "Filter: Essential info column" in df.columns and len(df):
        vals = df["Filter: Essential info column"].dropna().astype(str).unique().tolist()
        default_essential = "e_childs_sex" if "e_childs_sex" in vals else vals[0]
        df = pd.concat([
            df[df["Filter: Essential info column"].astype(str).eq(default_essential)],
            df[~df["Filter: Essential info column"].astype(str).eq(default_essential)],
        ], ignore_index=True)

    df.to_excel(writer, sheet_name=safe_name, startrow=4, index=False)
    ws = writer.sheets[safe_name]

    title_fmt = workbook.add_format({"bold": True, "font_size": 20, "font_color": "#1F4E78"})
    note_fmt = workbook.add_format({"font_color": "#666666", "italic": True})
    header_fmt = workbook.add_format({"bold": True, "bg_color": "#D9EAD3", "border": 1})
    pct_fmt = workbook.add_format({"num_format": "0.0%", "border": 1})
    count_fmt = workbook.add_format({"num_format": "#,##0", "border": 1})

    ws.write("A1", dashboard_title, title_fmt)
    ws.write("A2", "Use the table filters below, like a pivot chart: filter Essential info column and Analysis. The chart updates with visible rows only.", note_fmt)
    ws.write("A3", "Tip: choose one Essential info column and one Analysis from the filter arrows.", note_fmt)

    # Format header and columns.
    for c_idx, col_name in enumerate(df.columns):
        ws.write(4, c_idx, col_name, header_fmt)
        width = min(max(len(str(col_name)) + 4, 14), 44)
        ws.set_column(c_idx, c_idx, width)
        if col_name in ["Improved", "No change", "Decreased"]:
            ws.set_column(c_idx, c_idx, 14, pct_fmt)
        elif "count" in col_name.lower() or col_name == "Total counted":
            ws.set_column(c_idx, c_idx, 14, count_fmt)

    nrows = max(len(df), 1)
    ncols = max(len(df.columns), 1)
    ws.autofilter(4, 0, 4 + nrows, ncols - 1)
    ws.freeze_panes(5, 0)

    # Apply default filters for first view, if we can.
    if default_essential and "Filter: Essential info column" in df.columns:
        ws.filter_column(0, f'x == "{default_essential}"')
    if "Filter: Analysis" in df.columns and len(df):
        default_analysis = df["Filter: Analysis"].dropna().astype(str).iloc[0]
        ws.filter_column(1, f'x == "{default_analysis}"')

    # Hide rows that do not match the default view, so the first chart view is clean.
    if len(df) and default_essential and "Filter: Essential info column" in df.columns and "Filter: Analysis" in df.columns:
        default_analysis = df["Filter: Analysis"].dropna().astype(str).iloc[0]
        for r_idx, row in df.iterrows():
            visible = (
                str(row.get("Filter: Essential info column", "")) == str(default_essential)
                and str(row.get("Filter: Analysis", "")) == str(default_analysis)
            )
            if not visible:
                ws.set_row(5 + r_idx, options={"hidden": True})

    # Add chart directly from the table range. It will respond to Excel filters.
    col_index = {name: i for i, name in enumerate(df.columns)}
    if all(k in col_index for k in ["Category", "Improved", "No change", "Decreased"]):
        first_row = 5  # zero-based Excel row index where first data row starts in xlsxwriter notation
        last_row = 4 + max(len(df), 1)
        chart = workbook.add_chart({"type": "column"})
        chart.add_series({
            "name": "Improved",
            "categories": [safe_name, first_row, col_index["Category"], last_row, col_index["Category"]],
            "values": [safe_name, first_row, col_index["Improved"], last_row, col_index["Improved"]],
            "data_labels": {"value": True, "num_format": "0%"},
        })
        chart.add_series({
            "name": "No change",
            "categories": [safe_name, first_row, col_index["Category"], last_row, col_index["Category"]],
            "values": [safe_name, first_row, col_index["No change"], last_row, col_index["No change"]],
            "data_labels": {"value": True, "num_format": "0%"},
        })
        chart.add_series({
            "name": "Decreased",
            "categories": [safe_name, first_row, col_index["Category"], last_row, col_index["Category"]],
            "values": [safe_name, first_row, col_index["Decreased"], last_row, col_index["Decreased"]],
            "data_labels": {"value": True, "num_format": "0%"},
        })
        chart.set_title({"name": "Comparison status by selected category"})
        chart.set_y_axis({"num_format": "0%", "min": 0, "max": 1, "major_unit": 0.2})
        chart.set_x_axis({"name": "Category"})
        chart.set_legend({"position": "bottom"})
        chart.set_size({"width": 980, "height": 460})
        # Do not show data in hidden rows/columns. This is the key pivot-like behavior.
        chart.show_hidden_data = False
        ws.insert_chart("L5", chart)

    # Also add a small instruction block above chart.
    ws.set_column("L:L", 4)
    ws.set_column("M:U", 14)


def _rowlevel_meta(clean_df):
    prefer = ["caseid", "d_childs_full_name", "e_childs_sex", "f_childs_age",
              "teacher_location", "governorate", "nationality", "district"]
    cols = [c for c in prefer if c in clean_df.columns]
    return cols if cols else [clean_df.columns[0]]


def _rowlevel_assemble(clean_df, vdf, meta):
    """Prepend AVERAGE / MALE AVERAGE / FEMALE AVERAGE / MINIMUM / MAXIMUM rows above per-child rows.
    Returns (dataframe, number_of_stat_rows)."""
    label_col = meta[0]
    value_cols = list(vdf.columns)
    header = meta + value_cols
    sex = clean_df["e_childs_sex"].astype("string").str.lower() if "e_childs_sex" in clean_df.columns else None

    def stat_row(label, sub):
        row = {c: "" for c in meta}
        row[label_col] = label
        for c in value_cols:
            col = pd.to_numeric(sub[c], errors="coerce")
            if not col.notna().any():
                row[c] = ""
            elif label == "MINIMUM":
                row[c] = round(float(col.min()), 2)
            elif label == "MAXIMUM":
                row[c] = round(float(col.max()), 2)
            else:
                row[c] = round(float(col.mean()), 2)
        return row

    stats = [stat_row("AVERAGE", vdf)]
    if sex is not None:
        male = vdf[sex.str.startswith("m", na=False)]
        female = vdf[sex.str.startswith("f", na=False)]
        if len(male):
            stats.append(stat_row("MALE AVERAGE", male))
        if len(female):
            stats.append(stat_row("FEMALE AVERAGE", female))
    stats.append(stat_row("MINIMUM", vdf))
    stats.append(stat_row("MAXIMUM", vdf))

    body = clean_df[meta].copy().reset_index(drop=True)
    vreset = vdf.reset_index(drop=True)
    for c in value_cols:
        body[c] = vreset[c]
    top = pd.DataFrame(stats, columns=header)
    out = pd.concat([top, body[header]], ignore_index=True)
    return out, len(stats)


def rowlevel_questions(clean_df, max_scores=None):
    meta = _rowlevel_meta(clean_df)
    q_used = [q for q in BASELINE_QUESTION_COLS if q in clean_df.columns and f"{q}_post" in clean_df.columns]
    vdf = pd.DataFrame(index=clean_df.index)
    for q in q_used:
        vdf[f"{q} - pre"] = pd.to_numeric(clean_df[q], errors="coerce")
        vdf[f"{q} - post"] = pd.to_numeric(clean_df[f"{q}_post"], errors="coerce")
    return _rowlevel_assemble(clean_df, vdf, meta)


def rowlevel_items(clean_df, item_mapping=None, max_scores=None):
    if item_mapping is None:
        item_mapping = ITEM_MAPPING
    meta = _rowlevel_meta(clean_df)
    vdf = pd.DataFrame(index=clean_df.index)
    for item_id in [f"ITEM_{i}" for i in range(1, 22)]:
        qs = [q for q, it in item_mapping.items()
              if it == item_id and q in clean_df.columns and f"{q}_post" in clean_df.columns]
        if not qs:
            continue
        item_max = sum(question_max_score(q, max_scores) for q in qs)
        pre = pd.Series(0.0, index=clean_df.index)
        post = pd.Series(0.0, index=clean_df.index)
        for q in qs:
            pre = pre + pd.to_numeric(clean_df[q], errors="coerce").fillna(0)
            post = post + pd.to_numeric(clean_df[f"{q}_post"], errors="coerce").fillna(0)
        nm = f"{item_id} {ITEM_NAMES.get(item_id, item_id)}"
        vdf[f"{nm} - pre %"] = (pre / item_max * 100).round(1) if item_max else 0.0
        vdf[f"{nm} - post %"] = (post / item_max * 100).round(1) if item_max else 0.0
    return _rowlevel_assemble(clean_df, vdf, meta)


def rowlevel_domains(clean_df, item_mapping=None, domain_mapping=None, max_scores=None):
    if item_mapping is None:
        item_mapping = ITEM_MAPPING
    if domain_mapping is None:
        domain_mapping = DOMAIN_MAPPING
    meta = _rowlevel_meta(clean_df)
    item_to_domain = {}
    for d, items in domain_mapping.items():
        for it in items:
            item_to_domain[it] = d
    pre_lists = {d: [] for d in domain_mapping}
    post_lists = {d: [] for d in domain_mapping}
    for q, it in item_mapping.items():
        d = item_to_domain.get(it)
        if d is None or q not in clean_df.columns or f"{q}_post" not in clean_df.columns:
            continue
        mx = question_max_score(q, max_scores)
        pre_lists[d].append(pd.to_numeric(clean_df[q], errors="coerce").fillna(0) / mx * 100)
        post_lists[d].append(pd.to_numeric(clean_df[f"{q}_post"], errors="coerce").fillna(0) / mx * 100)
    vdf = pd.DataFrame(index=clean_df.index)
    dom_pre, dom_post = {}, {}
    for d in domain_mapping:
        if pre_lists[d]:
            pre = sum(pre_lists[d]) / len(pre_lists[d])
            post = sum(post_lists[d]) / len(post_lists[d])
        else:
            pre = pd.Series(0.0, index=clean_df.index)
            post = pd.Series(0.0, index=clean_df.index)
        dom_pre[d] = pre
        dom_post[d] = post
        vdf[f"{d} - pre %"] = pre.round(1)
        vdf[f"{d} - post %"] = post.round(1)
    if dom_pre:
        idpre = sum(dom_pre.values()) / len(dom_pre)
        idpost = sum(dom_post.values()) / len(dom_post)
        vdf["IDELA - pre %"] = idpre.round(1)
        vdf["IDELA - post %"] = idpost.round(1)
        vdf["IDELA - change %"] = (idpost - idpre).round(1)
    return _rowlevel_assemble(clean_df, vdf, meta)


def write_new_workbook(raw_df, cleaned_df, q_df, i_df, d_df, rq=None, ri=None, rd=None) -> bytes:
    """Cohort sheets (Question/Item/Domain) plus per-child row-level sheets with AVERAGE/MIN/MAX rows."""
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        wb = writer.book
        header_fmt = wb.add_format({"bold": True, "bg_color": "#2F3B52", "font_color": "#FFFFFF",
                                    "border": 1, "align": "center", "valign": "vcenter", "text_wrap": True})
        cache = {}

        def cell_fmt(bg, kind, bold=False):
            key = (bg, kind, bold)
            if key not in cache:
                d = {"border": 1, "valign": "vcenter"}
                if bg:
                    d["bg_color"] = bg
                if bold:
                    d["bold"] = True
                if kind == "pct":
                    d["num_format"] = '0.0"%"'
                elif kind == "num":
                    d["num_format"] = "0.###"
                cache[key] = wb.add_format(d)
            return cache[key]

        def kind_of(col):
            c = str(col)
            if "%" in c:
                return "pct"
            if col in ("Pre score", "Post score", "Max score"):
                return "num"
            return "text"

        def dump_plain(name, df):
            df = df.copy()
            df.to_excel(writer, sheet_name=name[:31], index=False)
            ws = writer.sheets[name[:31]]
            for j, c in enumerate(df.columns):
                ws.write(0, j, c, header_fmt)
            ws.freeze_panes(1, 0)

        def dump_colored(name, df, row_styles, first_col_width=42):
            ws = wb.add_worksheet(name[:31])
            writer.sheets[name[:31]] = ws
            cols = list(df.columns)
            for j, c in enumerate(cols):
                ws.write(0, j, c, header_fmt)
            for i in range(len(df)):
                bg, bold = row_styles[i] if row_styles else (None, False)
                for j, c in enumerate(cols):
                    v = df.iloc[i][c]
                    k = kind_of(c)
                    if k in ("pct", "num"):
                        try:
                            val = float(v)
                        except Exception:
                            val = 0.0
                    else:
                        val = "" if pd.isna(v) else str(v)
                    ws.write(i + 1, j, val, cell_fmt(bg, k, bold))
            ws.set_column(0, 0, first_col_width)
            if len(cols) > 1:
                ws.set_column(1, len(cols) - 1, 13)
            ws.freeze_panes(1, 0)

        def dump_rowlevel(name, df, n_stat, first_col_width=26):
            ws = wb.add_worksheet(name[:31])
            writer.sheets[name[:31]] = ws
            cols = list(df.columns)
            for j, c in enumerate(cols):
                ws.write(0, j, c, header_fmt)
            stat_bg = RESTFUL_COLORS["warm_sand"]["light"]
            for i in range(len(df)):
                is_stat = i < n_stat
                bg = stat_bg if is_stat else None
                for j, c in enumerate(cols):
                    v = df.iloc[i][c]
                    if v == "" or (not isinstance(v, str) and pd.isna(v)):
                        ws.write(i + 1, j, "", cell_fmt(bg, "text", is_stat))
                        continue
                    try:
                        val = float(v)
                        k = "pct" if "%" in str(c) else "num"
                        ws.write(i + 1, j, val, cell_fmt(bg, k, is_stat))
                    except (ValueError, TypeError):
                        ws.write(i + 1, j, str(v), cell_fmt(bg, "text", is_stat))
            ws.set_column(0, 0, first_col_width)
            if len(cols) > 1:
                ws.set_column(1, len(cols) - 1, 13)
            ws.freeze_panes(n_stat + 1, 1)

        dump_plain("raw data", raw_df)
        dump_plain("Cleaned data", cleaned_df)

        zebra = [RESTFUL_COLORS["slate_blue"]["light"], RESTFUL_COLORS["sage_green"]["light"]]
        dump_colored("Question Analysis", q_df, [(zebra[i % 2], False) for i in range(len(q_df))])
        dump_colored("Item Analysis", i_df, [(zebra[i % 2], False) for i in range(len(i_df))])

        med = [RESTFUL_COLORS[n]["medium"] for n in RESTFUL_ORDER]
        dstyles, di = [], 0
        for _, r in d_df.iterrows():
            if str(r["Domain"]).startswith("IDELA"):
                dstyles.append((RESTFUL_COLORS["warm_sand"]["medium"], True))
            else:
                dstyles.append((med[di % 4], False)); di += 1
        dump_colored("Domain Analysis", d_df, dstyles, first_col_width=36)

        if rq is not None:
            dump_rowlevel("Questions (per child)", rq[0], rq[1])
        if ri is not None:
            dump_rowlevel("Items (per child)", ri[0], ri[1], first_col_width=26)
        if rd is not None:
            dump_rowlevel("Domains (per child)", rd[0], rd[1], first_col_width=26)
    return out.getvalue()


def to_excel_bytes(sheets: Dict[str, pd.DataFrame]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book
        workbook.set_calc_mode("auto")
        dashboard_sources = {}
        for sheet_name, data in sheets.items():
            if sheet_name in ["QUESTION DASHBOARD", "ITEM DASHBOARD", "DOMAIN DASHBOARD", "IDELA DASHBOARD"]:
                dashboard_sources[sheet_name] = data
            else:
                write_standard_sheet(writer, workbook, sheet_name, data)

        for sheet_name, data in dashboard_sources.items():
            title = sheet_name.replace(" DASHBOARD", " Dashboard").title()
            write_filterable_dashboard(writer, workbook, sheet_name, data, title)

    return output.getvalue()

def go_next():
    st.session_state.step += 1
    st.rerun()


def go_back():
    st.session_state.step -= 1
    st.rerun()


def show_progress():
    labels = ["1. Upload", "2. Map Columns", "3. Pair Pre/Post", "4. Score Text", "5. Questions→Items", "6. Max Scores", "7. Items→Domains", "8. Review Rows", "9. Question Actions", "10. Download"]
    current = st.session_state.step
    st.progress((current - 1) / (len(labels) - 1))
    st.write(" → ".join([f"**{x}**" if i + 1 == current else x for i, x in enumerate(labels)]))


def mapping_scope(key: str) -> str:
    """Keep dropdown de-duplication within the same uploaded source only."""
    if key == "base_id" or key.startswith("base_"):
        return "baseline_file"
    if key == "end_id" or key.startswith("end_"):
        return "endline_file"
    return "current_file"


def selectbox_mapping(label: str, req_col: str, uploaded_cols: List[str], key: str, mapping: Dict[str, str], endline_hint: bool = False):
    # Make mapping easier: once an uploaded column is selected elsewhere in the same file/source,
    # remove it from the current dropdown. Keep the current selection visible so users can change it.
    current_scope = mapping_scope(key)
    current_value = mapping.get(key, suggest_column(req_col, uploaded_cols, endline_hint=endline_hint))
    selected_elsewhere = {
        v for k, v in mapping.items()
        if k != key and mapping_scope(k) == current_scope and v and v in uploaded_cols
    }
    available_cols = [c for c in uploaded_cols if c not in selected_elsewhere or c == current_value]
    options = [""] + available_cols
    if current_value not in options:
        current_value = ""
    index = options.index(current_value) if current_value in options else 0
    mapping[key] = st.selectbox(label, options=options, index=index, key=f"map_{key}")


def standard_output_columns() -> List[str]:
    return META_COLUMNS + BASELINE_QUESTION_COLS + ENDLINE_QUESTION_COLS


def keep_standard_columns(df: pd.DataFrame) -> pd.DataFrame:
    keep_cols = [c for c in standard_output_columns() if c in df.columns]
    return df[keep_cols].copy()



def validate_paired_rows(mapped_df: pd.DataFrame, expected_min_rows: int = 10):
    """Return (ok, message). Prevent wrong missing percentages caused by merging on the wrong ID column."""
    row_count = len(mapped_df) if mapped_df is not None else 0
    if row_count == 0:
        return False, "No paired baseline/endline rows were created. Please check the unique child/beneficiary ID mapping."
    if row_count < expected_min_rows:
        return False, (
            f"Only {row_count} paired baseline/endline rows were created. This is usually because the wrong ID column was selected. "
            "For duplicated baseline/endline files, do NOT use row number. Use the real child/case ID, usually `form.case.@case_id`."
        )
    return True, ""


def duplicated_pairing_summary(raw_df: pd.DataFrame, id_col: str, round_col: str, baseline_value, endline_value):
    data = raw_df.copy()
    rt = data[round_col].astype('string').str.strip().str.lower()
    base_val = str(baseline_value).strip().lower()
    end_val = str(endline_value).strip().lower()
    base_ids = set(data.loc[rt.eq(base_val), id_col].dropna().astype(str).str.strip())
    end_ids = set(data.loc[rt.eq(end_val), id_col].dropna().astype(str).str.strip())
    paired = base_ids & end_ids
    return len(base_ids), len(end_ids), len(paired)


def get_id_set(df: pd.DataFrame, id_col: str) -> set:
    if not id_col or id_col not in df.columns:
        return set()
    return set(df[id_col].dropna().astype(str).str.strip().replace('', pd.NA).dropna())


def show_analysis_count_summary(total_children: int, counted_children: int, reasons: Dict[str, int], details: Dict[str, list] = None):
    not_counted = max(total_children - counted_children, 0)
    st.info(f"Out of **{total_children}** child(ren), **{counted_children}** will be counted in this analysis and **{not_counted}** will not be counted.")
    if reasons:
        reason_df = pd.DataFrame([{"Reason": k, "Children": v} for k, v in reasons.items() if v > 0])
        if not reason_df.empty:
            st.dataframe(reason_df, hide_index=True, use_container_width=True)
    if details:
        with st.expander("Show not-counted child IDs"):
            for reason, ids in details.items():
                if ids:
                    st.write(f"**{reason}** ({len(ids)})")
                    st.dataframe(pd.DataFrame({"caseid": ids}), hide_index=True, use_container_width=True)


def show_same_row_count_summary(raw_df: pd.DataFrame, id_col: str):
    if not id_col or id_col not in raw_df.columns:
        return
    total_rows = len(raw_df)
    valid_id_rows = int(raw_df[id_col].notna().sum())
    missing_id_rows = total_rows - valid_id_rows
    total_children = raw_df[id_col].dropna().astype(str).str.strip().nunique()
    reasons = {}
    if missing_id_rows > 0:
        reasons["rows with missing child ID"] = missing_id_rows
    show_analysis_count_summary(total_children=total_children, counted_children=total_children, reasons=reasons)


def show_two_file_count_summary(base_df: pd.DataFrame, end_df: pd.DataFrame, base_id_col: str, end_id_col: str):
    if not base_id_col or not end_id_col or base_id_col not in base_df.columns or end_id_col not in end_df.columns:
        return
    base_ids = get_id_set(base_df, base_id_col)
    end_ids = get_id_set(end_df, end_id_col)
    paired = base_ids & end_ids
    only_base = sorted(base_ids - end_ids)
    only_end = sorted(end_ids - base_ids)
    total_children = len(base_ids | end_ids)
    reasons = {
        "only baseline with no endline": len(only_base),
        "only endline with no baseline": len(only_end),
    }
    details = {
        "only baseline with no endline": only_base,
        "only endline with no baseline": only_end,
    }
    show_analysis_count_summary(total_children, len(paired), reasons, details)


def show_duplicated_rows_count_summary(raw_df: pd.DataFrame, id_col: str, round_col: str, baseline_value, endline_value):
    if not id_col or not round_col or not baseline_value or not endline_value:
        return
    if id_col not in raw_df.columns or round_col not in raw_df.columns:
        return
    data = raw_df.copy()
    rt = data[round_col].astype('string').str.strip().str.lower()
    base_val = str(baseline_value).strip().lower()
    end_val = str(endline_value).strip().lower()
    base_ids = set(data.loc[rt.eq(base_val), id_col].dropna().astype(str).str.strip())
    end_ids = set(data.loc[rt.eq(end_val), id_col].dropna().astype(str).str.strip())
    paired = base_ids & end_ids
    only_base = sorted(base_ids - end_ids)
    only_end = sorted(end_ids - base_ids)
    all_known_round_ids = base_ids | end_ids
    all_ids = get_id_set(raw_df, id_col)
    other_round_ids = sorted(all_ids - all_known_round_ids)
    total_children = len(all_ids)
    reasons = {
        "only baseline with no endline": len(only_base),
        "only endline with no baseline": len(only_end),
        "not baseline/endline round value": len(other_round_ids),
    }
    details = {
        "only baseline with no endline": only_base,
        "only endline with no baseline": only_end,
        "not baseline/endline round value": other_round_ids,
    }
    show_analysis_count_summary(total_children, len(paired), reasons, details)


def idela_date_exists_mask(df: pd.DataFrame, date_col: str) -> pd.Series:
    """Return True for rows where the selected IDELA date field has a usable value."""
    if not date_col or date_col not in df.columns:
        return pd.Series([False] * len(df), index=df.index)

    as_text = df[date_col].astype("string").str.strip().str.lower()
    return (
        df[date_col].notna()
        & ~as_text.isin(["", "---", "nan", "none", "null", "<na>"])
    )


def filter_rows_with_idela_date(df: pd.DataFrame, date_col: str):
    """Filter rows where IDELA date exists and return filtered data plus a summary."""
    mask = idela_date_exists_mask(df, date_col)
    filtered = df.loc[mask].copy()
    summary = {
        "original_rows": int(len(df)),
        "kept_rows": int(mask.sum()),
        "removed_rows": int((~mask).sum()),
        "date_column": date_col,
    }
    return filtered, summary


def show_idela_date_filter_summary(summary: Dict[str, int]):
    if not summary:
        return
    st.success(
        f"IDELA date filter applied using `{summary.get('date_column')}`: "
        f"kept **{summary.get('kept_rows', 0)}** row(s), "
        f"removed **{summary.get('removed_rows', 0)}** row(s) without IDELA date."
    )

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

# STEP 1: Upload structure, files, and IDELA date filter
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

    mapping = dict(st.session_state.column_mapping) if st.session_state.column_mapping else {}

    if upload_type.startswith("One file: baseline and endline are in the same row"):
        uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xlsm", "xls"], key="same_file")
        if uploaded_file:
            xl = pd.ExcelFile(uploaded_file)
            sheet_name = st.selectbox("Select raw data sheet", xl.sheet_names, key="same_sheet")
            original_raw_df = read_excel_file(uploaded_file, sheet_name)
            uploaded_cols = list(original_raw_df.columns)

            st.success(f"Loaded {len(original_raw_df)} rows and {len(original_raw_df.columns)} columns.")
            st.session_state.raw_df = original_raw_df.copy()
            st.session_state.download_raw_df = original_raw_df.copy()
            st.session_state.column_mapping = mapping
            st.dataframe(original_raw_df.head(10), use_container_width=True)
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
                original_base_df = read_excel_file(base_file, base_sheet)
                st.write("Baseline preview")
                st.dataframe(original_base_df.head(5), use_container_width=True)
            with c2:
                end_sheet = st.selectbox("Endline sheet", end_xl.sheet_names, key="end_sheet")
                end_df = read_excel_file(end_file, end_sheet)
                st.write("Endline preview")
                st.dataframe(end_df.head(5), use_container_width=True)

            st.session_state.base_df = original_base_df.copy()
            st.session_state.end_df = end_df
            base_raw = original_base_df.copy(); base_raw.insert(0, "__source_file__", "baseline")
            end_raw = end_df.copy(); end_raw.insert(0, "__source_file__", "endline")
            st.session_state.download_raw_df = pd.concat([base_raw, end_raw], ignore_index=True, sort=False)
            st.session_state.column_mapping = mapping
            if st.button("Next: Map columns", type="primary"):
                go_next()

    else:
        uploaded_file = st.file_uploader("Upload Excel file with baseline/endline duplicated rows", type=["xlsx", "xlsm", "xls"], key="dup_file")
        if uploaded_file:
            xl = pd.ExcelFile(uploaded_file)
            sheet_name = st.selectbox("Select raw data sheet", xl.sheet_names, key="dup_sheet")
            original_raw_df = read_excel_file(uploaded_file, sheet_name)
            uploaded_cols = list(original_raw_df.columns)

            st.success(f"Loaded {len(original_raw_df)} rows and {len(original_raw_df.columns)} columns.")
            st.session_state.raw_df = original_raw_df.copy()
            st.session_state.download_raw_df = original_raw_df.copy()
            st.session_state.column_mapping = mapping
            st.dataframe(original_raw_df.head(10), use_container_width=True)
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
        tab_meta, tab_q = st.tabs(["Essential info columns", "Required question columns"])
        with tab_meta:
            st.warning("Map these essential info columns. Any other uploaded columns will be discarded.")
            for col in [c for c in META_COLUMNS if c != "IDELA_date"]:
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

        required_keys = META_COLUMNS + BASELINE_QUESTION_COLS + ENDLINE_QUESTION_COLS

        if st.button("Next: Pair pre/post", type="primary"):
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
            for col in [c for c in META_COLUMNS if c not in ["caseid", "IDELA_date"]]:
                selectbox_mapping(col, col, base_cols, f"base_{col}", mapping)
        with tab_base:
            for base_col in BASELINE_QUESTION_COLS:
                selectbox_mapping(question_mapping_label(base_col), base_col, base_cols, f"base_{base_col}", mapping)
        with tab_end:
            for base_col in BASELINE_QUESTION_COLS:
                selectbox_mapping(question_mapping_label(f"{base_col}_post"), base_col, end_cols, f"end_{base_col}", mapping, endline_hint=True)

        required_keys = ["base_id", "end_id"] + [f"base_{c}" for c in META_COLUMNS if c not in ["caseid", "IDELA_date"]] + [f"base_{c}" for c in BASELINE_QUESTION_COLS] + [f"end_{c}" for c in BASELINE_QUESTION_COLS]
        if st.button("Next: Pair pre/post", type="primary"):
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
                mapped = build_two_file_df(base_df, end_df, mapping)
                expected_min = max(10, int(min(base_df[mapping["base_id"]].nunique(), end_df[mapping["end_id"]].nunique()) * 0.50))
                ok, msg = validate_paired_rows(mapped, expected_min_rows=expected_min)
                if not ok:
                    st.error(msg)
                    st.info("Check that both files use the same child/beneficiary ID column.")
                else:
                    st.session_state.column_mapping = mapping
                    st.session_state.mapped_df = mapped
                    st.session_state.selected_delete_indices = set()
                    go_next()

    else:
        raw_df = st.session_state.raw_df
        uploaded_cols = list(raw_df.columns)
        st.write("Map the ID column, round column, then select which round value means baseline and endline.")
        tab_setup, tab_meta, tab_q = st.tabs(["ID and round", "Essential info columns", "Question columns"])
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
            for col in [c for c in META_COLUMNS if c not in ["caseid", "IDELA_date"]]:
                selectbox_mapping(col, col, uploaded_cols, f"meta_{col}", mapping)

        required_keys = ["dup_id", "round_col"] + [f"meta_{c}" for c in META_COLUMNS if c not in ["caseid", "IDELA_date"]] + [f"q_{c}" for c in BASELINE_QUESTION_COLS]
        if st.button("Next: Pair pre/post", type="primary"):
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
                base_n, end_n, paired_n = duplicated_pairing_summary(raw_df, mapping["dup_id"], mapping["round_col"], baseline_value, endline_value)
                expected_min = max(10, int(min(base_n, end_n) * 0.50))
                mapped = build_duplicated_rows_df(raw_df, mapping, baseline_value, endline_value)
                ok, msg = validate_paired_rows(mapped, expected_min_rows=expected_min)
                if not ok:
                    st.error(msg)
                    st.info(f"Baseline IDs: {base_n} | Endline IDs: {end_n} | Paired IDs: {paired_n}. Recommended ID column for your file: form.case.@case_id")
                else:
                    st.success(f"Paired baseline/endline rows created: {len(mapped)}")
                    st.session_state.column_mapping = mapping
                    st.session_state.mapped_df = mapped
                    st.session_state.selected_delete_indices = set()
                    go_next()

    st.session_state.column_mapping = mapping
    if st.button("Back"):
        go_back()

# STEP 3: Pair pre/post by case ID and drop unpaired children
elif st.session_state.step == 3:
    st.subheader("Step 3: Pair pre/post and drop unpaired children")
    st.write("A child is kept only if they have data on BOTH the pre (baseline) side and the post (endline) side.")

    source_df = st.session_state.mapped_df.copy() if st.session_state.mapped_df is not None else None
    if source_df is None or len(source_df) == 0:
        st.error("No mapped data found. Go back to Step 2 and map your columns.")
        st.stop()

    base_cols = [c for c in BASELINE_QUESTION_COLS if c in source_df.columns]
    end_cols = [c for c in ENDLINE_QUESTION_COLS if c in source_df.columns]

    # Treat blanks / --- / 999 as missing consistently before deciding if a side has data.
    check_df = normalize_score_values(source_df, base_cols + end_cols)

    def _side_has_data(cols):
        if not cols:
            return pd.Series([False] * len(check_df), index=check_df.index)
        present = pd.concat([~is_missing_question_value(check_df[c]) for c in cols], axis=1)
        return present.any(axis=1)

    has_pre = _side_has_data(base_cols)
    has_post = _side_has_data(end_cols)
    paired_mask = has_pre & has_post

    total = int(len(source_df))
    kept = int(paired_mask.sum())
    only_pre = int((has_pre & ~has_post).sum())
    only_post = int((~has_pre & has_post).sum())
    neither = int((~has_pre & ~has_post).sum())

    id_col = "caseid" if "caseid" in source_df.columns else None
    st.info(
        f"Out of **{total}** child record(s), **{kept}** have BOTH pre and post and will be kept. "
        f"**{total - kept}** will be dropped."
    )
    reason_rows = []
    if only_pre:
        reason_rows.append({"Reason": "Has pre only (no post)", "Children": only_pre})
    if only_post:
        reason_rows.append({"Reason": "Has post only (no pre)", "Children": only_post})
    if neither:
        reason_rows.append({"Reason": "No pre and no post data", "Children": neither})
    if reason_rows:
        st.dataframe(pd.DataFrame(reason_rows), hide_index=True, use_container_width=True)

    # Records that had data on exactly one side (a real assessment missing its pre or post).
    # Fully-empty records (no pre and no post) are dropped silently and only counted above.
    partial_mask = (has_pre != has_post)
    partial_df = source_df.loc[partial_mask].copy()
    if len(partial_df) > 0:
        with st.expander(f"Show {len(partial_df)} record(s) dropped for missing one side (pre or post)"):
            show_cols = [c for c in [id_col, "d_childs_full_name", "e_childs_sex", "f_childs_age", "teacher_location"] if c and c in partial_df.columns]
            disp = partial_df[show_cols].copy() if show_cols else partial_df.iloc[:, :4].copy()
            disp["has pre?"] = has_pre.loc[partial_df.index].map({True: "yes", False: "no"}).values
            disp["has post?"] = has_post.loc[partial_df.index].map({True: "yes", False: "no"}).values
            st.dataframe(disp, hide_index=True, use_container_width=True)
    elif (total - kept) > 0:
        st.caption("All dropped records simply had no data on either side; nothing to review individually.")

    paired_df = source_df.loc[paired_mask].copy()
    st.session_state.paired_df = paired_df
    st.session_state.pairing_summary = {
        "total": total, "kept": kept, "only_pre": only_pre,
        "only_post": only_post, "neither": neither,
    }

    if kept == 0:
        st.error("No child has both pre and post. Check your column mapping (case ID and the post/endline question columns).")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back"):
            go_back()
    with c2:
        if kept > 0 and st.button("Next: Score text values", type="primary"):
            # Re-scoring / re-review must start fresh from the newly paired set.
            st.session_state.scored_df = None
            st.session_state.filtered_df = None
            st.session_state.clean_base = None
            st.session_state.selected_delete_indices = set()
            st.session_state.actions = {}
            go_next()

# STEP 4: Score/recode text values
elif st.session_state.step == 4:
    st.subheader("Step 4: Score text values in question fields")
    base_df = (st.session_state.paired_df.copy() if st.session_state.get("paired_df") is not None
               else st.session_state.mapped_df.copy())
    all_question_cols = [c for c in BASELINE_QUESTION_COLS + ENDLINE_QUESTION_COLS if c in base_df.columns]

    # Before scoring answers, replace any null/blank value in question columns with ---
    base_df = replace_question_nulls_with_dash(base_df, all_question_cols)

    unscored_df = detect_unscored_values(base_df, all_question_cols)

    def _finalize_scoring(df_scored):
        # Convert scored values to numbers so downstream missing/action logic is consistent.
        final = normalize_score_values(df_scored, all_question_cols)
        st.session_state.scored_df = final
        st.session_state.actions = {}
        st.session_state.actions_confirmed = False
        st.session_state.qa_ready = False

    if unscored_df.empty:
        st.success("All question fields are already numeric, or contain only recognized missing values.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Back"):
                go_back()
        with c2:
            if st.button("Next: Map questions into items", type="primary"):
                _finalize_scoring(base_df)
                go_next()
    else:
        st.warning("Some question values are text/not scored. Choose the numeric score for each uploaded value.")

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
                scored_df = apply_value_recode(base_df, all_question_cols, recode_mapping)
                remaining_unscored = detect_unscored_values(scored_df, all_question_cols)
                if len(remaining_unscored) > 0:
                    st.error("Some text values are still not scored. Please review the list again.")
                    st.dataframe(remaining_unscored, use_container_width=True)
                else:
                    _finalize_scoring(scored_df)
                    go_next()

# STEP 8: Row review
elif st.session_state.step == 8:
    st.subheader("Step 8: Review rows with high missing percentage")
    mapped_df = (st.session_state.scored_df.copy() if st.session_state.get("scored_df") is not None
                 else (st.session_state.paired_df.copy() if st.session_state.get("paired_df") is not None
                       else st.session_state.mapped_df.copy()))

    filtered_df = mapped_df.copy()

    filtered_df.insert(0, "Delete Action", "")
    filtered_df.insert(1, "baseline missing %", missing_pct(filtered_df, BASELINE_QUESTION_COLS))
    filtered_df.insert(2, "endline missing %", missing_pct(filtered_df, ENDLINE_QUESTION_COLS))
    st.session_state.filtered_df = filtered_df

    st.write(f"Rows after pairing: **{len(filtered_df)}**")
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
            st.session_state.actions = {}
            st.session_state.actions_confirmed = False
            st.session_state.qa_ready = False
            go_next()

# STEP 9: Question actions
elif st.session_state.step == 9:
    st.subheader("Step 9: Question Missing Review and Actions")
    clean_base = st.session_state.clean_base.copy()
    st.info(f"Question missing percentages are calculated using **{len(clean_base)} cleaned rows**.")

    action_options = ["change missing to 0", "drop this question"]
    valid_actions = set(action_options)

    question_review_rows = []
    for base_col in BASELINE_QUESTION_COLS:
        post_col = f"{base_col}_post"
        question_name = QUESTION_LABELS.get(base_col, base_col)
        arabic_name, english_name = question_name.split(" | ", 1) if " | " in question_name else ("", question_name)
        base_missing = question_missing_pct(clean_base, base_col)
        end_missing = question_missing_pct(clean_base, post_col)
        high = base_missing >= 0.30 or end_missing >= 0.30
        default_action = "drop this question" if high else "change missing to 0"
        current = st.session_state.actions.get(base_col, default_action)
        if current not in valid_actions:
            current = default_action
        question_review_rows.append({
            "Baseline ID": base_col,
            "Endline ID": post_col,
            "Arabic": arabic_name,
            "English": english_name,
            "% Missing Baseline": base_missing * 100,
            "% Missing Endline": end_missing * 100,
            "High Missing": "YES" if high else "",
            "Action": current,
        })
    question_review_df = pd.DataFrame(question_review_rows)

    st.warning("Questions with baseline or endline missing ≥ 30% are flagged 'High Missing' and default to 'drop this question'. "
               "Change any Action, then press **Apply actions** — all edits are saved together on Apply, so there is no per-row delay.")

    # A form batches every edit and only reruns the app when you press a submit button.
    # This removes the previous lag where a change registered only after clicking another row.
    with st.form("question_actions_form", clear_on_submit=False):
        edited_actions = st.data_editor(
            question_review_df,
            column_config={
                "Baseline ID": st.column_config.TextColumn("Baseline ID", disabled=True),
                "Endline ID": st.column_config.TextColumn("Endline ID", disabled=True),
                "Arabic": st.column_config.TextColumn("Arabic", disabled=True),
                "English": st.column_config.TextColumn("English", disabled=True),
                "% Missing Baseline": st.column_config.ProgressColumn("% Missing Baseline", format="%.1f%%", min_value=0, max_value=100),
                "% Missing Endline": st.column_config.ProgressColumn("% Missing Endline", format="%.1f%%", min_value=0, max_value=100),
                "High Missing": st.column_config.TextColumn("High Missing", disabled=True),
                "Action": st.column_config.SelectboxColumn("Action", options=action_options, required=True),
            },
            disabled=["Baseline ID", "Endline ID", "Arabic", "English", "% Missing Baseline", "% Missing Endline", "High Missing"],
            hide_index=True,
            use_container_width=True,
            height=520,
            key="question_action_editor_form",
        )
        fc1, fc2 = st.columns(2)
        with fc1:
            set_all_zero = st.form_submit_button("Set all to 'change missing to 0'")
        with fc2:
            submitted = st.form_submit_button("Apply actions", type="primary")

    if set_all_zero:
        st.session_state.actions = {r["Baseline ID"]: "change missing to 0" for _, r in question_review_df.iterrows()}
        st.session_state.qa_ready = True
        st.rerun()

    if submitted:
        ea = edited_actions.copy()
        ea["Action"] = ea.apply(
            lambda r: r["Action"] if r["Action"] in valid_actions else ("drop this question" if r["High Missing"] == "YES" else "change missing to 0"),
            axis=1,
        )
        st.session_state.actions = dict(zip(ea["Baseline ID"], ea["Action"]))
        st.session_state.qa_ready = True
        st.rerun()

    if st.session_state.get("qa_ready"):
        dropped = [q for q, a in st.session_state.actions.items() if a == "drop this question"]
        if dropped:
            st.warning(f"{len(dropped)} question(s) will be dropped from baseline and endline.")
            drop_df = pd.DataFrame({
                "Baseline ID": dropped,
                "English": [QUESTION_LABELS.get(q, q).split(" | ", 1)[-1] for q in dropped],
            })
            st.dataframe(drop_df, hide_index=True, use_container_width=True)
        else:
            st.success("No questions will be dropped.")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("Back to editing"):
                st.session_state.qa_ready = False
                st.rerun()
        with cc2:
            if st.button("Confirm and continue to download", type="primary"):
                st.session_state.qa_ready = False
                go_next()

    st.divider()
    if st.button("Back"):
        go_back()

# STEP 5: Map questions into items (drag and drop)
elif st.session_state.step == 5:
    st.subheader("Step 5: Map questions into items")
    st.write("Drag each question card into the correct item box. Defaults follow the standard IDELA structure — adjust if needed.")

    ordered_items = [f"ITEM_{i}" for i in range(1, 22)]
    current_map = dict(st.session_state.item_mapping) if st.session_state.item_mapping else dict(ITEM_MAPPING)
    all_qids = list(QUESTION_LABELS.keys())

    def _q_card(qid):
        lab = QUESTION_LABELS.get(qid, qid)
        eng = lab.split(" | ", 1)[1].strip() if " | " in lab else str(lab)
        return f"{qid} · {eng}"

    def _item_header(item_id):
        return f"{item_id} · {ITEM_NAMES.get(item_id, item_id)}"

    UNASSIGNED_Q = "⬚ Unassigned questions"
    card_to_qid, header_to_item = {}, {}
    containers = []
    for item_id in ordered_items:
        header = _item_header(item_id)
        header_to_item[header] = item_id
        cards = []
        for q in [x for x in all_qids if current_map.get(x) == item_id]:
            c = _q_card(q); card_to_qid[c] = q; cards.append(c)
        containers.append({"header": header, "items": cards})
    un_cards = []
    for q in all_qids:
        if current_map.get(q) not in ordered_items:
            c = _q_card(q); card_to_qid[c] = q; un_cards.append(c)
    containers.append({"header": UNASSIGNED_Q, "items": un_cards})

    use_dropdown = st.checkbox("Use dropdown editor instead of drag & drop", value=not _HAS_SORTABLES, key="itemmap_dropdown")

    new_map = {}
    if _HAS_SORTABLES and not use_dropdown:
        result = sort_items(containers, multi_containers=True, direction="vertical", custom_style=SORTABLE_CSS)
        for cont in result:
            item_id = header_to_item.get(cont["header"])
            if item_id is None:
                continue
            for card in cont["items"]:
                q = card_to_qid.get(card)
                if q:
                    new_map[q] = item_id
    else:
        if not _HAS_SORTABLES:
            st.warning("Drag-and-drop component not installed. Add `streamlit-sortables` to requirements.txt for the drag view. Using dropdown editor for now.")
        item_choices = [f"{i} · {ITEM_NAMES.get(i, i)}" for i in ordered_items] + ["(unassigned)"]
        item_label_to_id = {f"{i} · {ITEM_NAMES.get(i, i)}": i for i in ordered_items}
        for q in all_qids:
            di = current_map.get(q)
            dl = f"{di} · {ITEM_NAMES.get(di, di)}" if di in ordered_items else "(unassigned)"
            idx = item_choices.index(dl) if dl in item_choices else len(item_choices) - 1
            choice = st.selectbox(_q_card(q), item_choices, index=idx, key=f"itemmap_{q}")
            if choice in item_label_to_id:
                new_map[q] = item_label_to_id[choice]

    st.session_state.item_mapping = new_map

    empty_items = [it for it in ordered_items if not any(v == it for v in new_map.values())]
    if empty_items:
        st.warning("Items with no questions yet: " + ", ".join(f"{i} ({ITEM_NAMES.get(i, i)})" for i in empty_items))

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back"):
            go_back()
    with c2:
        if st.button("Next: Set count-question max scores", type="primary"):
            go_next()

# STEP 7: Map items into domains (drag and drop)
elif st.session_state.step == 7:
    st.subheader("Step 7: Map items into domains")
    st.write("Drag each item card into the correct domain box. Defaults follow the standard IDELA domains — adjust if needed.")

    ordered_items = [f"ITEM_{i}" for i in range(1, 22)]
    current_domains = st.session_state.domain_mapping or {k: list(v) for k, v in DOMAIN_MAPPING.items()}
    domain_names = list(DOMAIN_MAPPING.keys())

    def _item_card2(item_id):
        return f"{item_id} · {ITEM_NAMES.get(item_id, item_id)}"

    item_to_domain = {}
    for dname, items in current_domains.items():
        for it in items:
            item_to_domain[it] = dname

    UNASSIGNED_I = "⬚ Unassigned items"
    card_to_item, header_to_domain = {}, {}
    containers = []
    for dname in domain_names:
        header_to_domain[dname] = dname
        cards = []
        for it in [x for x in ordered_items if item_to_domain.get(x) == dname]:
            c = _item_card2(it); card_to_item[c] = it; cards.append(c)
        containers.append({"header": dname, "items": cards})
    un_cards = []
    for it in ordered_items:
        if item_to_domain.get(it) not in domain_names:
            c = _item_card2(it); card_to_item[c] = it; un_cards.append(c)
    containers.append({"header": UNASSIGNED_I, "items": un_cards})

    use_dropdown = st.checkbox("Use dropdown editor instead of drag & drop", value=not _HAS_SORTABLES, key="domainmap_dropdown")

    new_domains = {d: [] for d in domain_names}
    if _HAS_SORTABLES and not use_dropdown:
        result = sort_items(containers, multi_containers=True, direction="vertical", custom_style=SORTABLE_CSS)
        for cont in result:
            dname = header_to_domain.get(cont["header"])
            if dname is None:
                continue
            for card in cont["items"]:
                it = card_to_item.get(card)
                if it:
                    new_domains[dname].append(it)
    else:
        if not _HAS_SORTABLES:
            st.warning("Drag-and-drop component not installed. Add `streamlit-sortables` to requirements.txt for the drag view. Using dropdown editor for now.")
        choices = domain_names + ["(unassigned)"]
        for it in ordered_items:
            dd = item_to_domain.get(it)
            idx = choices.index(dd) if dd in domain_names else len(choices) - 1
            choice = st.selectbox(_item_card2(it), choices, index=idx, key=f"domainmap_{it}")
            if choice in domain_names:
                new_domains[choice].append(it)

    st.session_state.domain_mapping = new_domains

    unassigned_items = [it for it in ordered_items if all(it not in v for v in new_domains.values())]
    if unassigned_items:
        st.warning("Items not in any domain (excluded from domain scores): " + ", ".join(unassigned_items))

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back"):
            go_back()
    with c2:
        if st.button("Next: Review rows", type="primary"):
            go_next()

# STEP 6: Set maximum score for count/number questions
elif st.session_state.step == 6:
    st.subheader("Step 6: Maximum score for count / number questions")
    scored = st.session_state.get("scored_df")
    if scored is None:
        st.error("No scored data yet. Go back to Step 4 (Score text values).")
        st.stop()
    st.write("Some questions are counts or levels rather than simply 0/1. Set the maximum possible score for each. "
             "The analysis uses current score ÷ max score for these questions.")

    base_qs = [q for q in BASELINE_QUESTION_COLS if q in scored.columns]
    detected = detect_count_questions(scored, base_qs)
    count_qs = [q for q in base_qs if q in COUNT_QUESTION_DEFAULT_MAX or q in detected]

    if not count_qs:
        st.info("No count/number questions detected — every question looks like 0/1.")
        st.session_state.max_scores = {}
    else:
        current = dict(st.session_state.max_scores or {})
        new_max = {}
        for q in count_qs:
            default = current.get(q, COUNT_QUESTION_DEFAULT_MAX.get(q, detected.get(q, 10)))
            new_max[q] = st.number_input(
                f"{q} — {question_excel_name(q, 'both')}",
                min_value=1.0, value=float(default), step=1.0, key=f"maxscore_{q}",
            )
        st.session_state.max_scores = new_max
        if "i19_closed_corners" in count_qs:
            st.caption("Note: Item 19 (closed corners) label says 0–3; your specified default is 4 — change it above if it should be 3.")

        preview = []
        for q in count_qs:
            mx = float(new_max[q])
            pre = pd.to_numeric(scored[q], errors="coerce")
            pre = pre[pre != 999]
            avg = float(pre.mean()) if pre.notna().any() else 0.0
            preview.append({
                "Question": question_excel_name(q, "english"),
                "Max": mx,
                "Avg pre score": round(avg, 2),
                "Avg pre %": round(avg / mx * 100, 1) if mx else 0.0,
            })
        st.markdown("#### Preview (baseline, current data — current score ÷ max)")
        st.dataframe(pd.DataFrame(preview), hide_index=True, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back"):
            go_back()
    with c2:
        if st.button("Next: Map items into domains", type="primary"):
            go_next()

# STEP 10: Download
elif st.session_state.step == 10:
    st.subheader("Step 10: Preview and Download")
    clean_base = st.session_state.clean_base.copy()
    actions = st.session_state.actions
    max_scores = st.session_state.get("max_scores") or {}
    item_mapping = st.session_state.get("item_mapping") or ITEM_MAPPING
    domain_mapping = st.session_state.get("domain_mapping") or DOMAIN_MAPPING

    clean_df = apply_actions(clean_base, actions)

    remaining_question_cols = [c for c in BASELINE_QUESTION_COLS + ENDLINE_QUESTION_COLS if c in clean_df.columns]
    remaining_missing_summary = get_remaining_missing_summary(clean_df, remaining_question_cols)

    q_df = analysis_by_question(clean_df, max_scores)
    i_df = analysis_by_item(clean_df, item_mapping, max_scores)
    d_df = analysis_by_domain(q_df, item_mapping, domain_mapping)
    cleaned_sheet = build_cleaned_data_sheet(clean_df, max_scores)

    st.write("Question analysis preview")
    st.dataframe(q_df, use_container_width=True, hide_index=True)
    st.write("Domain analysis preview")
    st.dataframe(d_df, use_container_width=True, hide_index=True)

    if len(remaining_missing_summary) > 0:
        cols = sorted(remaining_missing_summary["Question ID"].tolist())
        st.error("Download is blocked. Missing values remain in: " + ", ".join(cols))
        st.warning("Go back to Step 9 (Question actions) and choose an action (change missing to 0, or drop the question).")
    else:
        raw_sheet = st.session_state.get("download_raw_df")
        if raw_sheet is None:
            raw_sheet = st.session_state.get("filtered_df", clean_df)
        rq = rowlevel_questions(clean_df, max_scores)
        ri = rowlevel_items(clean_df, item_mapping, max_scores)
        rd = rowlevel_domains(clean_df, item_mapping, domain_mapping, max_scores)
        excel_bytes = write_new_workbook(raw_sheet, cleaned_sheet, q_df, i_df, d_df, rq, ri, rd)
        st.success("Workbook ready: raw data, cleaned data, and question / item / domain analysis.")
        st.download_button(
            label="Download IDELA analysis workbook",
            data=excel_bytes,
            file_name="idela_analysis_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

    if st.button("Back"):
        go_back()
