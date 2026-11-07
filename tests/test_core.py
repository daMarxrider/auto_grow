import time

from autogrow.storage import Storage
from autogrow.vpd import vpd_kpa


def test_vpd_known_value():
    assert abs(vpd_kpa(25, 60) - 1.267) < 0.01


def test_vpd_saturated_is_zero():
    assert vpd_kpa(25, 100) == 0


def test_storage_window(tmp_path):
    s = Storage(str(tmp_path / "t.db"))
    s.add(24, 60, ts=time.time() - 8 * 86400)
    s.add(25, 60)
    r = s.since(7 * 86400)
    assert len(r) == 1 and abs(r[0]["vpd"] - 1.267) < 0.01
