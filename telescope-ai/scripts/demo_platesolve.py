"""Demo: Plate solve an image (simulated)."""
import sys
import os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telescope_ai import PlateSolver, CameraController, TelescopeConfig


def main():
    config = TelescopeConfig.load()
    config.camera_type = "simulator"

    print("Generating simulated star field...")
    camera = CameraController(config)
    frame = camera.capture(exposure_ms=5000)
    if frame is None:
        print("Failed to capture frame")
        sys.exit(1)

    img_path = "/tmp/telescope_test_frame.jpg"
    # Normalize and save
    frame_8bit = (frame / 256).astype(np.uint8)
    Image.fromarray(frame_8bit).save(img_path)
    print(f"Saved test frame to {img_path}")

    print("Attempting plate solve...")
    solver = PlateSolver(config)
    result = solver.solve(img_path)

    if result:
        ra, dec, w, h = result
        print(f"\nPlate solve SUCCESS:")
        print(f"  RA:  {ra:.4f}h")
        print(f"  Dec: {dec:.4f}°")
        print(f"  FOV: {w:.2f}' × {h:.2f}'")
    else:
        print("\nPlate solve: no solution (expected without ASTAP installed)")
        print("Pre-solve analysis:")
        solver.estimate_initial(img_path)


if __name__ == "__main__":
    main()
