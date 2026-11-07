from autogrow.storage import Storage
from autogrow.watering import WaterConfig, Waterer


class Pump:
    def __init__(self):
        self.runs = []

    def run(self, s):
        self.runs.append(s)


def mk(tmp_path, **kw):
    pump = Pump()
    return Waterer(WaterConfig(**kw), pump, Storage(str(tmp_path / "t.db"))), pump


def test_waters_when_dry_not_when_wet(tmp_path):
    w, pump = mk(tmp_path)
    assert w.check(50) == 0 and pump.runs == []
    assert w.check(20) == 50 and pump.runs == [10.0]


def test_no_watering_without_reading(tmp_path):
    w, pump = mk(tmp_path)
    assert w.check(None) == 0 and pump.runs == []


def test_min_gap(tmp_path):
    w, pump = mk(tmp_path)
    w.check(20, now=1_000_000)
    assert w.check(20, now=1_000_000 + 3600) == 0
    assert w.check(20, now=1_000_000 + 7 * 3600) == 50


def test_daily_cap_applies_to_manual_too(tmp_path):
    w, pump = mk(tmp_path, max_ml_per_day=100)
    assert w.water("manual") == 50 and w.water("manual") == 50
    assert w.water("manual") == 0 and len(pump.runs) == 2
