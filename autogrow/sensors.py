import math
import time


class SimulatedSensor:
    """Fake sensor for development without hardware."""

    def read(self):
        t = time.time()
        return 24 + 3 * math.sin(t / 600), 60 + 10 * math.sin(t / 900)


class SHT31Sensor:
    """SHT31 over I2C (needs `pip install adafruit-circuitpython-sht31d` on the Pi)."""

    def __init__(self):
        import adafruit_sht31d
        import board

        self._s = adafruit_sht31d.SHT31D(board.I2C())

    def read(self):
        return self._s.temperature, self._s.relative_humidity


def make_sensor(kind: str):
    return {"sim": SimulatedSensor, "sht31": SHT31Sensor}[kind]()
