import threading
import time
from dataclasses import dataclass


@dataclass
class WaterConfig:
    dry_below: float = 35.0       # % soil moisture that triggers watering
    shot_seconds: float = 10.0    # pump run time per watering
    ml_per_second: float = 5.0    # pump calibration: measure it once!
    max_ml_per_day: float = 500.0  # hard cap, also applies to manual watering
    min_gap_hours: float = 6.0    # let the water soak in before re-checking


class SimSoilSensor:
    def read(self):
        return 30.0 + 20 * ((time.time() // 600) % 2)


class SeesawSoilSensor:
    """Adafruit STEMMA Soil Sensor (I2C). Needs `pip install adafruit-circuitpython-seesaw`."""

    DRY, WET = 350, 1000  # raw readings in air / in water: calibrate for your pot

    def __init__(self):
        import board
        from adafruit_seesaw.seesaw import Seesaw

        self._s = Seesaw(board.I2C(), addr=0x36)

    def read(self):
        raw = self._s.moisture_read()
        return max(0.0, min(100.0, (raw - self.DRY) / (self.WET - self.DRY) * 100))


class SimPump:
    def run(self, seconds):
        print(f"pump: {seconds:.1f}s")


class GpioPump:
    def __init__(self, pin=22):
        from gpiozero import DigitalOutputDevice

        self.dev = DigitalOutputDevice(pin, active_high=False)

    def run(self, seconds):
        try:
            self.dev.on()
            time.sleep(seconds)
        finally:
            self.dev.off()  # always switch off, even on errors


class Waterer:
    def __init__(self, cfg, pump, storage):
        self.cfg, self.pump, self.storage = cfg, pump, storage
        self.lock = threading.Lock()  # one watering at a time

    def water(self, reason, now=None):
        """Run one shot if the daily cap allows it. Returns ml given (0 if refused)."""
        ml = self.cfg.shot_seconds * self.cfg.ml_per_second
        with self.lock:
            if self.storage.water_ml_since(86400, now) + ml > self.cfg.max_ml_per_day:
                self.storage.log_water(0, f"refused (daily cap): {reason}", now)
                return 0.0
            self.pump.run(self.cfg.shot_seconds)
            self.storage.log_water(ml, reason, now)
        return ml

    def check(self, moisture, now=None):
        """Automatic watering decision for one soil reading."""
        if moisture is None or moisture >= self.cfg.dry_below:
            return 0.0
        last = self.storage.last_water_ts()
        if last and (now or time.time()) - last < self.cfg.min_gap_hours * 3600:
            return 0.0
        return self.water(f"soil {moisture:.0f}% < {self.cfg.dry_below:.0f}%", now)


def watering_loop(sensor, waterer, storage, minutes):
    while True:
        try:
            m = sensor.read()
            storage.add_soil(m)
            waterer.check(m)
        except Exception as e:  # a failing sensor must never trigger watering
            print("watering error:", e)
        time.sleep(minutes * 60)
