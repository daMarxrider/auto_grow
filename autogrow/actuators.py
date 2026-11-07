class SimActuators:
    def set(self, fan, lamp):
        print(f"actuators: fan={fan:.0%} lamp={lamp:.0%}")


class GpioActuators:
    """Fan on a relay (on/off at >=50% request), lamp dimmed via PWM + safety relay."""

    def __init__(self, fan_pin=17, lamp_relay_pin=27, lamp_pwm_pin=18):
        from gpiozero import DigitalOutputDevice, PWMOutputDevice

        # active_high=False: typical active-low relay boards
        self.fan = DigitalOutputDevice(fan_pin, active_high=False)
        self.lamp_relay = DigitalOutputDevice(lamp_relay_pin, active_high=False)
        self.lamp_pwm = PWMOutputDevice(lamp_pwm_pin, frequency=1000)

    def set(self, fan, lamp):
        self.fan.value = 1 if fan >= 0.3 else 0
        self.lamp_relay.value = 1 if lamp > 0 else 0
        self.lamp_pwm.value = lamp
