import pandas as pd
import streamlit as st
from model import MU_BY_TYPE

TEXTS = {
    "RU": {
        "title": "Таблица μ по материалам и видам излучений (учебные)",
        "desc": "Значения условные и иллюстративные. Столбцы — виды излучений, строки — материалы.",
        "download": "Скачать таблицу как CSV"
    },
    "EN": {
        "title": "μ table by materials and radiation types (educational)",
        "desc": "Values are illustrative. Columns: radiation types; rows: materials.",
        "download": "Download table as CSV"
    }
}

def T(lang, key):
    return TEXTS.get(lang, TEXTS["RU"]).get(key, key)

st.set_page_config(page_title="μ Table", layout="wide")
lang = st.sidebar.selectbox("Язык / Language", ["RU", "EN"], index=0)

st.title(T(lang, "title"))
st.caption(T(lang, "desc"))

# Build dataframe: rows=materials (union across types), cols=types
types = list(MU_BY_TYPE.keys())
materials = sorted({m for t in types for m in MU_BY_TYPE[t].keys()})
data = {t: [MU_BY_TYPE[t].get(m, None) for m in materials] for t in types}
df = pd.DataFrame(data, index=materials)

st.dataframe(df, use_container_width=True)
st.download_button(T(lang, "download"), data=df.to_csv().encode("utf-8"),
                   file_name="mu_table.csv", mime="text/csv")
