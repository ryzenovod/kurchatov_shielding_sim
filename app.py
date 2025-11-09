import json, os, io
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from model import MATERIALS, ShieldLayer, dose, dose_curve, classify_zone
from retriever import QAIndex

# --- i18n ---
TEXTS = {
    "RU": {
        "page_title": "Экранирование и доза — симулятор",
        "sidebar_header": "Параметры источника и экрана",
        "k_label": "Мощность источника k (отн.)",
        "r_label": "Текущее расстояние r (м)",
        "D_safe_label": "Порог безопасной зоны D_safe (отн.)",
        "shielding_subheader": "Экранирование (до 3 слоёв)",
        "num_layers": "Число слоёв",
        "material_layer": "Материал слоя",
        "thickness_layer": "Толщина (см)",
        "scenarios_subheader": "Сценарии",
        "scenario_name": "Название сценария",
        "save_scenario": "Сохранить сценарий",
        "scenario_saved": "Сценарий сохранён в scenarios/my_scenarios.json",
        "scenario_save_error": "Ошибка сохранения",
        "current_point": "Текущая точка",
        "Dr_metric_label": "D(r) (отн.)",
        "zone_green": "Зелёная зона (≤ D_safe)",
        "zone_yellow": "Жёлтая зона (между D_safe и 3·D_safe)",
        "zone_red": "Красная зона (> 3·D_safe)",
        "caption_model": "Модель учебная: 1/r² · exp(−Σ μ·x). Коэффициенты и единицы — относительные.",
        "chart_title": "График D(r)",
        "ylog_checkbox": "Логарифмическая шкала по D",
        "export_png_button": "Скачать график D(r) как PNG",
        "export_png_unavailable": "Экспорт PNG недоступен",
        "export_csv_button": "Скачать данные D(r) как CSV",
        "ask_assistant_header": "Спросить ассистента (локальная база знаний)",
        "ask_placeholder": "Введите вопрос (пример: «Что такое правило время–расстояние–экранирование?»)",
        "assistant_empty": "База знаний не загружена или пуста.",
        "assistant_nearest_question": "Ближайший вопрос:",
        "assistant_similarity": "Сходство (TF-IDF)",
        "version_caption": "Версия каркаса: 1.2, экспорт PNG+CSV, RU/EN"
    },
    "EN": {
        "page_title": "Shielding & Dose — Simulator",
        "sidebar_header": "Source & Shielding Parameters",
        "k_label": "Source strength k (rel.)",
        "r_label": "Current distance r (m)",
        "D_safe_label": "Safe threshold D_safe (rel.)",
        "shielding_subheader": "Shielding (up to 3 layers)",
        "num_layers": "Number of layers",
        "material_layer": "Layer material",
        "thickness_layer": "Thickness (cm)",
        "scenarios_subheader": "Scenarios",
        "scenario_name": "Scenario name",
        "save_scenario": "Save scenario",
        "scenario_saved": "Scenario saved to scenarios/my_scenarios.json",
        "scenario_save_error": "Save error",
        "current_point": "Current point",
        "Dr_metric_label": "D(r) (rel.)",
        "zone_green": "Green zone (≤ D_safe)",
        "zone_yellow": "Yellow zone (between D_safe and 3·D_safe)",
        "zone_red": "Red zone (> 3·D_safe)",
        "caption_model": "Educational model: 1/r² · exp(−Σ μ·x). Coefficients and units are relative.",
        "chart_title": "D(r) curve",
        "ylog_checkbox": "Logarithmic scale for D",
        "export_png_button": "Download D(r) chart as PNG",
        "export_png_unavailable": "PNG export not available",
        "export_csv_button": "Download D(r) data as CSV",
        "ask_assistant_header": "Ask the assistant (offline knowledge base)",
        "ask_placeholder": "Type a question (e.g., “What is time–distance–shielding rule?”)",
        "assistant_empty": "Knowledge base is not loaded or empty.",
        "assistant_nearest_question": "Nearest question:",
        "assistant_similarity": "Similarity (TF-IDF)",
        "version_caption": "Framework version: 1.2, PNG+CSV export, RU/EN"
    }
}

def T(lang, key):
    return TEXTS.get(lang, TEXTS["RU"]).get(key, key)

# --- Page config & language switch ---
st.set_page_config(page_title="Shielding Simulator", layout="wide")
lang = st.sidebar.selectbox("Язык / Language", ["RU", "EN"], index=0)

@st.cache_resource
def load_qa_index():
    try:
        return QAIndex.from_csv("data/qa.csv")
    except Exception:
        return QAIndex([])

qa_index = load_qa_index()

# --- Sidebar ---
st.sidebar.header(T(lang, "sidebar_header"))

k = st.sidebar.slider(T(lang, "k_label"), 0.1, 5.0, 1.0, 0.1)
r_current = st.sidebar.slider(T(lang, "r_label"), 0.1, 10.0, 2.0, 0.1)
D_safe = st.sidebar.slider(T(lang, "D_safe_label"), 0.01, 1.0, 0.2, 0.01)

st.sidebar.subheader(T(lang, "shielding_subheader"))
layers = []
layer_count = st.sidebar.number_input(T(lang, "num_layers"), 0, 3, 1, 1)
mat_names = list(MATERIALS.keys())
for i in range(int(layer_count)):
    col1, col2 = st.sidebar.columns(2)
    with col1:
        mat = st.selectbox(f"{T(lang, 'material_layer')} {i+1}", mat_names, key=f"mat_{i}")
    with col2:
        th = st.number_input(f"{T(lang, 'thickness_layer')} {i+1}", 0.0, 50.0, 0.0, 0.5, key=f"th_{i}")
    layers.append(ShieldLayer(material=mat, thickness_cm=th))

st.sidebar.divider()
st.sidebar.subheader(T(lang, "scenarios_subheader"))
scenario_name = st.sidebar.text_input(T(lang, "scenario_name"), value="Сценарий 1" if lang=="RU" else "Scenario 1")
if st.sidebar.button(T(lang, "save_scenario")):
    payload = {
        "k": float(k),
        "r_current": float(r_current),
        "D_safe": float(D_safe),
        "layers": [{"material": L.material, "thickness_cm": float(L.thickness_cm)} for L in layers],
        "lang": lang
    }
    try:
        os_path = "scenarios/my_scenarios.json"
        try:
            with open(os_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        data[scenario_name] = payload
        with open(os_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        st.sidebar.success(T(lang, "scenario_saved"))
    except Exception as e:
        st.sidebar.error(f"{T(lang, 'scenario_save_error')}: {e}")

# --- Main ---
colA, colB = st.columns([1, 2])

with colA:
    D_now = dose(k, r_current, layers)
    zone = classify_zone(D_now, D_safe)
    st.markdown("### " + T(lang, "current_point"))
    st.metric(label=T(lang, "Dr_metric_label"), value=f"{D_now:.3f}")
    if zone == "green":
        st.success(T(lang, "zone_green"))
    elif zone == "yellow":
        st.warning(T(lang, "zone_yellow"))
    else:
        st.error(T(lang, "zone_red"))
    st.caption(T(lang, "caption_model"))

with colB:
    st.markdown("### " + T(lang, "chart_title"))
    r_min, r_max = 0.1, 10.0
    r, d = dose_curve(k, layers, r_min, r_max, num=400)
    ylog = st.checkbox(T(lang, "ylog_checkbox"), value=False)
    fig = go.Figure()
    fig.add_scatter(x=r, y=d, mode="lines", name="D(r)")
    fig.add_hline(y=D_safe, line_dash="dot", annotation_text="D_safe")
    fig.update_layout(xaxis_title="r (m)" if lang=="EN" else "Расстояние r (м)",
                      yaxis_title="Dose rate D (rel.)" if lang=="EN" else "Относительная мощность дозы D")
    if ylog:
        fig.update_yaxes(type="log", exponentformat="power")
    st.plotly_chart(fig, use_container_width=True)
    # PNG export
    try:
        png_bytes = fig.to_image(format="png", scale=2)
        st.download_button(T(lang, "export_png_button"), data=png_bytes,
                           file_name="dose_curve.png", mime="image/png")
    except Exception as e:
        st.caption(f"{T(lang, 'export_png_unavailable')}: {e}")
    # CSV export
    df = pd.DataFrame({"r": r, "D": d})
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(T(lang, "export_csv_button"), data=csv_bytes,
                       file_name="dose_curve.csv", mime="text/csv")

st.divider()
st.markdown("## " + T(lang, "ask_assistant_header"))
query = st.text_input(T(lang, "ask_placeholder"))
if query:
    answers = qa_index.ask(query, topk=1)
    if not answers:
        st.info(T(lang, "assistant_empty"))
    else:
        q, a, sim = answers[0]
        st.markdown(f"**{T(lang, 'assistant_nearest_question')}** {q}")
        st.markdown(a)
        st.caption(f"{T(lang, 'assistant_similarity')}: {sim:.2f}")

st.caption(T(lang, "version_caption"))
