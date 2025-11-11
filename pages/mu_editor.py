import json, os
import pandas as pd
import streamlit as st
from model import MU_BY_TYPE, MU_ACTIVE

TEXTS = {
    "RU": {
        "title": "Редактор μ (учебные коэффициенты ослабления)",
        "desc": "Правьте значения и сохраняйте в пользовательский пресет. Сохранённые μ применяются во всех расчётах.",
        "edit_label": "Редактируемая таблица μ",
        "save": "Сохранить пресет",
        "reset": "Сбросить пресет",
        "saved": "Сохранено в data/mu_override.json",
        "reset_ok": "Пользовательский пресет удалён, используются значения по умолчанию.",
        "warn": "Значения учебные; вводите неотрицательные числа. При ошибке загрузки используются значения по умолчанию.",
        "presets": "Горячие пресеты",
        "preset_default": "Заводские (по умолчанию)",
        "preset_gamma": "Гамма‑жёсткие (усилить металлы)",
        "preset_neutron": "Нейтрон‑оптимизированные (усилить воду/бетон)",
        "preset_beta": "Бета‑безопасные (усилить низко‑Z, ослабить металлы)",
        "preset_alpha": "Альфа‑суперпорог (очень высокие μ)",
        "confirm": "Я понимаю, что перезаписываю пользовательский пресет",
        "need_confirm": "Подтвердите флажком перед сохранением."
    },
    "EN": {
        "title": "μ Editor (educational attenuation coefficients)",
        "desc": "Edit values and save as a user preset. Saved μ are used across all pages.",
        "edit_label": "Editable μ table",
        "save": "Save preset",
        "reset": "Reset preset",
        "saved": "Saved to data/mu_override.json",
        "reset_ok": "User preset removed; defaults are used.",
        "warn": "Values are educational; enter non‑negative numbers. On load error, defaults are used.",
        "presets": "Hot presets",
        "preset_default": "Factory defaults",
        "preset_gamma": "Gamma‑hard (boost metals)",
        "preset_neutron": "Neutron‑optimized (boost water/concrete)",
        "preset_beta": "Beta‑safe (boost low‑Z, reduce metals)",
        "preset_alpha": "Alpha‑super‑threshold (very high μ)",
        "confirm": "I understand this will overwrite the user preset",
        "need_confirm": "Please check the confirmation box before saving."
    }
}

def T(lang, key):
    return TEXTS.get(lang, TEXTS["RU"]).get(key, key)

st.set_page_config(page_title="μ Editor", layout="wide")
lang = st.sidebar.selectbox("Язык / Language", ["RU", "EN"], index=0)

st.title(T(lang, "title"))
st.caption(T(lang, "desc"))
st.warning(T(lang, "warn"))

types = sorted(set(MU_ACTIVE.keys()) | set(MU_BY_TYPE.keys()))
materials = sorted({m for t in types for m in MU_ACTIVE.get(t, {}).keys() | MU_BY_TYPE.get(t, {}).keys()})

# Build table from MU_ACTIVE (includes overrides)
data = {t: [MU_ACTIVE.get(t, {}).get(m, None) for m in materials] for t in types}
df = pd.DataFrame(data, index=materials)

st.subheader(T(lang, "presets"))
c1, c2, c3, c4, c5 = st.columns(5)
preset_choice = st.session_state.get("mu_preset_choice", "none")

def apply_preset(name: str):
    # Start from factory defaults
    base = {t: MU_BY_TYPE.get(t, {}).copy() for t in types}
    if name == "gamma":
        # boost metal μ for Gamma; slight reduce others for Gamma
        if "Гамма" in base:
            for mat in base["Гамма"]:
                if mat in ("Свинец", "Сталь"):
                    base["Гамма"][mat] = round(base["Гамма"][mat] * 1.25, 3)
                else:
                    base["Гамма"][mat] = round(base["Гамма"][mat] * 0.9, 3)
    elif name == "neutron":
        if "Нейтроны" in base:
            for mat in base["Нейтроны"]:
                if mat in ("Вода", "Бетон"):
                    base["Нейтроны"][mat] = round(base["Нейтроны"][mat] * 1.3, 3)
                else:
                    base["Нейтроны"][mat] = round(base["Нейтроны"][mat] * 0.9, 3)
    elif name == "beta":
        if "Бета" in base:
            for mat in base["Бета"]:
                if mat in ("Стекло/акрил", "Вода", "Бетон"):
                    base["Бета"][mat] = round(base["Бета"][mat] * 1.25, 3)
                else:
                    base["Бета"][mat] = round(base["Бета"][mat] * 0.8, 3)
    elif name == "alpha":
        if "Альфа" in base:
            for mat in base["Альфа"]:
                base["Альфа"][mat] = round(base["Альфа"][mat] * 2.0, 3)
        if "Нейтроны" in base:
            for mat in base["Нейтроны"]:
                if mat in ("Вода", "Бетон"):
                    base["Нейтроны"][mat] = round(base["Нейтроны"][mat] * 1.3, 3)
                else:
                    base["Нейтроны"][mat] = round(base["Нейтроны"][mat] * 0.9, 3)
    # Convert to DataFrame aligned to current materials/types
    return pd.DataFrame({t: [base.get(t, {}).get(m, None) for m in materials] for t in types}, index=materials)

with c1:
    if st.button(T(lang, "preset_default")):
        st.session_state["mu_preset_choice"] = "default"
        df = pd.DataFrame({t: [MU_BY_TYPE.get(t, {}).get(m, None) for m in materials] for t in types}, index=materials)
with c2:
    if st.button(T(lang, "preset_gamma")):
        st.session_state["mu_preset_choice"] = "gamma"
        df = apply_preset("gamma")
with c3:
    if st.button(T(lang, "preset_neutron")):
        st.session_state["mu_preset_choice"] = "neutron"
        df = apply_preset("neutron")
with c4:
    if st.button(T(lang, "preset_beta")):
        st.session_state["mu_preset_choice"] = "beta"
        df = apply_preset("beta")
with c5:
    if st.button(T(lang, "preset_alpha")):
        st.session_state["mu_preset_choice"] = "alpha"
        df = apply_preset("alpha")

st.subheader(T(lang, "edit_label"))
edited = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="mu_editor")

confirm = st.checkbox(T(lang, "confirm"))

col1, col2 = st.columns(2)
with col1:
    if st.button(T(lang, "save")):
        if not confirm:
            st.error(T(lang, "need_confirm"))
        else:
            out = {t: {} for t in edited.columns}
            for m in edited.index:
                for t in edited.columns:
                    val = edited.loc[m, t]
                    if pd.notna(val):
                        try:
                            valf = float(val)
                            if valf < 0: valf = 0.0
                            out[t][m] = valf
                        except Exception:
                            pass
            os.makedirs("data", exist_ok=True)
            with open("data/mu_override.json", "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            st.success(T(lang, "saved"))
with col2:
    if st.button(T(lang, "reset")):
        try:
            os.remove("data/mu_override.json")
        except FileNotFoundError:
            pass
        st.info(T(lang, "reset_ok"))
