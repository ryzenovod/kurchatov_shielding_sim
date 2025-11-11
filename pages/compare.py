import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from model import ShieldLayer, dose_curve

TEXTS = {
    "RU": {
        "page_title": "Сравнение сценариев",
        "title": "Сравнение двух сценариев",
        "need_two": "Нужно минимум два сохранённых сценария в файле scenarios/my_scenarios.json (создайте их на главной странице).",
        "scenario_A": "Сценарий A",
        "scenario_B": "Сценарий B",
        "ylog": "Логарифмическая шкала по D",
        "export_png": "Скачать сравнение как PNG",
        "png_unavailable": "Экспорт PNG недоступен",
        "probe": "Проверочное расстояние r_probe (м)",
        "metricA": "D_A(r={r:.2f})",
        "metricB": "D_B(r={r:.2f})",
        "export_csv": "Скачать данные сравнения как CSV"
    },
    "EN": {
        "page_title": "Scenario Comparison",
        "title": "Compare two scenarios",
        "need_two": "At least two saved scenarios are required in scenarios/my_scenarios.json (create them on the main page).",
        "scenario_A": "Scenario A",
        "scenario_B": "Scenario B",
        "ylog": "Logarithmic scale for D",
        "export_png": "Download comparison as PNG",
        "png_unavailable": "PNG export not available",
        "probe": "Probe distance r_probe (m)",
        "metricA": "D_A(r={r:.2f})",
        "metricB": "D_B(r={r:.2f})",
        "export_csv": "Download comparison data as CSV"
    }
}

def T(lang, key):
    return TEXTS.get(lang, TEXTS["RU"]).get(key, key)

st.set_page_config(page_title="Comparison", layout="wide")
lang = st.sidebar.selectbox("Язык / Language", ["RU", "EN"], index=0)

st.title(T(lang, "title"))

def load_scenarios(path="scenarios/my_scenarios.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

sc = load_scenarios()
names = sorted(sc.keys())

if len(names) < 2:
    st.info(T(lang, "need_two"))
else:
    col1, col2 = st.columns(2)
    with col1:
        n1 = st.selectbox(T(lang, "scenario_A"), names, index=0)
    with col2:
        n2 = st.selectbox(T(lang, "scenario_B"), names, index=1 if len(names) > 1 else 0)

    def mk_layers(raw):
        return [ShieldLayer(material=L['material'], thickness_cm=float(L['thickness_cm'])) for L in raw]

    A = sc[n1]; B = sc[n2]
    # Metadata
    metaA = {k: A.get(k) for k in ["radiation_type", "author", "note", "saved_at"]}
    metaB = {k: B.get(k) for k in ["radiation_type", "author", "note", "saved_at"]}
    st.caption(f"A: type={metaA.get('radiation_type')}, author={metaA.get('author')}, saved_at={metaA.get('saved_at')}")
    if metaA.get("note"):
        st.caption(f"A note: {metaA.get('note')}")
    st.caption(f"B: type={metaB.get('radiation_type')}, author={metaB.get('author')}, saved_at={metaB.get('saved_at')}")
    if metaB.get("note"):
        st.caption(f"B note: {metaB.get('note')}")
    layersA = mk_layers(A["layers"]); layersB = mk_layers(B["layers"])
    rA, dA = dose_curve(A["k"], layersA, 0.1, 10.0, num=400, radiation_type=A.get("radiation_type", "Гамма"))
    rB, dB = dose_curve(B["k"], layersB, 0.1, 10.0, num=400, radiation_type=B.get("radiation_type", "Гамма"))

    fig = go.Figure()
    fig.add_scatter(x=rA, y=dA, mode="lines", name=f"{n1}")
    fig.add_scatter(x=rB, y=dB, mode="lines", name=f"{n2}")
    fig.add_hline(y=A["D_safe"], line_dash="dot", annotation_text="D_safe (A)")
    fig.update_layout(xaxis_title="r (m)" if lang=="EN" else "r (м)",
                      yaxis_title="Dose rate D (rel.)" if lang=="EN" else "D (отн.)")
    ylog = st.checkbox(T(lang, "ylog"), value=True)
    if ylog:
        fig.update_yaxes(type="log", exponentformat="power")
    st.plotly_chart(fig, use_container_width=True)

    # PNG export
    try:
        png_bytes = fig.to_image(format="png", scale=2)
        st.download_button(T(lang, "export_png"), data=png_bytes, file_name="comparison.png", mime="image/png")
    except Exception as e:
        st.caption(f"{T(lang, 'png_unavailable')}: {e}")

    # CSV export on rA grid
    df = pd.DataFrame({"r": rA, f"D_{n1}": dA})
    def interp(r_arr, d_arr, r):
        i = int(np.clip(np.searchsorted(r_arr, r), 0, len(r_arr)-1))
        return float(d_arr[i])
    df[f"D_{n2}"] = [interp(rB, dB, rv) for rv in rA]
    st.download_button(T(lang, "export_csv"), data=df.to_csv(index=False).encode("utf-8"),
                       file_name="comparison.csv", mime="text/csv")

    r_probe = st.slider(T(lang, "probe"), 0.1, 10.0, 2.0, 0.1)
    def interp_val(r_arr, d_arr, r):
        i = int(np.clip(np.searchsorted(r_arr, r), 0, len(r_arr)-1))
        return float(d_arr[i])
    dA_probe = interp_val(rA, dA, r_probe)
    dB_probe = interp_val(rB, dB, r_probe)

    colm = st.columns(2)
    with colm[0]:
        st.metric(T(lang, "metricA").format(r=r_probe), f"{dA_probe:.4f}")
    with colm[1]:
        st.metric(T(lang, "metricB").format(r=r_probe), f"{dB_probe:.4f}")
