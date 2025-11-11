import numpy as np
from dataclasses import dataclass

MATERIALS = {
    "Свинец": 1.20,
    "Сталь": 0.80,
    "Бетон": 0.35,
    "Вода": 0.30,
    "Стекло/акрил": 0.15,
}

MATERIAL_COSTS = {
    "Свинец": 50.0,
    "Сталь": 35.0,
    "Бетон": 10.0,
    "Вода": 5.0,
    "Стекло/акрил": 20.0,
}

MU_BY_TYPE = {
    "Гамма": {
        "Свинец": 1.20, "Сталь": 0.80, "Бетон": 0.35, "Вода": 0.30, "Стекло/акрил": 0.15
    },
    "Бета": {
        "Стекло/акрил": 1.10, "Вода": 0.80, "Бетон": 0.40, "Сталь": 0.20, "Свинец": 0.05
    },
    "Альфа": {
        "Свинец": 25.0, "Сталь": 20.0, "Бетон": 15.0, "Вода": 12.0, "Стекло/акрил": 18.0
    },
    "Нейтроны": {
        "Вода": 1.10, "Бетон": 0.90, "Стекло/акрил": 0.30, "Сталь": 0.20, "Свинец": 0.10
    },
}

RADIATION_TYPES = list(MU_BY_TYPE.keys())

# --- Overrides loader ---
import json, os

def _load_mu_override(path: str = "data/mu_override.json"):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # normalize keys to strings and values to floats
        cleaned = {}
        for rtype, mats in data.items():
            cleaned[rtype] = {}
            for mat, val in mats.items():
                try:
                    cleaned[rtype][mat] = float(val)
                except Exception:
                    pass
        return cleaned
    except Exception:
        return None

def _merge_mu(base_table: dict, override: dict | None):
    if not override:
        return base_table
    merged = {k: v.copy() for k, v in base_table.items()}
    for rtype, mats in override.items():
        if rtype not in merged:
            merged[rtype] = {}
        for mat, val in mats.items():
            merged.setdefault(rtype, {})[mat] = float(val)
    return merged

MU_OVERRIDE = _load_mu_override()
MU_ACTIVE = _merge_mu(MU_BY_TYPE, MU_OVERRIDE)


@dataclass
class ShieldLayer:
    material: str
    thickness_cm: float

def _mu_for(material: str, radiation_type: str) -> float:
    table = MU_ACTIVE.get(radiation_type, MATERIALS)
    return float(table.get(material, MATERIALS.get(material, 0.0)))

def dose(k: float, r_m: float, layers: list[ShieldLayer], radiation_type: str = "Гамма") -> float:
    if r_m <= 0:
        r_m = 1e-3
    mu_sum = 0.0
    for L in layers:
        mu_sum += _mu_for(L.material, radiation_type) * max(L.thickness_cm, 0.0)
    attenuation = np.exp(-mu_sum)
    return float(k * attenuation / (r_m ** 2))

def dose_curve(k: float, layers: list[ShieldLayer], r_min: float, r_max: float, num: int = 200, radiation_type: str = "Гамма"):
    r = np.linspace(max(r_min, 1e-3), max(r_max, 1e-3), num=num)
    d = np.array([dose(k, ri, layers, radiation_type=radiation_type) for ri in r], dtype=float)
    return r, d

def classify_zone(D: float, D_safe: float) -> str:
    if D <= D_safe:
        return "green"
    if D <= 3.0 * D_safe:
        return "yellow"
    return "red"
