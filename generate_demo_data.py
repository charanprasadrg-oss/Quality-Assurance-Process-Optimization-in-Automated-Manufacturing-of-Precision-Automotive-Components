"""
generate_demo_data.py

Generates SYNTHETIC measurement datasets for automotive-style precision
components (see parts_catalog.py), used to demonstrate the QC/SPC tool
in this repository. Data is randomly generated (fixed seed) and does
NOT come from a real production line.

Supports two scenarios per part, to demonstrate a process-optimization
comparison:

    baseline  - represents the "before" state: manual inspection,
                looser process control, more variation and a slow
                average inspection time per part.
    improved  - represents the "after" state, following a simulated
                corrective action (e.g. tool-offset correction, better
                fixturing, switch to a digital gauge): tighter process
                variation and a shorter average inspection time.

Usage:
    python generate_demo_data.py --part camshaft_journal --scenario baseline
    python generate_demo_data.py --part camshaft_journal --scenario improved
    python generate_demo_data.py --part brake_caliper_bore --scenario both
"""

import argparse
import csv
import random
from datetime import datetime, timedelta

from parts_catalog import get_part, PARTS

N_PARTS = 80


def parse_args():
    parser = argparse.ArgumentParser(description="Generate synthetic automotive part measurement data")
    parser.add_argument("--part", required=True, choices=list(PARTS.keys()),
                         help="Which part from the catalog to simulate")
    parser.add_argument("--scenario", default="both", choices=["baseline", "improved", "both"],
                         help="Which process scenario to generate")
    parser.add_argument("--n", type=int, default=N_PARTS, help="Number of parts to simulate")
    return parser.parse_args()


def generate_scenario(part_name: str, part: dict, scenario: str, n: int):
    # Reproducible but distinct random stream per part+scenario, so the
    # three catalog parts don't produce identical-looking numbers.
    seed = abs(hash((part_name, scenario))) % (2**32)
    rng = random.Random(seed)

    nominal = part["nominal_mm"]
    tolerance = part["tolerance_mm"]
    column = part["measurement_column"]

    if scenario == "baseline":
        # Before process optimization: manual setup, more variation,
        # a slight off-center bias, slower manual inspection.
        sigma = tolerance * rng.uniform(0.36, 0.48)
        bias = tolerance * rng.uniform(0.12, 0.24)
        insp_time_mean = rng.uniform(42.0, 50.0)
        insp_time_sigma = rng.uniform(7.0, 11.0)
        method = "Manual (caliper/gauge + paper log)"
    else:
        # After process optimization: corrected tool offset / better
        # fixturing, tighter variation, centered on nominal, faster
        # inspection via a digital gauge feeding results directly in.
        sigma = tolerance * rng.uniform(0.16, 0.26)
        bias = 0.0
        insp_time_mean = rng.uniform(16.0, 21.0)
        insp_time_sigma = rng.uniform(2.5, 4.0)
        method = "Digital gauge (direct data capture)"

    start_time = datetime(2026, 7, 6, 6, 0, 0)
    rows = []
    for i in range(n):
        timestamp = start_time + timedelta(minutes=5 * i)
        value = round(rng.gauss(mu=nominal + bias, sigma=sigma), 4)
        insp_time = max(4.0, round(rng.gauss(mu=insp_time_mean, sigma=insp_time_sigma), 1))
        rows.append({
            "part_id": f"{part_name.upper()[:3]}-{scenario[:2].upper()}-{i + 1:04d}",
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M"),
            "machine_id": "CNC-07",
            "operator": rng.choice(["A. Muller", "S. Kaya", "J. Becker"]),
            "inspection_method": method,
            column: value,
            "inspection_time_sec": insp_time,
        })

    out_path = f"data/{part_name}_{scenario}.csv"
    with open(out_path, "w", newline="") as f:
        fieldnames = ["part_id", "timestamp", "machine_id", "operator",
                      "inspection_method", column, "inspection_time_sec"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[{scenario}] wrote {len(rows)} rows to {out_path} "
          f"(nominal={nominal}, tol=+/-{tolerance}, avg inspection time~{insp_time_mean}s)")
    return out_path


def main():
    args = parse_args()
    part = get_part(args.part)

    scenarios = ["baseline", "improved"] if args.scenario == "both" else [args.scenario]
    for scenario in scenarios:
        generate_scenario(args.part, part, scenario, args.n)


if __name__ == "__main__":
    main()
