import streamlit as st
from model import MATERIALS, MATERIAL_COSTS, ShieldLayer, dose

st.set_page_config(page_title="Стоимость vs Снижение D", layout="wide")
st.title("Финтех-расширение: стоимость экрана vs снижение D (учебно)")

st.sidebar.header("Исходные параметры")
k = st.sidebar.slider("Мощность источника k (отн.)", 0.1, 5.0, 1.0, 0.1)
r = st.sidebar.slider("Расстояние r (м)", 0.1, 10.0, 2.0, 0.1)

st.subheader("Настройка слоёв и цен (условные ед.)")
layers = []
mat_names = list(MATERIALS.keys())
for i in range(3):
    col = st.columns([2, 1, 1, 1])
    with col[0]:
        mat = st.selectbox(f"Материал слоя {i+1}", mat_names, index=i if i < len(mat_names) else 0, key=f"matF_{i}")
    with col[1]:
        th = st.number_input(f"Толщина {i+1} (см)", 0.0, 50.0, 0.0, 0.5, key=f"thF_{i}")
    with col[2]:
        default_cost = MATERIAL_COSTS.get(mat, 10.0)
        cost = st.number_input(f"Цена/см {i+1}", 0.0, 1000.0, float(default_cost), 1.0, key=f"costF_{i}")
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
    st.metric("Без экрана: D0", f"{D0:.4f}")
with colB:
    st.metric("С экраном: D", f"{D_with:.4f}")
with colC:
    st.metric("Снижение ΔD", f"{(D0 - D_with):.4f}")

st.metric("Итого стоимость экрана (условн.)", f"{cost_total:.2f}")

if cost_total > 0:
    bc = (D0 - D_with) / cost_total
    st.info(f"Показатель «снижение на единицу стоимости»: {bc:.6f}")
else:
    st.warning("Добавьте толщины или цену, чтобы рассчитать показатель.")
