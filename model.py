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

@dataclass
class ShieldLayer:
    material: str
    thickness_cm: float

def dose(k: float, r_m: float, layers: list[ShieldLayer]) -> float:
    if r_m <= 0:
        r_m = 1e-3
    mu_sum = 0.0
    for L in layers:
        mu = MATERIALS.get(L.material, 0.0)
        mu_sum += mu * max(L.thickness_cm, 0.0)
    attenuation = np.exp(-mu_sum)
    return float(k * attenuation / (r_m ** 2))

def dose_curve(k: float, layers: list[ShieldLayer], r_min: float, r_max: float, num: int = 200):
    r = np.linspace(max(r_min, 1e-3), max(r_max, 1e-3), num=num)
    d = np.array([dose(k, ri, layers) for ri in r], dtype=float)
    return r, d

def classify_zone(D: float, D_safe: float) -> str:
    if D <= D_safe:
        return "green"
    if D <= 3.0 * D_safe:
        return "yellow"
    return "red"
