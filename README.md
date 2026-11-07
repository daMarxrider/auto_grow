*As requested by [Answer0832](https://github.com/Answer0832)*

# auto_grow

Automated climate control and monitoring for a chili grow tent under artificial light.

The goal is a self-regulating system that keeps temperature, humidity and VPD (vapor pressure deficit) in the ideal range, gives remote access to live data and a camera image, and later waters the plants automatically during longer absences.

## Roadmap

1. **Monitoring & sensors (MVP)**: temperature/RH sensors, VPD calculation, local storage, local dashboard
2. **Automatic control**: exhaust fan and lamp dimming, PID/threshold control, manual override, safety limits
3. **Remote access & camera**: externally reachable dashboard (VPN/tunnel), live graphs, camera, authentication
4. **Automatic watering** (later): soil moisture sensors, pump, watering logic with limits

Out of scope: nutrient management, AI disease detection, smart-home integration, multiple tents.

## Feature scope

The full feature scope (in German) is in [docs/feature_scope_growbox.md](docs/feature_scope_growbox.md).

## Status

Phase 1 (monitoring) and phase 2 (control) are in progress. Chosen parts and wiring: [hardware.md](hardware.md).

## Run

```
python -m autogrow --sensor sim            # simulated sensor, no hardware needed
python -m autogrow --sensor sht31          # SHT31 on I2C (Raspberry Pi)
```

Add `--actuators gpio` to drive the fan/lamp through GPIO (needs `gpiozero`); the default `sim` only prints. Ideal ranges and limits: `--vpd-min --vpd-max --temp-soft-max --temp-hard-max`.

Dashboard: http://localhost:8080 (options: `--interval`, `--db`, `--port`). Tests: `pytest`.
