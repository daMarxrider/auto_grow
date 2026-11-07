from autogrow.control import Config, Controller, decide
from autogrow.storage import Storage

C = Config()


def test_in_range():
    assert decide(C, 24, 70)[:2] == (0.5, 1.0)  # VPD ~0.9


def test_humid_ventilates_more():
    assert decide(C, 24, 95)[0] > 0.5


def test_dry_slows_fan():
    assert decide(C, 24, 30)[0] == 0.3


def test_hot_dims_lamp_and_full_fan():
    fan, lamp, _ = decide(C, 30, 60)
    assert fan == 1.0 and 0 < lamp < 1


def test_hard_limit_lamp_off():
    assert decide(C, 32, 60)[:2] == (1.0, 0.0)


def test_stale_or_missing_sensor_failsafe():
    assert decide(C, None, None)[:2] == (1.0, 0.0)
    assert decide(C, 24, 60, age=999)[:2] == (1.0, 0.0)


class Rec:
    calls = []

    def set(self, fan, lamp):
        self.calls.append((fan, lamp))


def test_override_cannot_beat_hard_limit(tmp_path):
    ctl = Controller(C, Rec(), Storage(str(tmp_path / "t.db")))
    ctl.override = {"fan": 0.0, "lamp": 1.0}
    assert ctl.step(24, 70)[:2] == (0.0, 1.0)
    assert ctl.step(35, 50)[:2] == (1.0, 0.0)
