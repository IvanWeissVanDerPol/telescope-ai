"""Demo: Generate an AI-optimized night observing plan."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telescope_ai import NightScheduler, WeatherService, TelescopeConfig


def main():
    config = TelescopeConfig.load()
    weather = WeatherService(config)
    scheduler = NightScheduler(config, weather)

    print(f"Location: {config.latitude}, {config.longitude}")
    print(f"Generating observing plan...\n")

    plan = scheduler.generate_plan(max_targets=8)
    cond = weather.get_conditions()

    print(f"Weather: {cond.condition} ({cond.cloud_cover_pct:.0f}% clouds)")
    print(f"Dark: {cond.is_dark}")
    print(f"Observable: {cond.is_observable}")
    if not cond.is_observable:
        print(f"Why not: {cond.reason}")
    print()

    print("=" * 60)
    print("TONIGHT'S OBSERVING PLAN")
    print("=" * 60)

    for item in plan:
        print(f"\n#{item.priority}: {item.target.name}")
        print(f"   Catalog:   {item.target.catalog_id or 'N/A'}")
        print(f"   Type:      {item.target.object_type}")
        print(f"   Magnitude: {item.target.magnitude}")
        print(f"   Altitude:  {item.altitude}°")
        print(f"   Time:      {item.best_time}")
        print(f"   Duration:  {item.duration_minutes} min")
        print(f"   Why:       {item.reason}")
        if item.target.description:
            print(f"   Info:      {item.target.description}")


if __name__ == "__main__":
    main()
