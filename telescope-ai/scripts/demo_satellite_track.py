"""Demo: Track a satellite with the telescope."""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telescope_ai import SatelliteTracker, MountController, TelescopeConfig

SATELLITE = "ISS (ZARYA)"
DURATION = 120  # 2 minutes


def main():
    config = TelescopeConfig.load()
    config.mount_type = "simulator"

    mount = MountController(config)
    if not mount.connect():
        print("Failed to connect mount")
        sys.exit(1)

    tracker = SatelliteTracker(config)
    print(f"Fetching TLE data...")
    if not tracker.fetch_tle():
        print("Failed to fetch TLEs")

    pos = tracker.get_current_position(SATELLITE)
    if pos:
        print(f"{SATELLITE}: Alt={pos.alt:.1f}° Az={pos.az:.1f}° Range={pos.range_km:.0f}km")
    else:
        sats = tracker.get_available_satellites()[:5]
        print(f"Available: {', '.join(sats)}")

    print(f"\nTracking {SATELLITE} for {DURATION}s...")
    tracker.track_satellite(SATELLITE, mount.goto_altaz, duration_s=DURATION)
    print("Tracking complete!")

    mount.disconnect()


if __name__ == "__main__":
    main()
