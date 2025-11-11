import streamlit as st
from model import MATERIALS, MATERIAL_COSTS, ShieldLayer, dose

TEXTS = {
    "RU": {
        "page_title": "Стоимость vs Снижение D",
        "title": "Финтех-расширение: стоимость экрана vs снижение D (учебно)",
        "sidebar_header": "Исходные параметры",
        "k_label": "Мощность источника k (отн.)",
        "r_label": "Расстояние r (м)",
        "layers_title": "Настройка слоёв и цен (условные ед.)",
        "material": "Материал слоя",
        "thickness": "Толщина (см)",
        "price": "Цена/см",
        "no_shield": "Без экрана: D0",
        "with_shield": "С экраном: D",
        "delta": "Снижение ΔD",
        "total_cost": "Итого стоимость экрана (условн.)",
        "bc": "Показатель «снижение на единицу стоимости»: {v:.6f}",
        "need_values": "Добавьте толщины или цену, чтобы рассчитать показатель."
    },
    "EN": {
        "page_title": "Cost vs ΔDose",
        "title": "Fintech extension: cost of shielding vs ΔD (educational)",
        "sidebar_header": "Parameters",
        "k_label": "Source strength k (rel.)",
        "r_label": "Distance r (m)",
        "layers_title": "Layers & prices (unit costs)",
        "material": "Layer material",
        "thickness": "Thickness (cm)",
        "price": "Price/cm",
        "no_shield": "No shield: D0",
        "with_shield": "With shield: D",
        "delta": "Reduction ΔD",
        "total_cost": "Total cost (units)",
        "bc": "Benefit per cost: {v:.6f}",
        "need_values": "Add thickness/prices to compute the metric."
    }
}

def T(lang, key):
    return TEXTS.get(lang, TEXTS["RU"]).get(key, key)

st.set_page_config(page_title="Cost vs ΔD", layout="wide")
lang = st.sidebar.selectbox("Язык / Language", ["RU", "EN"], index=0)

st.title(T(lang, "title"))

st.sidebar.header(T(lang, "sidebar_header"))
k = st.sidebar.slider(T(lang, "k_label"), 0.1, 5.0, 1.0, 0.1)
r = st.sidebar.slider(T(lang, "r_label"), 0.1, 10.0, 2.0, 0.1)

st.subheader(T(lang, "layers_title"))
layers = []
mat_names = list(MATERIALS.keys())
for i in range(3):
    col = st.columns([2, 1, 1, 1])
    with col[0]:
        mat = st.selectbox(f"{T(lang, 'material')} {i+1}", mat_names, index=i if i < len(mat_names) else 0, key=f"matF_{i}")
    with col[1]:
        th = st.number_input(f"{T(lang, 'thickness')} {i+1}", 0.0, 50.0, 0.0, 0.5, key=f"thF_{i}")
    with col[2]:
        default_cost = MATERIAL_COSTS.get(mat, 10.0)
        cost = st.number_input(f"{T(lang, 'price')} {i+1}", 0.0, 1000.0, float(default_cost), 1.0, key=f"costF_{i}")
    with col[3]:
        st.caption(" ")
    layers.append(ShieldLayer(mat, th))

D0 = dose(k, r, [])
D_with = dose(k, r, layers)
cost_total = 0.0
for L in layers:
    if L.thickness_cm > 0:
        unit = MATERIAL_COSTS.get(L.material, 10.0)
        cost_total += unit * L.thickness_cm

colA, colB, colC = st.columns(3)
with colA:
    st.metric(T(lang, "no_shield"), f"{D0:.4f}")
with colB:
    st.metric(T(lang, "with_shield"), f"{D_with:.4f}")
with colC:
    st.metric(T(lang, "delta"), f"{(D0 - D_with):.4f}")

st.metric(T(lang, "total_cost"), f"{cost_total:.2f}")

if cost_total > 0:
    bc = (D0 - D_with) / cost_total
    st.info(T(lang, "bc").format(v=bc))
else:
    st.warning(T(lang, "need_values"))
