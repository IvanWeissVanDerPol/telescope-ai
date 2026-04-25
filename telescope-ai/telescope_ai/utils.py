import math

def hms_to_hours(h: int, m: int, s: float = 0) -> float:
    return h + m / 60 + s / 3600

def dms_to_degrees(d: int, m: int, s: float = 0) -> float:
    sign = -1 if d < 0 else 1
    return sign * (abs(d) + m / 60 + s / 3600)

def hours_to_hms(ra: float) -> str:
    h = int(ra)
    m = int((ra - h) * 60)
    s = (ra - h - m / 60) * 3600
    return f"{h:02d}h {m:02d}m {s:04.1f}s"

def degrees_to_dms(dec: float) -> str:
    sign = "-" if dec < 0 else "+"
    d = int(abs(dec))
    m = int((abs(dec) - d) * 60)
    s = (abs(dec) - d - m / 60) * 3600
    return f"{sign}{d:02d}° {m:02d}' {s:04.1f}\""

def angular_distance(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    dlat = math.radians(dec2 - dec1)
    dlon = math.radians((ra2 - ra1) * 15)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(dec1)) * math.cos(math.radians(dec2)) * math.sin(dlon / 2) ** 2
    return math.degrees(2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def jd_from_datetime(dt) -> float:
    import datetime
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    from skyfield.api import load
    ts = load.timescale()
    return ts.from_datetime(dt).tt
