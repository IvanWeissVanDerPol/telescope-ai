# Hardware Setup Guide

## Your Telescope: Celestron NexStar 130SLT

| Spec | Value |
|------|-------|
| Aperture | 130mm (5") |
| Focal Length | 650mm (f/5) |
| Mount | Alt-Azimuth, computerized |
| Motor | DC servo, 4°/s max slew |
| Controller | NexStar+ hand controller |
| Communication | RS-232 (9600 baud, 8N1) |
| Power | 12V DC (8x AA batteries or adapter) |
| Weight | ~8.5 kg (18.7 lbs) |

## Required Hardware

### To connect to a computer:

| Item | Cost | Notes |
|------|------|-------|
| USB-to-serial cable | $10-15 | FTDI-based recommended (PL2303 works) |
| Celestron #93920 cable | $30 | Official cable, includes adapter |
| Or: generic USB-serial + RJ-22 adapter | $15 | Same protocol |

### Optional:

| Item | Cost | Use |
|------|------|-----|
| Phone eyepiece adapter | $15 | Phone camera for plate solving |
| ZWO ASI120MC (used) | $50-80 | Entry-level astro camera |
| T-ring + T-adapter (for DSLR) | $30 | Prime-focus DSLR photography |
| 12V power adapter | $15 | Save batteries |

## Connection Methods

### Method 1: Direct Serial (All Features)

```
NexStar HC --serial-- USB-adapter --USB-- Computer
```

Best for: Python control, satellite tracking, custom automation.

### Method 2: Via CPWI/ASCOM (Windows Only)

```
NexStar HC --serial-- Computer running CPWI/ASCOM -- TCP -- Any app
```

Best for: N.I.N.A., Stellarium, SharpCap, plate solving.

### Method 3: Via INDI (Linux/RPi)

```
NexStar HC --serial-- RPi running INDI -- WiFi -- Phone/Laptop
```

Best for: Headless operation, remote access, low power.

## Pinout

The NexStar+ hand controller uses an RJ-22 (4P4C) connector:

```
Pin 1: Ground
Pin 2: TX (from mount)
Pin 3: RX (to mount)
Pin 4: +5V (do not connect)
```

Standard serial cable (DB9):
```
RJ-22 Pin 2 → DB9 Pin 2 (RX)
RJ-22 Pin 3 → DB9 Pin 3 (TX)
RJ-22 Pin 1 → DB9 Pin 5 (GND)
```

## Testing Your Connection

```bash
# Linux: find the serial port
ls /dev/ttyUSB*

# Test communication
python3 -c "
import serial
s = serial.Serial('/dev/ttyUSB0', 9600, timeout=2)
s.write(b'K#')
ver = s.read(1024)
print(f'Version: {ver}')
"
```

Expected: `Version: b'4.17'` (or similar firmware version).

## Camera Options

### Phone Camera (Free start)

1. Buy phone eyepiece adapter ($15 from Amazon/Mercadolibre)
2. Download DeepSkyCamera (Android) or NightCap (iOS)
3. Hold phone to eyepiece, capture

### Webcam/Planetary

1. Replace eyepiece with camera
2. Install ASCOM drivers for the camera
3. Use SharpCap (Windows) or INDI (Linux)

### DSLR

1. Buy T-ring for your camera brand + T-adapter (1.25"/2")
2. Remove eyepiece, insert T-adapter, attach camera
3. Manual focus via live view

## Power

- The NexStar runs on 8x AA batteries (~4 hours)
- Better: 12V 2A AC adapter (Celestron #18769) or portable power bank with 12V output
- For RPi: separate 5V/3A USB-C power supply
