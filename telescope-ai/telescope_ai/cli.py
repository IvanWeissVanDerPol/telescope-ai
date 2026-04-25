import argparse
import logging
import sys
from .config import TelescopeConfig
from .mount import MountController
from .satellite import SatelliteTracker
from .scheduler import NightScheduler
from .weather import WeatherService
from .platesolve import PlateSolver

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(prog="telescope-ai", description="AI-powered telescope control")
    parser.add_argument("--config", help="Config file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    sub = parser.add_subparsers(dest="command", required=True)

    # connect
    p_conn = sub.add_parser("connect", help="Connect to mount")
    p_conn.add_argument("--type", choices=["nexstar", "simulator"], default=None)

    # goto
    p_goto = sub.add_parser("goto", help="Point telescope at coordinates")
    p_goto.add_argument("--ra", type=float, required=True, help="Right Ascension in hours")
    p_goto.add_argument("--dec", type=float, required=True, help="Declination in degrees")

    # position
    sub.add_parser("position", help="Get current telescope position")

    # satellite
    p_sat = sub.add_parser("satellite", help="Satellite operations")
    p_sat.add_argument("action", choices=["list", "track", "predict", "iss"])
    p_sat.add_argument("--name", help="Satellite name")
    p_sat.add_argument("--duration", type=int, default=300, help="Track duration (s)")
    p_sat.add_argument("--min-alt", type=float, default=20, help="Minimum altitude")

    # plan
    p_plan = sub.add_parser("plan", help="Generate night observing plan")
    p_plan.add_argument("--max", type=int, default=5, help="Max targets")

    # weather
    sub.add_parser("weather", help="Check observing conditions")

    # platesolve
    p_solve = sub.add_parser("platesolve", help="Plate solve an image")
    p_solve.add_argument("image", help="Image file path")

    # classify
    p_class = sub.add_parser("classify", help="Classify what the telescope sees")
    p_class.add_argument("--ra", type=float, help="RA in hours")
    p_class.add_argument("--dec", type=float, help="Dec in degrees")
    p_class.add_argument("--image", help="Image file path")

    # demo
    sub.add_parser("demo", help="Run full demonstration")

    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")

    config = TelescopeConfig.load(args.config)
    if args.command == "connect" and args.type:
        config.mount_type = args.type

    mount = MountController(config)
    weather = WeatherService(config)

    if args.command == "connect":
        if mount.connect():
            print(f"Connected to {config.mount_type} mount")
        else:
            print("Connection failed")
            sys.exit(1)

    elif args.command == "goto":
        if not mount.connect():
            sys.exit(1)
        mount.goto_radec(args.ra, args.dec)
        print(f"Goto RA={args.ra}h Dec={args.dec}°")

    elif args.command == "position":
        if not mount.connect():
            sys.exit(1)
        ra, dec = mount.get_position_radec()
        alt, az = mount.get_position_altaz()
        print(f"RA={ra:.4f}h  Dec={dec:.4f}°")
        print(f"Alt={alt:.2f}°  Az={az:.2f}°")

    elif args.command == "satellite":
        tracker = SatelliteTracker(config)
        if args.action == "list":
            if not tracker.fetch_tle():
                print("Failed to fetch TLEs")
                sys.exit(1)
            satellites = tracker.get_available_satellites()
            print(f"{len(satellites)} satellites available:")
            for s in satellites[:30]:
                print(f"  - {s}")
            if len(satellites) > 30:
                print(f"  ... and {len(satellites) - 30} more")

        elif args.action == "predict":
            if not args.name:
                print("--name required")
                sys.exit(1)
            tracker.fetch_tle()
            passes = tracker.predict_passes(args.name, args.min_alt)
            print(f"Predicted passes for {args.name}:")
            for p in passes:
                print(f"  Alt={p.max_altitude:.1f}° {p.direction}")

        elif args.action == "iss":
            passes = tracker.get_iss_pass_times()
            print("ISS passes (next 24h):")
            for p in passes:
                print(f"  {p['time']}  Alt={p['altitude']}°  {p['direction']}")

        elif args.action == "track":
            if not args.name:
                print("--name required")
                sys.exit(1)
            tracker.fetch_tle()
            mount.connect()
            print(f"Tracking {args.name} for {args.duration}s...")
            tracker.track_satellite(args.name, mount.goto_altaz, args.duration)

    elif args.command == "plan":
        plan = NightScheduler(config, weather).generate_plan(max_targets=args.max)
        print("Tonight's observing plan:")
        print("=" * 60)
        for item in plan:
            print(f"#{item.priority}: {item.target.name}")
            print(f"   Type: {item.target.object_type}")
            print(f"   Altitude: {item.altitude}°")
            print(f"   Duration: {item.duration_minutes} min")
            print(f"   Why: {item.reason}")
            print()

    elif args.command == "weather":
        cond = weather.get_conditions(force=True)
        print(f"Conditions: {cond.condition}")
        print(f"Cloud cover: {cond.cloud_cover_pct:.0f}%")
        print(f"Wind: {cond.wind_speed_ms:.1f} m/s")
        print(f"Dark: {cond.is_dark}")
        print(f"Observable: {cond.is_observable}")
        print(f"Reason: {cond.reason}")

    elif args.command == "platesolve":
        solver = PlateSolver(config)
        result = solver.solve(args.image)
        if result:
            ra, dec, w, h = result
            print(f"Solved: RA={ra:.4f}h Dec={dec:.4f}° FOV={w:.2f}x{h:.2f} arcmin")
        else:
            print("No solution found")

    elif args.command == "classify":
        from .classifier import ObjectClassifier
        classifier = ObjectClassifier(config)
        result = classifier.classify(image_path=args.image, ra=args.ra or 0, dec=args.dec or 0)
        print(f"Classification: {result.label}")
        print(f"Type: {result.object_type}")
        print(f"Confidence: {result.confidence:.1%}")
        if result.description:
            print(f"Info: {result.description}")

    elif args.command == "demo":
        print("=" * 60)
        print("TELESCOPE AI DEMONSTRATION")
        print("=" * 60)
        if not mount.connect():
            sys.exit(1)
        ra, dec = mount.get_position_radec()
        print(f"\n1. Mount position: RA={ra:.2f}h Dec={dec:.2f}°")
        if not weather.get_conditions().is_dark:
            print("2. Weather: daytime or cloudy")
        else:
            plan = NightScheduler(config, weather).generate_plan(3)
            print(f"\n2. Tonight's plan: {plan[0].target.name} (alt={plan[0].altitude}°)")
            print(f"   #1: {plan[0].target.name} - {plan[0].reason}")
            print(f"   #2: {plan[1].target.name} - {plan[1].reason}")
            print(f"   #3: {plan[2].target.name} - {plan[2].reason}")
        print("\n3. To track satellites: telescope-ai satellite track --name \"ISS (ZARYA)\"")
        print("4. To plate solve: telescope-ai platesolve /path/to/image.jpg")
        print("\nDemo complete.")

    mount.disconnect()


if __name__ == "__main__":
    main()
