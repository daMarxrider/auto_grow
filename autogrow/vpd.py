import math


def vpd_kpa(temp_c: float, rh: float) -> float:
    """Vapor pressure deficit in kPa (Tetens), using air temperature for the leaf."""
    svp = 0.6108 * math.exp(17.27 * temp_c / (temp_c + 237.3))
    return svp * (1 - rh / 100)
