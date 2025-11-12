import json, os
import math
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from datetime import datetime
import numpy as np
from model import (
    MATERIALS,
    ShieldLayer,
    dose,
    dose_curve,
    classify_zone,
    _mu_for,
    DANGEROUS_COMBINATIONS,
)
from retriever import QAIndex

TEXTS = {
    "RU": {
        "page_title": "Экранирование и доза — симулятор",
        "language_selector": "Язык / Language",
        "sidebar_header": "Параметры источника и экрана",
        "k_label": "Мощность источника k (отн.)",
        "r_label": "Текущее расстояние r (м)",
        "D_safe_label": "Порог безопасной зоны D_safe (отн.)",
        "rad_type": "Вид излучения",
        "shielding_subheader": "Экранирование (до 3 слоёв)",
        "num_layers": "Число слоёв",
        "material_layer": "Материал слоя",
        "thickness_layer": "Толщина (см)",
        "scenarios_subheader": "Сценарии",
        "scenario_name": "Название сценария",
        "author_label": "Автор",
        "note_label": "Заметка",
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
        "formula_section": "Интерактивная формула",
        "formula_description": "Изменяйте параметры модели и мгновенно обновляйте график D(r).",
        "formula_k_label": "Мощность источника k",
        "formula_r_label": "Текущее расстояние r",
        "formula_eval_label": "r для расчёта D(r)",
        "formula_result_label": "Расчётное значение D(r)",
        "formula_mu_label": "Суммарное ослабление",
        "material_visualization_title": "Визуализация слоёв",
        "material_visualization_caption": "Слои экрана отображаются по толщине (см).",
        "material_visualization_empty": "Добавьте слой, чтобы увидеть визуализацию.",
        "rad_animation_title": "Анимация излучения",
        "rad_animation_caption": "Наглядная схема прохождения выбранного излучения сквозь экран.",
        "recommendations_header": "Рекомендации по толщине материалов",
        "recommendations_caption": "Толщина для достижения безопасной дозы на текущем расстоянии.",
        "recommendations_material": "Материал",
        "recommendations_thickness": "Толщина (см)",
        "recommendations_not_needed": "Дополнительное экранирование не требуется",
        "safety_header": "Предупреждения по безопасности",
        "safety_warning_prefix": "Внимание:",
        "dangerous_combination_intro": "Проверьте совместимость выбранных материалов.",
        "ask_assistant_header": "Спросить ассистента (локальная база знаний)",
        "ask_placeholder": "Введите вопрос (пример: «Что такое правило время–расстояние–экранирование?»)",
        "assistant_empty": "База знаний не загружена или пуста.",
        "assistant_nearest_question": "Ближайший вопрос:",
        "assistant_similarity": "Сходство (TF-IDF)",
        "version_caption": "Версия каркаса: 1.4, интерактивная формула, визуализации, RU/EN/ZH"
    },
    "EN": {
        "page_title": "Shielding & Dose — Simulator",
        "language_selector": "Language",
        "sidebar_header": "Source & Shielding Parameters",
        "k_label": "Source strength k (rel.)",
        "r_label": "Current distance r (m)",
        "D_safe_label": "Safe threshold D_safe (rel.)",
        "rad_type": "Radiation type",
        "shielding_subheader": "Shielding (up to 3 layers)",
        "num_layers": "Number of layers",
        "material_layer": "Layer material",
        "thickness_layer": "Thickness (cm)",
        "scenarios_subheader": "Scenarios",
        "scenario_name": "Scenario name",
        "author_label": "Author",
        "note_label": "Note",
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
        "formula_section": "Interactive formula",
        "formula_description": "Adjust the model parameters to update the D(r) curve instantly.",
        "formula_k_label": "Source strength k",
        "formula_r_label": "Current distance r",
        "formula_eval_label": "r used for D(r)",
        "formula_result_label": "Computed D(r)",
        "formula_mu_label": "Total attenuation",
        "material_visualization_title": "Layer visualization",
        "material_visualization_caption": "Shield layers are scaled by their thickness (cm).",
        "material_visualization_empty": "Add a layer to see the visualization.",
        "rad_animation_title": "Radiation animation",
        "rad_animation_caption": "Animated path of the selected radiation through the shield.",
        "recommendations_header": "Material thickness recommendations",
        "recommendations_caption": "Thickness needed to reach the safe dose at the current distance.",
        "recommendations_material": "Material",
        "recommendations_thickness": "Thickness (cm)",
        "recommendations_not_needed": "No extra shielding required",
        "safety_header": "Safety warnings",
        "safety_warning_prefix": "Caution:",
        "dangerous_combination_intro": "Verify compatibility of the chosen materials.",
        "ask_assistant_header": "Ask the assistant (offline knowledge base)",
        "ask_placeholder": "Type a question (e.g., “What is time–distance–shielding rule?”)",
        "assistant_empty": "Knowledge base is not loaded or empty.",
        "assistant_nearest_question": "Nearest question:",
        "assistant_similarity": "Similarity (TF-IDF)",
        "version_caption": "Framework version: 1.4, interactive formula, visualizations, RU/EN/ZH"
    },
    "ZH": {
        "page_title": "屏蔽与剂量模拟器",
        "language_selector": "语言",
        "sidebar_header": "源与屏蔽参数",
        "k_label": "源强 k (相对)",
        "r_label": "当前距离 r (米)",
        "D_safe_label": "安全阈值 D_safe (相对)",
        "rad_type": "辐射类型",
        "shielding_subheader": "屏蔽层 (最多 3 层)",
        "num_layers": "层数",
        "material_layer": "层材料",
        "thickness_layer": "厚度 (厘米)",
        "scenarios_subheader": "情景",
        "scenario_name": "情景名称",
        "author_label": "作者",
        "note_label": "备注",
        "save_scenario": "保存情景",
        "scenario_saved": "情景已保存到 scenarios/my_scenarios.json",
        "scenario_save_error": "保存错误",
        "current_point": "当前点",
        "Dr_metric_label": "D(r) (相对)",
        "zone_green": "绿色区域 (≤ D_safe)",
        "zone_yellow": "黄色区域 (介于 D_safe 与 3·D_safe)",
        "zone_red": "红色区域 (> 3·D_safe)",
        "caption_model": "教学模型: 1/r² · exp(−Σ μ·x)。系数和单位均为相对值。",
        "chart_title": "D(r) 曲线",
        "ylog_checkbox": "对数坐标 (D)",
        "export_png_button": "下载 D(r) 曲线 PNG",
        "export_png_unavailable": "无法导出 PNG",
        "export_csv_button": "下载 D(r) 数据 CSV",
        "formula_section": "交互公式",
        "formula_description": "调整模型参数即可即时刷新 D(r) 曲线。",
        "formula_k_label": "源强 k",
        "formula_r_label": "当前距离 r",
        "formula_eval_label": "用于计算的 r",
        "formula_result_label": "计算得到的 D(r)",
        "formula_mu_label": "总衰减",
        "material_visualization_title": "屏蔽层可视化",
        "material_visualization_caption": "根据厚度(厘米)显示各屏蔽层。",
        "material_visualization_empty": "添加屏蔽层以查看可视化。",
        "rad_animation_title": "辐射动画",
        "rad_animation_caption": "展示所选辐射穿过屏蔽的示意动画。",
        "recommendations_header": "材料厚度建议",
        "recommendations_caption": "在当前距离达到安全剂量所需的厚度。",
        "recommendations_material": "材料",
        "recommendations_thickness": "厚度 (厘米)",
        "recommendations_not_needed": "无需额外屏蔽",
        "safety_header": "安全警示",
        "safety_warning_prefix": "注意:",
        "dangerous_combination_intro": "请检查所选材料的兼容性。",
        "ask_assistant_header": "询问助手 (离线知识库)",
        "ask_placeholder": "输入问题 (例如：“什么是时间-距离-屏蔽原则？”)",
        "assistant_empty": "知识库未加载或为空。",
        "assistant_nearest_question": "最接近的问题:",
        "assistant_similarity": "相似度 (TF-IDF)",
        "version_caption": "框架版本: 1.4，交互公式，可视化，支持 RU/EN/ZH"
    }
}

HINTS = {
    "RU": {
        "Гамма": "Гамма: чем выше плотность и Z — тем лучше (свинец, сталь, алюминий). Вода/бетон/акрил — слабее.",
        "Бета": "Бета: предпочтительны низко-Z (акрил/стекло, вода, алюминий). Свинец может усиливать тормозное излучение (учебно).",
        "Альфа": "Альфа: гасятся очень тонкими слоями; практически любой твёрдый материал подходит.",
        "Нейтроны": "Нейтроны: лучше водородсодержащие материалы (вода, бетон). Металлы — хуже."
    },
    "EN": {
        "Гамма": "Gamma: higher density and Z are better (lead, steel, aluminium). Water/concrete/acrylic are weaker.",
        "Бета": "Beta: prefer low-Z (acrylic/glass, water, aluminium). Lead may increase bremsstrahlung (educational simplification).",
        "Альфа": "Alpha: stopped by very thin layers; almost any solid works.",
        "Нейтроны": "Neutrons: hydrogen-rich materials are better (water, concrete). Metals are worse."
    },
    "ZH": {
        "Гамма": "伽马: 高密度高 Z 材料更好 (铅、钢、铝)，水/混凝土/丙烯酸稍弱。",
        "Бета": "贝塔: 优选低 Z 材料 (丙烯酸/玻璃、水、铝)。铅可能增强轫致辐射 (教学示例)。",
        "Альфа": "阿尔法: 极薄的固体材料即可屏蔽，几乎任意材料都有效。",
        "Нейтроны": "中子: 含氢材料效果更佳 (水、混凝土)，金属通常较差。"
    }
}

MATERIAL_COLORS = {
    "Свинец": "#4e596b",
    "Сталь": "#8c8f99",
    "Бетон": "#b8a68c",
    "Вода": "#4f9ff5",
    "Стекло/акрил": "#9fd9ff",
    "Алюминий": "#c0c8d6",
}

RAD_TYPE_OPTIONS = {
    "RU": [("Гамма", "Гамма"), ("Бета", "Бета"), ("Альфа", "Альфа"), ("Нейтроны", "Нейтроны")],
    "EN": [("Gamma (γ)", "Гамма"), ("Beta (β)", "Бета"), ("Alpha (α)", "Альфа"), ("Neutrons", "Нейтроны")],
    "ZH": [("伽马 (Gamma)", "Гамма"), ("贝塔 (Beta)", "Бета"), ("阿尔法 (Alpha)", "Альфа"), ("中子", "Нейтроны")],
}

RAD_ANIMATION_SETTINGS = {
    "Гамма": {"color": "#ffcc00", "symbol": "diamond", "label": "γ"},
    "Бета": {"color": "#29b6f6", "symbol": "circle", "label": "β"},
    "Альфа": {"color": "#ef5350", "symbol": "triangle-up", "label": "α"},
    "Нейтроны": {"color": "#66bb6a", "symbol": "square", "label": "n"},
}

LANG_OPTIONS = ["RU", "EN", "ZH"]
LANG_DISPLAY = {"RU": "Русский", "EN": "English", "ZH": "简体中文"}
LANG_SELECTOR_LABEL = "Язык / Language / 语言"


PARAM_CONFIG = {
    "k": {
        "value": "k_value",
        "slider": "k_slider",
        "formula": "k_formula",
        "pending_formula": "pending_k_from_formula",
        "pending_slider": "pending_k_from_slider",
        "formula_flag": "sync_k_from_formula",
        "slider_flag": "sync_k_from_slider",
        "default": 1.0,
    },
    "r": {
        "value": "r_value",
        "slider": "r_slider",
        "formula": "r_formula",
        "pending_formula": "pending_r_from_formula",
        "pending_slider": "pending_r_from_slider",
        "formula_flag": "sync_r_from_formula",
        "slider_flag": "sync_r_from_slider",
        "default": 2.0,
    },
}


def queue_formula_sync(param: str) -> None:
    cfg = PARAM_CONFIG[param]
    formula_key = cfg["formula"]
    value_key = cfg["value"]
    new_val = float(st.session_state.get(formula_key, st.session_state.get(value_key, cfg["default"])))
    st.session_state[cfg["pending_formula"]] = new_val
    st.session_state[cfg["formula_flag"]] = True


def queue_slider_sync(param: str) -> None:
    cfg = PARAM_CONFIG[param]
    slider_key = cfg["slider"]
    value_key = cfg["value"]
    new_val = float(st.session_state.get(slider_key, st.session_state.get(value_key, cfg["default"])))
    st.session_state[cfg["pending_slider"]] = new_val
    st.session_state[cfg["slider_flag"]] = True


def ensure_parameter_state(param: str) -> None:
    cfg = PARAM_CONFIG[param]
    default = cfg["default"]
    value_key = cfg["value"]
    slider_key = cfg["slider"]
    formula_key = cfg["formula"]
    if value_key not in st.session_state:
        st.session_state[value_key] = default
    if slider_key not in st.session_state:
        st.session_state[slider_key] = float(st.session_state[value_key])
    if formula_key not in st.session_state:
        st.session_state[formula_key] = float(st.session_state[value_key])


def apply_pending_syncs(param: str) -> None:
    cfg = PARAM_CONFIG[param]
    if st.session_state.get(cfg["formula_flag"]):
        new_val = float(
            st.session_state.get(cfg["pending_formula"], st.session_state[cfg["value"]])
        )
        st.session_state[cfg["value"]] = new_val
        st.session_state[cfg["slider"]] = new_val
        st.session_state[cfg["formula"]] = new_val
        st.session_state[cfg["formula_flag"]] = False
    if st.session_state.get(cfg["slider_flag"]):
        new_val = float(
            st.session_state.get(cfg["pending_slider"], st.session_state[cfg["value"]])
        )
        st.session_state[cfg["value"]] = new_val
        st.session_state[cfg["formula"]] = new_val
        st.session_state[cfg["slider_flag"]] = False


def get_radiation_options(lang: str) -> tuple[list[str], list[str]]:
    options = RAD_TYPE_OPTIONS.get(lang, RAD_TYPE_OPTIONS["RU"])
    labels = [label for label, _ in options]
    values = [value for _, value in options]
    return labels, values


def compute_total_attenuation(layers: list[ShieldLayer], radiation_type: str) -> tuple[float, list[tuple[str, float, float, float]]]:
    terms = []
    total = 0.0
    for layer in layers:
        mu = _mu_for(layer.material, radiation_type)
        contribution = mu * max(layer.thickness_cm, 0.0)
        if layer.thickness_cm > 0:
            terms.append((layer.material, mu, layer.thickness_cm, contribution))
        total += contribution
    return total, terms


def compute_recommendations(k: float, r_current: float, D_safe: float, radiation_type: str, lang: str) -> pd.DataFrame:
    records = []
    if k <= 0:
        return pd.DataFrame(columns=[T(lang, "recommendations_material"), T(lang, "recommendations_thickness")])
    target = D_safe * (r_current ** 2) / k
    for material in MATERIALS.keys():
        mu = _mu_for(material, radiation_type)
        if mu <= 0:
            thickness = float("nan")
        elif target >= 1:
            thickness = 0.0
        else:
            thickness = max(0.0, -math.log(target) / mu)
        records.append({
            T(lang, "recommendations_material"): material,
            T(lang, "recommendations_thickness"): thickness if thickness >= 0 else float("nan"),
        })
    df = pd.DataFrame(records)
    df[T(lang, "recommendations_thickness")] = df[T(lang, "recommendations_thickness")].map(
        lambda x: "—" if pd.isna(x) else f"{x:.2f}"
    )
    return df


def build_material_figure(layers: list[ShieldLayer], lang: str) -> go.Figure:
    fig = go.Figure()
    for layer in layers:
        if layer.thickness_cm <= 0:
            continue
        color = MATERIAL_COLORS.get(layer.material, "#888888")
        fig.add_trace(
            go.Bar(
                x=[layer.thickness_cm],
                y=[""],
                orientation="h",
                marker_color=color,
                name=layer.material,
                hovertemplate=(
                    f"{layer.material}: {layer.thickness_cm:.2f} см" if lang == "RU" else f"{layer.material}: {layer.thickness_cm:.2f} cm"
                ),
                width=0.6,
            )
        )
    fig.update_layout(
        barmode="stack",
        showlegend=True,
        height=220,
        xaxis_title="Толщина (см)" if lang == "RU" else ("Thickness (cm)" if lang == "EN" else "厚度 (厘米)"),
        yaxis=dict(showticklabels=False),
        margin=dict(l=20, r=20, t=30, b=30),
    )
    return fig


def build_radiation_animation(layers: list[ShieldLayer], radiation_type: str, lang: str) -> go.Figure:
    settings = RAD_ANIMATION_SETTINGS.get(radiation_type, RAD_ANIMATION_SETTINGS["Гамма"])
    total_thickness = sum(max(layer.thickness_cm, 0.0) for layer in layers)
    x_positions = np.linspace(0, max(total_thickness, 1.0), 12)
    frames = []
    for idx in range(len(x_positions)):
        frames.append(
            go.Frame(
                data=[
                    go.Scatter(
                        x=x_positions[: idx + 1],
                        y=[1 + 0.1 * math.sin(2 * (x + idx / 2)) for x in x_positions[: idx + 1]],
                        mode="lines+markers",
                        line=dict(color=settings["color"], width=3),
                        marker=dict(color=settings["color"], symbol=settings["symbol"], size=10),
                        name=settings["label"],
                    )
                ],
                name=f"frame{idx}",
            )
        )
    base_trace = go.Scatter(
        x=[x_positions[0]],
        y=[1],
        mode="lines+markers",
        line=dict(color=settings["color"], width=3),
        marker=dict(color=settings["color"], symbol=settings["symbol"], size=10),
        name=settings["label"],
    )
    shield_boundary = np.cumsum([0] + [max(layer.thickness_cm, 0.0) for layer in layers])
    layout = go.Layout(
        height=280,
        xaxis=dict(
            title="Толщина экрана (см)" if lang == "RU" else ("Shield thickness (cm)" if lang == "EN" else "屏蔽厚度 (厘米)"),
            range=[0, max(total_thickness, 1.0)],
        ),
        yaxis=dict(showticklabels=False, range=[0.5, 1.6]),
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "buttons": [
                    {
                        "label": "▶",
                        "method": "animate",
                        "args": [None, {"frame": {"duration": 200, "redraw": True}, "fromcurrent": True}],
                    }
                ],
            }
        ],
        shapes=[
            dict(
                type="rect",
                x0=shield_boundary[i],
                x1=shield_boundary[i + 1],
                y0=0.5,
                y1=1.6,
                fillcolor=MATERIAL_COLORS.get(layer.material, "#dddddd"),
                opacity=0.15,
                line=dict(width=0),
            )
            for i, layer in enumerate(layers)
            if layer.thickness_cm > 0
        ],
        margin=dict(l=20, r=20, t=30, b=40),
    )
    fig = go.Figure(data=[base_trace], frames=frames, layout=layout)
    return fig


def check_hazards(layers: list[ShieldLayer], lang: str) -> list[str]:
    materials_selected = {layer.material for layer in layers if layer.thickness_cm > 0}
    warnings = []
    for combo in DANGEROUS_COMBINATIONS:
        if combo["materials"].issubset(materials_selected):
            messages = combo.get("messages", {})
            warning = messages.get(lang) or messages.get("EN") or next(iter(messages.values()), "")
            if warning:
                warnings.append(warning)
    return warnings

def T(lang, key):
    return TEXTS.get(lang, TEXTS["RU"]).get(key, key)

st.set_page_config(page_title="Shielding Simulator", layout="wide")
lang = st.sidebar.selectbox(
    LANG_SELECTOR_LABEL,
    LANG_OPTIONS,
    index=0,
    format_func=lambda code: LANG_DISPLAY.get(code, code),
)

for param in ("k", "r"):
    ensure_parameter_state(param)
    apply_pending_syncs(param)

if "D_safe_value" not in st.session_state:
    st.session_state["D_safe_value"] = 0.2
if "r_eval" not in st.session_state:
    st.session_state["r_eval"] = float(st.session_state[PARAM_CONFIG["r"]["value"]])

@st.cache_resource
def load_qa_index():
    try:
        return QAIndex.from_csv("data/qa.csv")
    except Exception:
        return QAIndex([])

qa_index = load_qa_index()

st.sidebar.header(T(lang, "sidebar_header"))
rad_labels, rad_values = get_radiation_options(lang)
selected_label = st.sidebar.selectbox(T(lang, "rad_type"), rad_labels, index=0)
rad_type = rad_values[rad_labels.index(selected_label)]

k_slider_val = float(st.session_state[PARAM_CONFIG["k"]["slider"]])
k = st.sidebar.slider(
    T(lang, "k_label"),
    0.1,
    5.0,
    k_slider_val,
    0.1,
    key=PARAM_CONFIG["k"]["slider"],
    on_change=queue_slider_sync,
    args=("k",),
)
st.session_state[PARAM_CONFIG["k"]["value"]] = float(st.session_state[PARAM_CONFIG["k"]["slider"]])

r_slider_val = float(st.session_state[PARAM_CONFIG["r"]["slider"]])
r_current = st.sidebar.slider(
    T(lang, "r_label"),
    0.1,
    10.0,
    r_slider_val,
    0.1,
    key=PARAM_CONFIG["r"]["slider"],
    on_change=queue_slider_sync,
    args=("r",),
)
st.session_state[PARAM_CONFIG["r"]["value"]] = float(st.session_state[PARAM_CONFIG["r"]["slider"]])
D_safe = st.sidebar.slider(T(lang, "D_safe_label"), 0.01, 1.0, st.session_state["D_safe_value"], 0.01, key="D_safe_value")

st.sidebar.subheader(T(lang, "shielding_subheader"))
layers = []
layer_count = st.sidebar.number_input(T(lang, "num_layers"), 0, 3, 1, 1)
mat_names = list(MATERIALS.keys())
for i in range(int(layer_count)):
    col1, col2 = st.sidebar.columns(2)
    with col1:
        hint = HINTS.get(lang, HINTS["RU"]).get(rad_type, "")
        mat = st.selectbox(f"{T(lang, 'material_layer')} {i+1}", mat_names, key=f"mat_{i}", help=hint)
    with col2:
        th = st.number_input(f"{T(lang, 'thickness_layer')} {i+1}", 0.0, 50.0, 0.0, 0.5, key=f"th_{i}")
    layers.append(ShieldLayer(material=mat, thickness_cm=th))

st.sidebar.divider()
st.sidebar.subheader(T(lang, "scenarios_subheader"))
default_name = "Сценарий 1" if lang == "RU" else ("Scenario 1" if lang == "EN" else "情景 1")
scenario_name = st.sidebar.text_input(T(lang, "scenario_name"), value=default_name)
author = st.sidebar.text_input(T(lang, "author_label"), value="")
note = st.sidebar.text_area(T(lang, "note_label"), value="")
if st.sidebar.button(T(lang, "save_scenario")):
    payload = {
        "k": float(k),
        "r_current": float(r_current),
        "D_safe": float(D_safe),
        "layers": [{"material": L.material, "thickness_cm": float(L.thickness_cm)} for L in layers],
        "radiation_type": rad_type,
        "author": author,
        "note": note,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "lang": lang
    }
    try:
        os_path = "scenarios/my_scenarios.json"
        os.makedirs(os.path.dirname(os_path), exist_ok=True)
        try:
            with open(os_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        scenario_key = scenario_name if f"[{rad_type}]" in scenario_name else f"{scenario_name} [{rad_type}]"
        data[scenario_key] = payload
        with open(os_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        st.sidebar.success(T(lang, "scenario_saved"))
    except Exception as e:
        st.sidebar.error(f"{T(lang, 'scenario_save_error')}: {e}")

k = float(st.session_state["k_value"])
r_current = float(st.session_state["r_value"])
D_safe = float(st.session_state["D_safe_value"])

st.divider()
st.markdown("## " + T(lang, "formula_section"))
st.caption(T(lang, "formula_description"))

formula_cols = st.columns(3)
with formula_cols[0]:
    k_formula_default = float(st.session_state.get(PARAM_CONFIG["k"]["formula"], k))
    st.number_input(
        T(lang, "formula_k_label"),
        min_value=0.1,
        max_value=5.0,
        value=k_formula_default,
        step=0.1,
        key=PARAM_CONFIG["k"]["formula"],
        on_change=queue_formula_sync,
        args=("k",),
    )
with formula_cols[1]:
    r_formula_default = float(st.session_state.get(PARAM_CONFIG["r"]["formula"], r_current))
    st.number_input(
        T(lang, "formula_r_label"),
        min_value=0.1,
        max_value=10.0,
        value=r_formula_default,
        step=0.1,
        key=PARAM_CONFIG["r"]["formula"],
        on_change=queue_formula_sync,
        args=("r",),
    )
with formula_cols[2]:
    r_eval_default = float(st.session_state.get("r_eval", r_current))
    st.number_input(
        T(lang, "formula_eval_label"),
        min_value=0.1,
        max_value=10.0,
        value=r_eval_default,
        step=0.1,
        key="r_eval",
    )

k_formula_value = float(st.session_state.get(PARAM_CONFIG["k"]["formula"], k))
r_eval_value = float(st.session_state.get("r_eval", r_current))

total_mu, mu_terms = compute_total_attenuation(layers, rad_type)
if mu_terms:
    mu_expr = " + ".join([f"{mu:.2f} \\cdot {th:.2f}" for _, mu, th, _ in mu_terms])
else:
    mu_expr = "0"
latex_formula = rf"D(r) = \frac{{{k_formula_value:.2f}}}{{r^2}} \cdot \exp(-({mu_expr}))"
st.latex(latex_formula)
st.caption(f"{T(lang, 'formula_mu_label')}: {total_mu:.2f}")
dose_at_eval = dose(k_formula_value, r_eval_value, layers, radiation_type=rad_type)
st.metric(T(lang, "formula_result_label"), f"{dose_at_eval:.3f}")
if mu_terms:
    breakdown_lines = [
        f"{mat}: μ={mu:.2f}, x={th:.2f} см, μ·x={contrib:.2f}" if lang == "RU" else (
            f"{mat}: μ={mu:.2f}, x={th:.2f} cm, μ·x={contrib:.2f}" if lang == "EN" else f"{mat}: μ={mu:.2f}, x={th:.2f} 厘米, μ·x={contrib:.2f}"
        )
        for mat, mu, th, contrib in mu_terms
    ]
    st.markdown("\n".join(f"- {line}" for line in breakdown_lines))

colA, colB = st.columns([1, 2])

with colA:
    D_now = dose(k, r_current, layers, radiation_type=rad_type)
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
    r, d = dose_curve(k, layers, r_min, r_max, num=400, radiation_type=rad_type)
    ylog = st.checkbox(T(lang, "ylog_checkbox"), value=False)
    fig = go.Figure()
    fig.add_scatter(x=r, y=d, mode="lines", name="D(r)")
    fig.add_hline(y=D_safe, line_dash="dot", annotation_text="D_safe")
    fig.add_vline(x=r_eval_value, line_dash="dash", line_color="#888888", annotation_text=f"r={r_eval_value:.2f}")
    x_title = {
        "EN": "Distance r (m)",
        "ZH": "距离 r (米)",
    }.get(lang, "Расстояние r (м)")
    y_title = {
        "EN": "Dose rate D (rel.)",
        "ZH": "剂量率 D (相对)",
    }.get(lang, "Относительная мощность дозы D")
    fig.update_layout(xaxis_title=x_title, yaxis_title=y_title)
    if ylog:
        fig.update_yaxes(type="log", exponentformat="power")
    st.plotly_chart(fig, use_container_width=True)
    try:
        png_bytes = fig.to_image(format="png", scale=2)
        st.download_button(T(lang, "export_png_button"), data=png_bytes,
                           file_name="dose_curve.png", mime="image/png")
    except Exception as e:
        st.caption(f"{T(lang, 'export_png_unavailable')}: {e}")
    df = pd.DataFrame({"r": r, "D": d})
    st.download_button(T(lang, "export_csv_button"), data=df.to_csv(index=False).encode("utf-8"),
                       file_name="dose_curve.csv", mime="text/csv")

viz_col1, viz_col2 = st.columns(2)
with viz_col1:
    st.markdown("#### " + T(lang, "material_visualization_title"))
    if any(layer.thickness_cm > 0 for layer in layers):
        mat_fig = build_material_figure(layers, lang)
        st.plotly_chart(mat_fig, use_container_width=True)
        st.caption(T(lang, "material_visualization_caption"))
    else:
        st.info(T(lang, "material_visualization_empty"))

with viz_col2:
    st.markdown("#### " + T(lang, "rad_animation_title"))
    anim_fig = build_radiation_animation(layers, rad_type, lang)
    st.plotly_chart(anim_fig, use_container_width=True)
    st.caption(T(lang, "rad_animation_caption"))

st.markdown("### " + T(lang, "recommendations_header"))
st.caption(T(lang, "recommendations_caption"))
recommendations_df = compute_recommendations(k, r_current, D_safe, rad_type, lang)
if k > 0 and (D_safe * (r_current ** 2) / k) >= 1:
    st.success(T(lang, "recommendations_not_needed"))
st.table(recommendations_df)

warnings = check_hazards(layers, lang)
if warnings:
    st.markdown("### " + T(lang, "safety_header"))
    st.write(T(lang, "dangerous_combination_intro"))
    for msg in warnings:
        st.warning(f"{T(lang, 'safety_warning_prefix')} {msg}")

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
