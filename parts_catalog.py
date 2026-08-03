"""
parts_catalog.py

A small catalog of automotive-style precision components used by
generate_demo_data.py to simulate realistic inspection scenarios.

IMPORTANT: The nominal dimensions and tolerances below are reasonable,
textbook-style engineering assumptions for these kinds of components
(the sort of values you'd find in a machine design reference), NOT
specifications copied from any real manufacturer's drawing. They exist to
give the demo data a believable, automotive-relevant context.
"""

PARTS = {
    "brake_caliper_bore": {
        "description": "Brake caliper piston bore (hydraulic sealing surface)",
        "nominal_mm": 42.000,
        "tolerance_mm": 0.020,      # tight tolerance: sealing/hydraulic fit
        "measurement_column": "bore_diameter_mm",
        "gauge": "Bore gauge (dial/digital)",
    },
    "camshaft_journal": {
        "description": "Camshaft journal diameter (plain bearing fit)",
        "nominal_mm": 26.000,
        "tolerance_mm": 0.013,      # tight tolerance: bearing running fit
        "measurement_column": "journal_diameter_mm",
        "gauge": "Micrometer",
    },
    "conrod_small_end_bore": {
        "description": "Connecting rod small-end bore (piston pin fit)",
        "nominal_mm": 22.000,
        "tolerance_mm": 0.015,
        "measurement_column": "bore_diameter_mm",
        "gauge": "Bore gauge (dial/digital)",
    },
}


def get_part(name: str) -> dict:
    if name not in PARTS:
        valid = ", ".join(PARTS.keys())
        raise ValueError(f"Unknown part '{name}'. Available parts: {valid}")
    return PARTS[name]
