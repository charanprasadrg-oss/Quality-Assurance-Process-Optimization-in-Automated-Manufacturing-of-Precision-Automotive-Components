"""
generate_demo_data.py

Generates a SYNTHETIC dataset of bore (hole) diameter measurements for a
fictional machined part, used to demonstrate the quality-inspection tool
in this repository.

This data is randomly generated (fixed seed for reproducibility) and does
NOT come from a real production line. It exists purely so the analysis
script (inspect.py) has realistic-looking numbers to work with.

Simulated scenario:
    Part:              Machined flange, bore diameter
    Nominal diameter:  10.00 mm
    Tolerance:          +/- 0.05 mm  (LSL = 9.95 mm, USL = 10.05 mm)
    Sample:            80 consecutively produced parts, one measurement each,
                       taken with a digital bore gauge.
    Scripted behaviour: the process is well-centered for the first 50 parts,
                       then a small tool-wear drift is introduced for the
                       remaining parts to create a few out-of-tolerance
                       readings for the tool to catch.
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

NOMINAL = 10.00
TOLERANCE = 0.05
LSL = NOMINAL - TOLERANCE
USL = NOMINAL + TOLERANCE

N_STABLE = 50
N_DRIFT = 30
N_TOTAL = N_STABLE + N_DRIFT

OUTPUT_FILE = "data/bore_diameter_measurements.csv"


def generate_measurement(part_index: int) -> float:
    """Return a simulated diameter reading for a given part index."""
    if part_index < N_STABLE:
        # Stable, well-centered process: small natural variation only
        value = random.gauss(mu=NOMINAL, sigma=0.012)
    else:
        # Simulated tool wear: gradual upward drift + slightly higher noise
        drift_steps = part_index - N_STABLE
        drift = 0.0009 * drift_steps  # slow upward creep
        value = random.gauss(mu=NOMINAL + drift, sigma=0.016)
    return round(value, 4)


def main():
    start_time = datetime(2026, 7, 1, 6, 0, 0)
    rows = []
    for i in range(N_TOTAL):
        timestamp = start_time + timedelta(minutes=6 * i)
        diameter = generate_measurement(i)
        rows.append(
            {
                "part_id": f"P{i + 1:04d}",
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M"),
                "machine_id": "CNC-03",
                "operator": random.choice(["A. Muller", "S. Kaya", "J. Becker"]),
                "diameter_mm": diameter,
            }
        )

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["part_id", "timestamp", "machine_id", "operator", "diameter_mm"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} synthetic measurements to {OUTPUT_FILE}")
    print(f"Nominal: {NOMINAL} mm | LSL: {LSL} mm | USL: {USL} mm")


if __name__ == "__main__":
    main()
