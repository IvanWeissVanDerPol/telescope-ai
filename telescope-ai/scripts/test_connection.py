"""Test connection to mount. Works with simulator or real hardware."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telescope_ai import MountController, TelescopeConfig


def main():
    config = TelescopeConfig.load()
    mount_type = sys.argv[1] if len(sys.argv) > 1 else config.mount_type
    config.mount_type = mount_type

    print(f"Connecting to {mount_type} mount...")
    mount = MountController(config)

    if not mount.connect():
        print("FAILED: Could not connect")
        sys.exit(1)

    print("OK: Connected")

    try:
        ra, dec = mount.get_position_radec()
        alt, az = mount.get_position_altaz()
        print(f"OK: Position RA={ra:.4f}h Dec={dec:.4f}°")
        print(f"OK: Position Alt={alt:.2f}° Az={az:.2f}°")

        print("Testing goto RA=5.583h Dec=-5.383° (M42)...")
        mount.goto_radec(5.583, -5.383)
        ra2, dec2 = mount.get_position_radec()
        print(f"OK: After goto RA={ra2:.4f}h Dec={dec2:.4f}°")

        print("All connection tests passed!")

    finally:
        mount.disconnect()


if __name__ == "__main__":
    main()
