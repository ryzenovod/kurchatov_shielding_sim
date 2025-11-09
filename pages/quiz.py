import json
import streamlit as st

st.set_page_config(page_title="Проверь себя", layout="centered")

st.title("Квиз: радиационная безопасность (учебно)")

@st.cache_resource
def load_quiz():
    with open("data/quiz.json", "r", encoding="utf-8") as f:
        return json.load(f)

quiz = load_quiz()
score = 0
answers_user = []

for i, q in enumerate(quiz["questions"], start=1):
    st.subheader(f"Вопрос {i}")
    st.markdown(q["text"])
    choice = st.radio("Выберите ответ", q["options"], index=None, key=f"q{i}")
    answers_user.append(choice)

if st.button("Проверить"):
    st.divider()
    for i, q in enumerate(quiz["questions"], start=1):
        correct = q["answer"]
        user = answers_user[i-1]
        if user == correct:
            score += 1
            st.success(f"Вопрос {i}: верно — {correct}")
        else:
            st.error(f"Вопрос {i}: неверно. Правильно: {correct}")
        st.caption(q["explain"])
    st.info(f"Итог: {score} / {len(quiz['questions'])}")
