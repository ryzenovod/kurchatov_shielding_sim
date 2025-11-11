import json
import streamlit as st

TEXTS = {
    "RU": {
        "title": "Квиз: радиационная безопасность (учебно)",
        "choose": "Выберите ответ",
        "check": "Проверить",
        "correct": "верно — {ans}",
        "wrong": "неверно. Правильно: {ans}",
        "result": "Итог: {score} / {total}"
    },
    "EN": {
        "title": "Quiz: radiation safety (educational)",
        "choose": "Choose one",
        "check": "Check",
        "correct": "correct — {ans}",
        "wrong": "wrong. Correct: {ans}",
        "result": "Score: {score} / {total}"
    }
}

def T(lang, key):
    return TEXTS.get(lang, TEXTS["RU"]).get(key, key)

st.set_page_config(page_title="Quiz", layout="centered")
lang = st.sidebar.selectbox("Язык / Language", ["RU", "EN"], index=0)

st.title(T(lang, "title"))

@st.cache_resource
def load_quiz(lang):
    path = "data/quiz_en.json" if lang=="EN" else "data/quiz.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

quiz = load_quiz(lang)
score = 0
answers_user = []

for i, q in enumerate(quiz["questions"], start=1):
    st.subheader(f"Q{i}" if lang=="EN" else f"Вопрос {i}")
    st.markdown(q["text"])
    choice = st.radio(T(lang, "choose"), q["options"], index=None, key=f"q{i}")
    answers_user.append(choice)

if st.button(T(lang, "check")):
    st.divider()
    for i, q in enumerate(quiz["questions"], start=1):
        correct = q["answer"]
        user = answers_user[i-1]
        if user == correct:
            st.success((T(lang, "correct")).format(ans=correct))
            score += 1
        else:
            st.error((T(lang, "wrong")).format(ans=correct))
        st.caption(q["explain"])
    st.info((T(lang, "result")).format(score=score, total=len(quiz['questions'])))
