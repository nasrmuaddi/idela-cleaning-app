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
    "sub_district",
]

QUESTION_NAME_MAP = {
  "i1a_name_mark": {
    "arabic": "هل يمكنك أن تخبرني باسمك الأول واسم عائلتك؟",
    "english": "Can you tell me your first and last/surname name?",
    "post": "i1a_name_mark_post"
  },
  "i1a_name_mark_post": {
    "arabic": "هل يمكنك أن تخبرني باسمك الأول واسم عائلتك؟",
    "english": "Can you tell me your first and last/surname name?",
    "baseline": "i1a_name_mark"
  },
  "i1a_age_mark": {
    "arabic": "هل يمكنك أن تخبرني عن عمرك؟",
    "english": "Can you tell me how old you are?",
    "post": "i1a_age_mark_post"
  },
  "i1a_age_mark_post": {
    "arabic": "هل يمكنك أن تخبرني عن عمرك؟",
    "english": "Can you tell me how old you are?",
    "baseline": "i1a_age_mark"
  },
  "i1a_sex_mark": {
    "arabic": "هل أنت صبي أم فتاة؟",
    "english": "Are you a boy or a girl?",
    "post": "i1a_sex_mark_post"
  },
  "i1a_sex_mark_post": {
    "arabic": "هل أنت صبي أم فتاة؟",
    "english": "Are you a boy or a girl?",
    "baseline": "i1a_sex_mark"
  },
  "i1a_caregiver_mark": {
    "arabic": "أخبرني باسم شخص واحد يعتني بك",
    "english": "Please tell me the name of one person who takes care of you",
    "post": "i1a_caregiver_mark_post"
  },
  "i1a_caregiver_mark_post": {
    "arabic": "أخبرني باسم شخص واحد يعتني بك",
    "english": "Please tell me the name of one person who takes care of you",
    "baseline": "i1a_caregiver_mark"
  },
  "i1a_neighborhood_mark": {
    "arabic": "اسم الحي/المجتمع/القرية التي تعيش فيها",
    "english": "Can you tell me the name of the neighborhood/community/village that you live in ?",
    "post": "i1a_neighborhood_mark_post"
  },
  "i1a_neighborhood_mark_post": {
    "arabic": "اسم الحي/المجتمع/القرية التي تعيش فيها",
    "english": "Can you tell me the name of the neighborhood/community/village that you live in ?",
    "baseline": "i1a_neighborhood_mark"
  },
  "i1a_state_mark": {
    "arabic": "اسم الولاية/الدولة التي تعيش فيها",
    "english": "Can you tell me the name of the state/country that you live in?",
    "post": "i1a_state_mark_post"
  },
  "i1a_state_mark_post": {
    "arabic": "اسم الولاية/الدولة التي تعيش فيها",
    "english": "Can you tell me the name of the state/country that you live in?",
    "baseline": "i1a_state_mark"
  },
  "i1a_country_mark": {
    "arabic": "هل من الممكن أن تخبرني عن اسم البلد أو المدينة التي تعيش به الآن؟ (فيك تخبرني شو اسم البلد أو المدينة يللي عايش فية هلق؟)",
    "english": "Can you tell me the name of the state/country that you live in?",
    "post": "i1a_country_mark_post"
  },
  "i1a_country_mark_post": {
    "arabic": "هل من الممكن أن تخبرني عن اسم البلد أو المدينة التي تعيش به الآن؟ (فيك تخبرني شو اسم البلد أو المدينة يللي عايش فية هلق؟)",
    "english": "Can you tell me the name of the state/country that you live in?",
    "baseline": "i1a_country_mark"
  },
  "country_from_mark": {
    "arabic": "من الممكن ان تخبرني عن اسم البلد الذي اتو منه اهلك؟ (فيك تخبرني عن اسم البلد يلي ايجو منو اهلك)",
    "english": "Can you tell me the name of the state/country that you live in?",
    "post": "country_from_mark_post"
  },
  "country_from_mark_post": {
    "arabic": "من الممكن ان تخبرني عن اسم البلد الذي اتو منه اهلك؟ (فيك تخبرني عن اسم البلد يلي ايجو منو اهلك)",
    "english": "Can you tell me the name of the state/country that you live in?",
    "baseline": "country_from_mark"
  },
  "i2a_biggest_circle_mark": {
    "arabic": "يحدد الدائرة الأكبر",
    "english": "Child identifies biggest circle",
    "post": "i2a_biggest_circle_mark_post"
  },
  "i2a_biggest_circle_mark_post": {
    "arabic": "يحدد الدائرة الأكبر",
    "english": "Child identifies biggest circle",
    "baseline": "i2a_biggest_circle_mark"
  },
  "i2b_smallest_circle_mark": {
    "arabic": "يحدد الدائرة الأصغر",
    "english": "Child identifies smallest circle",
    "post": "i2b_smallest_circle_mark_post"
  },
  "i2b_smallest_circle_mark_post": {
    "arabic": "يحدد الدائرة الأصغر",
    "english": "Child identifies smallest circle",
    "baseline": "i2b_smallest_circle_mark"
  },
  "i2c_longest_stick_mark": {
    "arabic": "يحدد العصا الأطول",
    "english": "Child identifies longest stick",
    "post": "i2c_longest_stick_mark_post"
  },
  "i2c_longest_stick_mark_post": {
    "arabic": "يحدد العصا الأطول",
    "english": "Child identifies longest stick",
    "baseline": "i2c_longest_stick_mark"
  },
  "i2d_shortest_stick_mark": {
    "arabic": "يحدد العصا الأقصر",
    "english": "Child identifies shortest stick",
    "post": "i2d_shortest_stick_mark_post"
  },
  "i2d_shortest_stick_mark_post": {
    "arabic": "يحدد العصا الأقصر",
    "english": "Child identifies shortest stick",
    "baseline": "i2d_shortest_stick_mark"
  },
  "i3_sort_criterion1_mark": {
    "arabic": "صنف الطفل البطاقات حسب اللون أو الشكل/ طريقة واحدة فقط",
    "english": "Child sorts cards by first criterion",
    "post": "i3_sort_criterion1_mark_post"
  },
  "i3_sort_criterion1_mark_post": {
    "arabic": "صنف الطفل البطاقات حسب اللون أو الشكل/ طريقة واحدة فقط",
    "english": "Child sorts cards by first criterion",
    "baseline": "i3_sort_criterion1_mark"
  },
  "i3_sort_criterion2_mark": {
    "arabic": "صنف الطفل البطاقات حسب اللون أو الشكل/ طريقة ثانية فقط –",
    "english": "Child sorts cards by second criterion",
    "post": "i3_sort_criterion2_mark_post"
  },
  "i3_sort_criterion2_mark_post": {
    "arabic": "صنف الطفل البطاقات حسب اللون أو الشكل/ طريقة ثانية فقط –",
    "english": "Child sorts cards by second criterion",
    "baseline": "i3_sort_criterion2_mark"
  },
  "i4_circle_mark": {
    "arabic": "يتعرف على الدائرة",
    "english": "Child identifies circle",
    "post": "i4_circle_mark_post"
  },
  "i4_circle_mark_post": {
    "arabic": "يتعرف على الدائرة",
    "english": "Child identifies circle",
    "baseline": "i4_circle_mark"
  },
  "i4_rectangle_mark": {
    "arabic": "يتعرف على المستطيل",
    "english": "Child identifies rectangle",
    "post": "i4_rectangle_mark_post"
  },
  "i4_rectangle_mark_post": {
    "arabic": "يتعرف على المستطيل",
    "english": "Child identifies rectangle",
    "baseline": "i4_rectangle_mark"
  },
  "i4_triangle_mark": {
    "arabic": "يتعرف على المثلث",
    "english": "Child identifies triangle",
    "post": "i4_triangle_mark_post"
  },
  "i4_triangle_mark_post": {
    "arabic": "يتعرف على المثلث",
    "english": "Child identifies triangle",
    "baseline": "i4_triangle_mark"
  },
  "i4_square_mark": {
    "arabic": "يتعرف على المربع",
    "english": "Child identifies square",
    "post": "i4_square_mark_post"
  },
  "i4_square_mark_post": {
    "arabic": "يتعرف على المربع",
    "english": "Child identifies square",
    "baseline": "i4_square_mark"
  },
  "i4_circle_env_mark": {
    "arabic": "حدد الطفل شيء يشبه الدائرة من محيطه",
    "english": "Child identifies circle in the environment",
    "post": "i4_circle_env_mark_post"
  },
  "i4_circle_env_mark_post": {
    "arabic": "حدد الطفل شيء يشبه الدائرة من محيطه",
    "english": "Child identifies circle in the environment",
    "baseline": "i4_circle_env_mark"
  },
  "i5_row12_correct_count": {
    "arabic": "الصفوف 1-2: عدد الأرقام الصحيحة (0-10)",
    "english": "Rows 1-2: Number of correct numbers (0-10)",
    "post": "i5_row12_correct_count_post"
  },
  "i5_row12_correct_count_post": {
    "arabic": "الصفوف 1-2: عدد الأرقام الصحيحة (0-10)",
    "english": "Rows 1-2: Number of correct numbers (0-10)",
    "baseline": "i5_row12_correct_count"
  },
  "i5_row34_correct_count": {
    "arabic": "الصفوف 3-4: عدد الأرقام الصحيحة (0-10)",
    "english": "Rows 3-4: Number of correct numbers (0-10)",
    "post": "i5_row34_correct_count_post"
  },
  "i5_row34_correct_count_post": {
    "arabic": "الصفوف 3-4: عدد الأرقام الصحيحة (0-10)",
    "english": "Rows 3-4: Number of correct numbers (0-10)",
    "baseline": "i5_row34_correct_count"
  },
  "i6_give3_mark": {
    "arabic": "يحدد 3 عناصر",
    "english": "Child identifies 3 items",
    "post": "i6_give3_mark_post"
  },
  "i6_give3_mark_post": {
    "arabic": "يحدد 3 عناصر",
    "english": "Child identifies 3 items",
    "baseline": "i6_give3_mark"
  },
  "i6_give5_mark": {
    "arabic": "يحدد 5 عناصر",
    "english": "Child identifies 5 items",
    "post": "i6_give5_mark_post"
  },
  "i6_give5_mark_post": {
    "arabic": "يحدد 5 عناصر",
    "english": "Child identifies 5 items",
    "baseline": "i6_give5_mark"
  },
  "i6_give8_mark": {
    "arabic": "يحدد 8 عناصر",
    "english": "Child identifies 8 items",
    "post": "i6_give8_mark_post"
  },
  "i6_give8_mark_post": {
    "arabic": "يحدد 8 عناصر",
    "english": "Child identifies 8 items",
    "baseline": "i6_give8_mark"
  },
  "i6_focus_mark": {
    "arabic": "يظل مركزًا على المهمة؛ لا يتشتت بسهولة",
    "english": "Child stays concentrated  on the task at hand; not easily distracted",
    "post": "i6_focus_mark_post"
  },
  "i6_focus_mark_post": {
    "arabic": "يظل مركزًا على المهمة؛ لا يتشتت بسهولة",
    "english": "Child stays concentrated  on the task at hand; not easily distracted",
    "baseline": "i6_focus_mark"
  },
  "i6_eager_mark": {
    "arabic": "متحمس لإنجاز المهمة؛ لا يريد التوقف",
    "english": "Child is motivated to complete task; does not want to stop\nthe task.",
    "post": "i6_eager_mark_post"
  },
  "i6_eager_mark_post": {
    "arabic": "متحمس لإنجاز المهمة؛ لا يريد التوقف",
    "english": "Child is motivated to complete task; does not want to stop\nthe task.",
    "baseline": "i6_eager_mark"
  },
  "i7_add3_2_mark": {
    "arabic": "يضيف 3 و 2",
    "english": "Child adds 3 and 2",
    "post": "i7_add3_2_mark_post"
  },
  "i7_add3_2_mark_post": {
    "arabic": "يضيف 3 و 2",
    "english": "Child adds 3 and 2",
    "baseline": "i7_add3_2_mark"
  },
  "i7_add2_2_mark": {
    "arabic": "يضيف 2 و 2",
    "english": "Child adds 2 and 2",
    "post": "i7_add2_2_mark_post"
  },
  "i7_add2_2_mark_post": {
    "arabic": "يضيف 2 و 2",
    "english": "Child adds 2 and 2",
    "baseline": "i7_add2_2_mark"
  },
  "i7_subtract1_from3_mark": {
    "arabic": "يطرح 1 من 3",
    "english": "Child subtracts 1 from 3",
    "post": "i7_subtract1_from3_mark_post"
  },
  "i7_subtract1_from3_mark_post": {
    "arabic": "يطرح 1 من 3",
    "english": "Child subtracts 1 from 3",
    "baseline": "i7_subtract1_from3_mark"
  },
  "i8_friends_count": {
    "arabic": "عدد الأصدقاء المذكورين (0-10)",
    "english": "Number of friends named (0-10)",
    "post": "i8_friends_count_post"
  },
  "i8_friends_count_post": {
    "arabic": "عدد الأصدقاء المذكورين (0-10)",
    "english": "Number of friends named (0-10)",
    "baseline": "i8_friends_count"
  },
  "i9_sad_trigger_mark": {
    "arabic": "يحدد شيئًا يجعله حزينًا",
    "english": "Child identifies something that makes them sad",
    "post": "i9_sad_trigger_mark_post"
  },
  "i9_sad_trigger_mark_post": {
    "arabic": "يحدد شيئًا يجعله حزينًا",
    "english": "Child identifies something that makes them sad",
    "baseline": "i9_sad_trigger_mark"
  },
  "i9_regulate1_mark": {
    "arabic": "يعطي إجابة واحدة للتعامل مع الحزن",
    "english": "Child gives one response on dealing with sad feeling",
    "post": "i9_regulate1_mark_post"
  },
  "i9_regulate1_mark_post": {
    "arabic": "يعطي إجابة واحدة للتعامل مع الحزن",
    "english": "Child gives one response on dealing with sad feeling",
    "baseline": "i9_regulate1_mark"
  },
  "i9_regulate2_mark": {
    "arabic": "يعطي إجابة ثانية للتعامل مع الحزن",
    "english": "Child gives another response on dealing with  sad feeling",
    "post": "i9_regulate2_mark_post"
  },
  "i9_regulate2_mark_post": {
    "arabic": "يعطي إجابة ثانية للتعامل مع الحزن",
    "english": "Child gives another response on dealing with  sad feeling",
    "baseline": "i9_regulate2_mark"
  },
  "i9_happy_trigger_mark": {
    "arabic": "يحدد شيئًا يجعله سعيدًا",
    "english": "Child identifies something that makes them happy",
    "post": "i9_happy_trigger_mark_post"
  },
  "i9_happy_trigger_mark_post": {
    "arabic": "يحدد شيئًا يجعله سعيدًا",
    "english": "Child identifies something that makes them happy",
    "baseline": "i9_happy_trigger_mark"
  },
  "i10_understands_feeling_mark": {
    "arabic": "الطفل يدرك أن صديقه يشعر بالحزن/الألم/الضيق",
    "english": "Child identifies that friend is feeling sad/hurt/upset",
    "post": "i10_understands_feeling_mark_post"
  },
  "i10_understands_feeling_mark_post": {
    "arabic": "الطفل يدرك أن صديقه يشعر بالحزن/الألم/الضيق",
    "english": "Child identifies that friend is feeling sad/hurt/upset",
    "baseline": "i10_understands_feeling_mark"
  },
  "i10_help1_mark": {
    "arabic": "الطفل يعطي إجابة واحدة عن كيفية جعل صديقه يشعر بتحسن",
    "english": "Child gives one response for how to make friend feel better",
    "post": "i10_help1_mark_post"
  },
  "i10_help1_mark_post": {
    "arabic": "الطفل يعطي إجابة واحدة عن كيفية جعل صديقه يشعر بتحسن",
    "english": "Child gives one response for how to make friend feel better",
    "baseline": "i10_help1_mark"
  },
  "i10_help2_mark": {
    "arabic": "الطفل يعطي إجابة ثانية عن كيفية جعل صديقه يشعر بتحسن",
    "english": "Child gives second response for how to make friend feel better",
    "post": "i10_help2_mark_post"
  },
  "i10_help2_mark_post": {
    "arabic": "الطفل يعطي إجابة ثانية عن كيفية جعل صديقه يشعر بتحسن",
    "english": "Child gives second response for how to make friend feel better",
    "baseline": "i10_help2_mark"
  },
  "i11_conflict1_mark": {
    "arabic": "يعطي الطفل إجابة واحدة عن كيفية حل النزاع",
    "english": "Child gives one response for how to solve conflict",
    "post": "i11_conflict1_mark_post"
  },
  "i11_conflict1_mark_post": {
    "arabic": "يعطي الطفل إجابة واحدة عن كيفية حل النزاع",
    "english": "Child gives one response for how to solve conflict",
    "baseline": "i11_conflict1_mark"
  },
  "i11_conflict2_mark": {
    "arabic": "يعطي الطفل إجابة ثانية عن كيفية حل النزاع",
    "english": "Child gives second response for how to solve conflict",
    "post": "i11_conflict2_mark_post"
  },
  "i11_conflict2_mark_post": {
    "arabic": "يعطي الطفل إجابة ثانية عن كيفية حل النزاع",
    "english": "Child gives second response for how to solve conflict",
    "baseline": "i11_conflict2_mark"
  },
  "i12_seq1_mark": {
    "arabic": "سلسله الأرقام 1…6",
    "english": "numbers sequance 1…6",
    "post": "i12_seq1_mark_post"
  },
  "i12_seq1_mark_post": {
    "arabic": "سلسله الأرقام 1…6",
    "english": "numbers sequance 1…6",
    "baseline": "i12_seq1_mark"
  },
  "i12_seq2_mark": {
    "arabic": "5…2…9 سلسله الأرقام",
    "english": "numbers sequance 5…2…9",
    "post": "i12_seq2_mark_post"
  },
  "i12_seq2_mark_post": {
    "arabic": "5…2…9 سلسله الأرقام",
    "english": "numbers sequance 5…2…9",
    "baseline": "i12_seq2_mark"
  },
  "i12_seq3_mark": {
    "arabic": "8…3…1…4 سلسله الأرقام",
    "english": "numbers sequance 8…3…1…4",
    "post": "i12_seq3_mark_post"
  },
  "i12_seq3_mark_post": {
    "arabic": "8…3…1…4 سلسله الأرقام",
    "english": "numbers sequance 8…3…1…4",
    "baseline": "i12_seq3_mark"
  },
  "i12_seq4_mark": {
    "arabic": "1…2…4…7…3 سلسله الأرقام",
    "english": "numbers sequance 1…2…4…7…3",
    "post": "i12_seq4_mark_post"
  },
  "i12_seq4_mark_post": {
    "arabic": "1…2…4…7…3 سلسله الأرقام",
    "english": "numbers sequance 1…2…4…7…3",
    "baseline": "i12_seq4_mark"
  },
  "i13_market_items_count": {
    "arabic": "عدد عناصر السوق المذكورة (0-10)",
    "english": "Number of market items named (0-10)",
    "post": "i13_market_items_count_post"
  },
  "i13_market_items_count_post": {
    "arabic": "عدد عناصر السوق المذكورة (0-10)",
    "english": "Number of market items named (0-10)",
    "baseline": "i13_market_items_count"
  },
  "i13_animals_count": {
    "arabic": "عدد الحيوانات المذكورة (0-10)",
    "english": "Number of animals named (0-10)",
    "post": "i13_animals_count_post"
  },
  "i13_animals_count_post": {
    "arabic": "عدد الحيوانات المذكورة (0-10)",
    "english": "Number of animals named (0-10)",
    "baseline": "i13_animals_count"
  },
  "i14_open_book_mark": {
    "arabic": "يفتح الطفل الكتاب بشكل صحيح (يقلب الكتاب بحيث لم تعد مقلوبة)",
    "english": "Child opens the book appropriately (turns book so words are no longer upside down)",
    "post": "i14_open_book_mark_post"
  },
  "i14_open_book_mark_post": {
    "arabic": "يفتح الطفل الكتاب بشكل صحيح (يقلب الكتاب بحيث لم تعد مقلوبة)",
    "english": "Child opens the book appropriately (turns book so words are no longer upside down)",
    "baseline": "i14_open_book_mark"
  },
  "i14_point_text_mark": {
    "arabic": "يشير الطفل إلى النص الموجود على الصفحة (يمكن أن يكون الجملة كاملة، الكلمة الأولى، النص بأكمله)",
    "english": "Child points to text on the page (can be the full sentence, the first word, the whole text)",
    "post": "i14_point_text_mark_post"
  },
  "i14_point_text_mark_post": {
    "arabic": "يشير الطفل إلى النص الموجود على الصفحة (يمكن أن يكون الجملة كاملة، الكلمة الأولى، النص بأكمله)",
    "english": "Child points to text on the page (can be the full sentence, the first word, the whole text)",
    "baseline": "i14_point_text_mark"
  },
  "i14_text_direction_mark": {
    "arabic": "أشار الطفل الطريقة الصحيحة في القراءة (من اليمين)",
    "english": "Child shows direction of text",
    "post": "i14_text_direction_mark_post"
  },
  "i14_text_direction_mark_post": {
    "arabic": "أشار الطفل الطريقة الصحيحة في القراءة (من اليمين)",
    "english": "Child shows direction of text",
    "baseline": "i14_text_direction_mark"
  },
  "i15_row12_letters_count": {
    "arabic": "الصفوف 1-2: عدد الحروف الصحيحة",
    "english": "Rows 1-2: Number of correct letters",
    "post": "i15_row12_letters_count_post"
  },
  "i15_row12_letters_count_post": {
    "arabic": "الصفوف 1-2: عدد الحروف الصحيحة",
    "english": "Rows 1-2: Number of correct letters",
    "baseline": "i15_row12_letters_count"
  },
  "i15_row34_letters_count": {
    "arabic": "الصفوف 3-4: عدد الحروف الصحيحة",
    "english": "Rows 3-4: Number of correct letters",
    "post": "i15_row34_letters_count_post"
  },
  "i15_row34_letters_count_post": {
    "arabic": "الصفوف 3-4: عدد الحروف الصحيحة",
    "english": "Rows 3-4: Number of correct letters",
    "baseline": "i15_row34_letters_count"
  },
  "i16_s_pair_mark": {
    "arabic": "التعرف على زوج الأصوات /ب/",
    "english": "Child identifies /s/ word pair",
    "post": "i16_s_pair_mark_post"
  },
  "i16_s_pair_mark_post": {
    "arabic": "التعرف على زوج الأصوات /ب/",
    "english": "Child identifies /s/ word pair",
    "baseline": "i16_s_pair_mark"
  },
  "i16_t_pair_mark": {
    "arabic": "التعرف على زوج الأصوات /س/",
    "english": "Child identifies /t/ word pair",
    "post": "i16_t_pair_mark_post"
  },
  "i16_t_pair_mark_post": {
    "arabic": "التعرف على زوج الأصوات /س/",
    "english": "Child identifies /t/ word pair",
    "baseline": "i16_t_pair_mark"
  },
  "i16_c_pair_mark": {
    "arabic": "التعرف على زوج الأصوات /ت/",
    "english": "Child identifies /c/ word pair",
    "post": "i16_c_pair_mark_post"
  },
  "i16_c_pair_mark_post": {
    "arabic": "التعرف على زوج الأصوات /ت/",
    "english": "Child identifies /c/ word pair",
    "baseline": "i16_c_pair_mark"
  },
  "i17_writing_level": {
    "arabic": "مستوى الكتابة (0-4)",
    "english": "Writing level (0-4)",
    "post": "i17_writing_level_post"
  },
  "i17_writing_level_post": {
    "arabic": "مستوى الكتابة (0-4)",
    "english": "Writing level (0-4)",
    "baseline": "i17_writing_level"
  },
  "i18_mouse_stole_hat_mark": {
    "arabic": "من سرق قبعة القطة؟ (الفأر)",
    "english": "“Who stole the cat’s hat?” (the mouse)",
    "post": "i18_mouse_stole_hat_mark_post"
  },
  "i18_mouse_stole_hat_mark_post": {
    "arabic": "من سرق قبعة القطة؟ (الفأر)",
    "english": "“Who stole the cat’s hat?” (the mouse)",
    "baseline": "i18_mouse_stole_hat_mark"
  },
  "i18_hat_color_mark": {
    "arabic": "لون القبعة (أحمر)",
    "english": "“Can you tell me the color of the hat?” (red)",
    "post": "i18_hat_color_mark_post"
  },
  "i18_hat_color_mark_post": {
    "arabic": "لون القبعة (أحمر)",
    "english": "“Can you tell me the color of the hat?” (red)",
    "baseline": "i18_hat_color_mark"
  },
  "i18_why_chased_mark": {
    "arabic": "لماذا طاردت القطة الفأر؟",
    "english": "Why did the cat chase the mouse?” (because the mouse\ntook/stole its hat)",
    "post": "i18_why_chased_mark_post"
  },
  "i18_why_chased_mark_post": {
    "arabic": "لماذا طاردت القطة الفأر؟",
    "english": "Why did the cat chase the mouse?” (because the mouse\ntook/stole its hat)",
    "baseline": "i18_why_chased_mark"
  },
  "i18_where_trapped_mark": {
    "arabic": "أين حوصر الفأر؟",
    "english": "”Where did the mouse get trapped ?” (under the table)",
    "post": "i18_where_trapped_mark_post"
  },
  "i18_where_trapped_mark_post": {
    "arabic": "أين حوصر الفأر؟",
    "english": "”Where did the mouse get trapped ?” (under the table)",
    "baseline": "i18_where_trapped_mark"
  },
  "i18_why_spared_mark": {
    "arabic": "لماذا لم تأكل القطة الفأر؟",
    "english": "Child stays concentrated on the task at hand; not easily\ndistracted",
    "post": "i18_why_spared_mark_post"
  },
  "i18_why_spared_mark_post": {
    "arabic": "لماذا لم تأكل القطة الفأر؟",
    "english": "Child stays concentrated on the task at hand; not easily\ndistracted",
    "baseline": "i18_why_spared_mark"
  },
  "i18_focus_mark": {
    "arabic": "يظل مركزًا على المهمة؛ لا يتشتت بسهولة",
    "english": "Child stays concentrated on the task at hand; not easily distracted",
    "post": "i18_focus_mark_post"
  },
  "i18_focus_mark_post": {
    "arabic": "يظل مركزًا على المهمة؛ لا يتشتت بسهولة",
    "english": "Child stays concentrated on the task at hand; not easily distracted",
    "baseline": "i18_focus_mark"
  },
  "i18_eager_mark": {
    "arabic": "متحمس لإنجاز المهمة؛ لا يريد التوقف",
    "english": "Child is motivated to complete task; does not want to stop\nthe task.",
    "post": "i18_eager_mark_post"
  },
  "i18_eager_mark_post": {
    "arabic": "متحمس لإنجاز المهمة؛ لا يريد التوقف",
    "english": "Child is motivated to complete task; does not want to stop\nthe task.",
    "baseline": "i18_eager_mark"
  },
  "i19_closed_corners": {
    "arabic": "عدد الزوايا المغلقة بدون فجوات (0-3)",
    "english": "a)\tNumber of closed corners, no gaps (0, 1, 2, 3)",
    "post": "i19_closed_corners_post"
  },
  "i19_closed_corners_post": {
    "arabic": "عدد الزوايا المغلقة بدون فجوات (0-3)",
    "english": "a)\tNumber of closed corners, no gaps (0, 1, 2, 3)",
    "baseline": "i19_closed_corners"
  },
  "i19_exited_mark": {
    "arabic": "الطفل متحمس لإتمام المهمة، لا يريد أن يتوقف عن العمل.",
    "english": "The child is excited to complete the task and does not want to stop working.",
    "post": "i19_exited_mark_post"
  },
  "i19_exited_mark_post": {
    "arabic": "الطفل متحمس لإتمام المهمة، لا يريد أن يتوقف عن العمل.",
    "english": "The child is excited to complete the task and does not want to stop working.",
    "baseline": "i19_exited_mark"
  },
  "i20_head_mark": {
    "arabic": "يرسم رأسًا",
    "english": "Child draws a head",
    "post": "i20_head_mark_post"
  },
  "i20_head_mark_post": {
    "arabic": "يرسم رأسًا",
    "english": "Child draws a head",
    "baseline": "i20_head_mark"
  },
  "i20_torso_mark": {
    "arabic": "يرسم جذعًا/جسمًا",
    "english": "Child draws a trunk/body",
    "post": "i20_torso_mark_post"
  },
  "i20_torso_mark_post": {
    "arabic": "يرسم جذعًا/جسمًا",
    "english": "Child draws a trunk/body",
    "baseline": "i20_torso_mark"
  },
  "i20_arms_mark": {
    "arabic": "يرسم الذراعين",
    "english": "Child draws arms",
    "post": "i20_arms_mark_post"
  },
  "i20_arms_mark_post": {
    "arabic": "يرسم الذراعين",
    "english": "Child draws arms",
    "baseline": "i20_arms_mark"
  },
  "i20_legs_mark": {
    "arabic": "يرسم الساقين",
    "english": "Child draws legs",
    "post": "i20_legs_mark_post"
  },
  "i20_legs_mark_post": {
    "arabic": "يرسم الساقين",
    "english": "Child draws legs",
    "baseline": "i20_legs_mark"
  },
  "i20_face1_mark": {
    "arabic": "يرسم سمة واحدة من سمات الوجه",
    "english": "Child draws 1 facial feature",
    "post": "i20_face1_mark_post"
  },
  "i20_face1_mark_post": {
    "arabic": "يرسم سمة واحدة من سمات الوجه",
    "english": "Child draws 1 facial feature",
    "baseline": "i20_face1_mark"
  },
  "i20_face2_mark": {
    "arabic": "يرسم سمتين من سمات الوجه",
    "english": "Child draws 2 facial feature",
    "post": "i20_face2_mark_post"
  },
  "i20_face2_mark_post": {
    "arabic": "يرسم سمتين من سمات الوجه",
    "english": "Child draws 2 facial feature",
    "baseline": "i20_face2_mark"
  },
  "i20_hands_mark": {
    "arabic": "يرسم اليدين",
    "english": "Child draws hands",
    "post": "i20_hands_mark_post"
  },
  "i20_hands_mark_post": {
    "arabic": "يرسم اليدين",
    "english": "Child draws hands",
    "baseline": "i20_hands_mark"
  },
  "i20_feet_mark": {
    "arabic": "يرسم القدمين",
    "english": "Child draws feet",
    "post": "i20_feet_mark_post"
  },
  "i20_feet_mark_post": {
    "arabic": "يرسم القدمين",
    "english": "Child draws feet",
    "baseline": "i20_feet_mark"
  },
  "i20_focus_mark": {
    "arabic": "يبقى مركزًا على المهمة؛ لا يتشتت بسهولة",
    "english": "Child stays concentrated  on the task at hand; not easily\ndistracted",
    "post": "i20_focus_mark_post"
  },
  "i20_focus_mark_post": {
    "arabic": "يبقى مركزًا على المهمة؛ لا يتشتت بسهولة",
    "english": "Child stays concentrated  on the task at hand; not easily\ndistracted",
    "baseline": "i20_focus_mark"
  },
  "i20_eager_mark": {
    "arabic": "متحمس لإنجاز المهمة؛ لا يريد التوقف",
    "english": "Child is motivated to complete task; does not want to stop the task.",
    "post": "i20_eager_mark_post"
  },
  "i20_eager_mark_post": {
    "arabic": "متحمس لإنجاز المهمة؛ لا يريد التوقف",
    "english": "Child is motivated to complete task; does not want to stop the task.",
    "baseline": "i20_eager_mark"
  },
  "i21_steps": {
    "arabic": "عدد الخطوات التي قفزها (بحد أقصى 10)",
    "english": "a)\tNumber of steps hoped (Maximum 10 steps.)",
    "post": "i21_steps_post"
  },
  "i21_steps_post": {
    "arabic": "عدد الخطوات التي قفزها (بحد أقصى 10)",
    "english": "a)\tNumber of steps hoped (Maximum 10 steps.)",
    "baseline": "i21_steps"
  }
}


def get_question_arabic(question_code: str) -> str:
    return QUESTION_NAME_MAP.get(question_code, {}).get("arabic", "")


def get_question_english(question_code: str) -> str:
    return QUESTION_NAME_MAP.get(question_code, {}).get("english", "")


def find_range_columns(df: pd.DataFrame, start_col: str, end_col: str) -> List[str]:
    cols = list(df.columns)

    if start_col not in cols or end_col not in cols:
        return []

    return cols[cols.index(start_col): cols.index(end_col) + 1]


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
                "border": 1,
            })

            for col_num, value in enumerate(data.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(
                    col_num,
                    col_num,
                    min(max(len(str(value)) + 2, 12), 45),
                )

            worksheet.autofilter(
                0,
                0,
                max(len(data), 1),
                max(len(data.columns) - 1, 0),
            )

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

    raw_df["IDELA_date_parsed"] = pd.to_datetime(
        raw_df["IDELA_date"],
        errors="coerce",
    )

    filtered_df = raw_df[
        raw_df["IDELA_date_parsed"].notna()
    ].drop(columns=["IDELA_date_parsed"]).copy()

    baseline_cols = find_range_columns(filtered_df, BASELINE_START, BASELINE_END)

    endline_cols = find_range_columns(filtered_df, ENDLINE_START, ENDLINE_END)

    all_question_cols = baseline_cols + endline_cols

    filtered_df = normalize_score_values(filtered_df, all_question_cols)

    filtered_df.insert(0, "Delete Action", "")

    filtered_df.insert(
        1,
        "baseline missing %",
        missing_pct(filtered_df, baseline_cols),
    )

    filtered_df.insert(
        2,
        "endline missing %",
        missing_pct(filtered_df, endline_cols),
    )

    st.subheader("2) Filtered on IDELA Date")

    st.write(f"Rows kept after IDELA_date validation: **{len(filtered_df)}**")

    high_missing = filtered_df[
        (filtered_df["baseline missing %"] > 0.30)
        | (filtered_df["endline missing %"] > 0.30)
    ].copy()

    st.warning(
        f"Rows with baseline or endline missing above 30%: {len(high_missing)}"
    )

    delete_indices = []

    if len(high_missing) > 0:
        st.write("Select rows to delete. Unselected rows will be kept.")

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

        display_cols += ["baseline missing %", "endline missing %"]

        edited = st.data_editor(
            high_missing_display[display_cols],
            use_container_width=True,
            hide_index=False,
            column_config={
                "baseline missing %": st.column_config.NumberColumn(
                    "baseline missing %",
                    format="%.1f%%",
                ),
                "endline missing %": st.column_config.NumberColumn(
                    "endline missing %",
                    format="%.1f%%",
                ),
            },
        )

        delete_indices = edited.index[
            edited["Select Delete"] == True
        ].tolist()

    clean_base = filtered_df.drop(index=delete_indices).copy()

    clean_base = clean_base.drop(
        columns=[
            "Delete Action",
            "baseline missing %",
            "endline missing %",
        ],
        errors="ignore",
    )

    st.subheader("3) Question Missing Review and Actions")

    actions = {}

    action_options = [
        "No action",
        "change missing to 0",
        "drop this question",
    ]

    if not baseline_cols:
        st.error("Baseline question columns were not found.")

    else:
        question_review_rows = []

        for base_col in baseline_cols:
            post_col = f"{base_col}_post"

            question_review_rows.append({
                "Baseline Question": base_col,
                "Endline Question": post_col if post_col in clean_base.columns else "",
                "Arabic Question": get_question_arabic(base_col),
                "English Question": get_question_english(base_col),
                "Baseline Missing %": question_missing_pct(clean_base, base_col) * 100,
                "Endline Missing %": (
                    question_missing_pct(clean_base, post_col) * 100
                    if post_col in clean_base.columns
                    else 0.0
                ),
                "Action": "No action",
            })

        question_review_df = pd.DataFrame(question_review_rows)

        edited_actions = st.data_editor(
            question_review_df,
            hide_index=True,
            use_container_width=True,
            column_order=[
                "Baseline Question",
                "Endline Question",
                "Arabic Question",
                "English Question",
                "Baseline Missing %",
                "Endline Missing %",
                "Action",
            ],
            column_config={
                "Arabic Question": st.column_config.TextColumn(
                    "Arabic Question",
                    width="large",
                ),
                "English Question": st.column_config.TextColumn(
                    "English Question",
                    width="large",
                ),
                "Baseline Missing %": st.column_config.ProgressColumn(
                    "Baseline Missing %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
                "Endline Missing %": st.column_config.ProgressColumn(
                    "Endline Missing %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
                "Action": st.column_config.SelectboxColumn(
                    "Action",
                    options=action_options,
                    required=True,
                ),
            },
        )

        actions = dict(zip(
            edited_actions["Baseline Question"],
            edited_actions["Action"],
        ))

        st.info(
            "If you choose 'drop this question', both the baseline question "
            "and its matching post/endline question are removed."
        )

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
        "IDELA ANALYSIS": pd.DataFrame(),
    }

    excel_bytes = to_excel_bytes(sheets)

    st.download_button(
        label="Download cleaned IDELA workbook",
        data=excel_bytes,
        file_name="idela_cleaned_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

else:
    st.info("Upload your Excel file to start.")
