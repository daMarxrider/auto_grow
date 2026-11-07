# Hardware

Chosen parts for the build. Mains-voltage parts must be wired by someone qualified; nothing here replaces that.

| Role | Pick | Why |
|------|------|-----|
| Controller | [Raspberry Pi 4 Model B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) (2 GB is plenty) + official USB-C power supply | Runs Python, camera and Tailscale on one board; hardware PWM on GPIO18 |
| Temp + RH sensor | [Adafruit SHT31-D breakout](https://www.adafruit.com/product/2857) ([guide](https://learn.adafruit.com/adafruit-sht31-d-temperature-and-humidity-sensor-breakout)) | ±0.3 °C / ±2 % RH, beats the scope's ±0.5 °C / ±3 % RH. I2C address 0x44, or 0x45 for a second redundant sensor |
| Camera | [Raspberry Pi Camera Module 3](https://www.raspberrypi.com/products/camera-module-3/) | Autofocus, native Pi support. Pick the NoIR version only if you add IR light |
| Lamp dimming | PWM to 0-10 V converter module, e.g. [this type](https://rajivelectronics.com/product/pwm-to-voltage-0-100-to-10v-converter-module) | Works only if the lamp's driver has a 0-10 V dim input. Check this first (open point in the scope) |
| Exhaust fan | 5 V opto-isolated relay module (any 2-channel, active-low) | Simple on/off. If the fan is EC with a 0-10 V or PWM input, use the same converter type as the lamp for speed control |
| Soil moisture | [Adafruit STEMMA Soil Sensor](https://www.adafruit.com/product/4026) (I2C, address 0x36) | Capacitive (does not corrode like resistive probes), no ADC needed |
| Water pump | 12 V peristaltic pump (dosing pump) + 12 V supply, switched by a third relay channel | Dosing is predictable, so ml/s can be calibrated and the daily cap means something. Any pump works if you measure its flow |
| Safety cutoff | Mechanical thermostat (e.g. capillary or bimetal, set ~35 °C) wired in series with the lamp | Hardware limit that still works if the Pi or the software hangs |
| Remote access | [Tailscale](https://tailscale.com/kb/1017/install) | No port forwarding, free for personal use |

## Wiring (BCM pin numbers, used as defaults by the code)

| Signal | GPIO |
|--------|------|
| SHT31 SDA / SCL | 2 / 3 |
| Lamp dimmer PWM | 18 |
| Fan relay | 17 |
| Lamp relay (software safety cutoff) | 27 |
| Pump relay | 22 |
| Soil sensor SDA / SCL | 2 / 3 (shared I2C bus) |

## Notes


- If the lamp is not dimmable, the lamp runs on/off via its relay only and dimming is skipped.

- Watering: measure the pump's real flow (run it for 10 s into a cup) and pass it as `--ml-per-second`; calibrate the soil sensor's dry/wet raw values in `SeesawSoilSensor`. Keep the reservoir small enough that a stuck pump cannot flood the tent.
