import time
from dataclasses import dataclass

from .vpd import vpd_kpa


@dataclass
class Config:
    vpd_min: float = 0.8       # kPa; below this the air is too humid -> ventilate
    vpd_max: float = 1.2       # kPa; above this the air is too dry -> slow the fan
    temp_soft_max: float = 28.0  # start dimming the lamp, fan to full
    temp_hard_max: float = 32.0  # lamp off
    temp_min: float = 15.0     # fan off below this (don't cool a cold tent)
    stale_after: float = 180.0   # seconds without a valid reading -> failsafe


def decide(cfg: Config, temp, rh, age=0.0):
    """Return (fan 0..1, lamp 0..1, reason). Pure function, no I/O."""
    if temp is None or rh is None or age > cfg.stale_after:
        return 1.0, 0.0, "failsafe: no valid sensor data (lamp off, fan on)"
    if temp >= cfg.temp_hard_max:
        return 1.0, 0.0, f"hard limit: {temp:.1f}C >= {cfg.temp_hard_max}C"

    # lamp: full below soft limit, linearly dimmed to 0 at the hard limit
    lamp = 1.0
    if temp > cfg.temp_soft_max:
        lamp = (cfg.temp_hard_max - temp) / (cfg.temp_hard_max - cfg.temp_soft_max)

    vpd = vpd_kpa(temp, rh)
    if temp > cfg.temp_soft_max:
        fan, why = 1.0, "too hot"
    elif temp < cfg.temp_min:
        fan, why = 0.0, "too cold"
    elif vpd < cfg.vpd_min:
        fan, why = min(1.0, 0.5 + (cfg.vpd_min - vpd)), "VPD low, ventilate"
    elif vpd > cfg.vpd_max:
        fan, why = 0.3, "VPD high, minimal ventilation"
    else:
        fan, why = 0.5, "VPD in range"
    return fan, round(lamp, 2), why


class Controller:
    def __init__(self, cfg, actuators, storage):
        self.cfg, self.act, self.storage = cfg, actuators, storage
        self.override = {}  # {"fan": 0..1, "lamp": 0..1}
        self.last = (None, None)  # last applied (fan, lamp)
        self.last_ok = time.time()

    def step(self, temp=None, rh=None):
        if temp is not None and rh is not None:
            self.last_ok = time.time()
        fan, lamp, why = decide(self.cfg, temp, rh, time.time() - self.last_ok)
        # manual override applies, but never beats a safety condition
        safe = why.startswith(("failsafe", "hard limit"))
        if not safe:
            if "fan" in self.override:
                fan, why = self.override["fan"], "manual override"
            if "lamp" in self.override:
                lamp = self.override["lamp"]
        if (fan, lamp) != self.last:
            self.act.set(fan, lamp)
            self.storage.log_action(fan, lamp, why)
            self.last = (fan, lamp)
        return fan, lamp, why
