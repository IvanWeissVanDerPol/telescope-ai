"""Demo: Classify a celestial object by coordinates."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telescope_ai import ObjectClassifier, TelescopeConfig


def classify_object(ra: float, dec: float, name: str = ""):
    config = TelescopeConfig.load()
    classifier = ObjectClassifier(config)
    result = classifier.classify(ra=ra, dec=dec)

    label = f" ({name})" if name else ""
    print(f"\n{'=' * 50}")
    print(f"Position: RA={ra:.3f}h Dec={dec:.3f}°{label}")
    print(f"{'=' * 50}")
    print(f"Object:      {result.label}")
    print(f"Type:        {result.object_type}")
    print(f"Confidence:  {result.confidence:.1%}")
    print(f"Description: {result.description}")
    print(f"Catalogs:    {', '.join(result.catalog_ids) if result.catalog_ids else 'N/A'}")


def main():
    # Test coordinates
    targets = [
        (5.583, -5.383, "M42 - Orion Nebula"),
        (13.467, -47.283, "Omega Centauri"),
        (5.333, -69.75, "LMC"),
        (10.75, -59.867, "Carina Nebula"),
        (12.9, -60.35, "Jewel Box"),
        (12.0, 30.0, "Empty field"),
    ]

    for ra, dec, name in targets:
        classify_object(ra, dec, name)

    print("\n\nDone!")


if __name__ == "__main__":
    main()
