import io, json, zipfile
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from model import ShieldLayer, dose_curve

TEXTS = {
    "RU": {
        "title": "Экспорт пакета артефактов (PNG+CSV)",
        "desc": "Соберите ZIP с графиками и данными для выбранных сценариев. Если выбрать 2 сценария — будет добавлено сравнение.",
        "pick": "Выберите 1–2 сценария",
        "make": "Сформировать ZIP",
        "ok": "Готово: сформирован ZIP с {n} файлами.",
        "include_mu": "Добавить таблицу μ (CSV)",
        "include_override": "Добавить текущий пресет μ (mu_override.json, если есть)"
    },
    "EN": {
        "title": "Export bundle (PNG+CSV)",
        "desc": "Build a ZIP with charts and data for selected scenarios. If you select 2 scenarios, a comparison is added.",
        "pick": "Select 1–2 scenarios",
        "make": "Build ZIP",
        "ok": "Done: ZIP with {n} files created.",
        "include_mu": "Include μ table (CSV)",
        "include_override": "Include current μ preset (mu_override.json, if present)"
    }
}

def T(lang, key):
    return TEXTS.get(lang, TEXTS["RU"]).get(key, key)

st.set_page_config(page_title="Export bundle", layout="wide")
lang = st.sidebar.selectbox("Язык / Language", ["RU", "EN"], index=0)

st.title(T(lang, "title"))
st.caption(T(lang, "desc"))

# Load scenarios
import os, json
os.makedirs("scenarios", exist_ok=True)
path = "scenarios/my_scenarios.json"
try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    data = {}

names = sorted(list(data.keys()))
sel = st.multiselect(T(lang, "pick"), names, max_selections=2)

inc_mu = st.checkbox(T(lang, "include_mu"), value=True)
inc_override = st.checkbox(T(lang, "include_override"), value=True)

def mk_layers(raw):
    return [ShieldLayer(material=L['material'], thickness_cm=float(L['thickness_cm'])) for L in raw]

def make_curve_png_csv(name: str, sc: dict):
    layers = mk_layers(sc["layers"])
    r, d = dose_curve(sc["k"], layers, 0.1, 10.0, num=400, radiation_type=sc.get("radiation_type", "Гамма"))
    # CSV
    df = pd.DataFrame({"r": r, "D": d})
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    # PNG
    fig = go.Figure()
    meta = {
        'type': sc.get('radiation_type', 'Гамма'),
        'author': sc.get('author', ''),
        'saved': sc.get('saved_at', ''),
        'note': sc.get('note', '')
    }
    legend_name = f"{name} [{meta['type']}]"
    fig.add_scatter(x=r, y=d, mode="lines", name=legend_name)
    fig.add_hline(y=sc["D_safe"], line_dash="dot", annotation_text="D_safe")
    title_txt = f"{name} — {meta['type']}" + (f" | {meta['author']}" if meta['author'] else "") + (f" | {meta['saved']}" if meta['saved'] else "")
    fig.update_layout(title=title_txt,
                      xaxis_title="r (m)" if lang=="EN" else "r (м)",
                      yaxis_title="Dose rate D (rel.)" if lang=="EN" else "D (отн.)",
                      margin=dict(t=90))
    if meta['note']:
        fig.add_annotation(xref="paper", yref="paper", x=0, y=1.12, showarrow=False,
                           text=(meta['note'][:120] + ('…' if len(meta['note'])>120 else '')))
    png_bytes = fig.to_image(format="png", scale=2)
    return csv_bytes, png_bytes

def make_compare_png_csv(nameA, scA, nameB, scB):
    layersA = mk_layers(scA["layers"]); layersB = mk_layers(scB["layers"])
    rA, dA = dose_curve(scA["k"], layersA, 0.1, 10.0, num=400, radiation_type=scA.get("radiation_type", "Гамма"))
    rB, dB = dose_curve(scB["k"], layersB, 0.1, 10.0, num=400, radiation_type=scB.get("radiation_type", "Гамма"))
    # CSV on rA grid
    def interp(r_arr, d_arr, r):
        i = int(np.clip(np.searchsorted(r_arr, r), 0, len(r_arr)-1))
        return float(d_arr[i])
    df = pd.DataFrame({"r": rA, f"D_{nameA}": dA, f"D_{nameB}": [interp(rB, dB, rv) for rv in rA]})
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    # PNG
    fig = go.Figure()
    fig.add_scatter(x=rA, y=dA, mode="lines", name=nameA)
    fig.add_scatter(x=rB, y=dB, mode="lines", name=nameB)
    fig.add_hline(y=scA["D_safe"], line_dash="dot", annotation_text="D_safe (A)")
    fig.update_layout(xaxis_title="r (m)" if lang=="EN" else "r (м)",
                      yaxis_title="Dose rate D (rel.)" if lang=="EN" else "D (отн.)")
    png_bytes = fig.to_image(format="png", scale=2)
    return csv_bytes, png_bytes

if st.button(T(lang, "make")) and sel:
    files = []
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        # Per‑scenario artifacts
        for name in sel:
            sc = data[name]
            csv_b, png_b = make_curve_png_csv(name, sc)
            safe_name = name.replace("/", "_").replace("\\", "_")
            zf.writestr(f"{safe_name}/curve.csv", csv_b)
            zf.writestr(f"{safe_name}/curve.png", png_b)
            files += [f"{safe_name}/curve.csv", f"{safe_name}/curve.png"]
        # Comparison if two selected
        if len(sel) == 2:
            a, b = sel
            scA, scB = data[a], data[b]
            csv_b, png_b = make_compare_png_csv(a, scA, b, scB)
            zf.writestr(f"{a}_VS_{b}/comparison.csv", csv_b)
            zf.writestr(f"{a}_VS_{b}/comparison.png", png_b)
            files += [f"{a}_VS_{b}/comparison.csv", f"{a}_VS_{b}/comparison.png"]
        # μ table and override
        if inc_mu:
            # Build merged μ active table in CSV via model import
            from model import MU_ACTIVE
            types = list(MU_ACTIVE.keys())
            mats = sorted({m for t in types for m in MU_ACTIVE[t].keys()})
            df_mu = pd.DataFrame({t: [MU_ACTIVE[t].get(m, None) for m in mats] for t in types}, index=mats)
            zf.writestr("mu_table.csv", df_mu.to_csv().encode("utf-8"))
            files.append("mu_table.csv")
        if inc_override and os.path.exists("data/mu_override.json"):
            with open("data/mu_override.json", "rb") as f:
                zf.writestr("mu_override.json", f.read())
            files.append("mu_override.json")
    mem.seek(0)
    st.success(T(lang, "ok").format(n=len(files)))
    st.download_button("Download ZIP", data=mem, file_name="bundle.zip", mime="application/zip")
