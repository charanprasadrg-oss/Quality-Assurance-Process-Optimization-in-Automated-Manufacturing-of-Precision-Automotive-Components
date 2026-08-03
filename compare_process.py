"""
compare_process.py

Compares a "baseline" and "improved" measurement dataset for the same
automotive part (see parts_catalog.py / generate_demo_data.py) to
demonstrate a quality-assurance & process-optimization workflow:

    - capability (Cp/Cpk) before vs. after a simulated corrective action
    - fail rate before vs. after
    - average inspection cycle time before vs. after

Produces a Markdown comparison report with charts, showing quantitatively
what "process optimization" bought you.

Usage:
    python generate_demo_data.py --part camshaft_journal --scenario both
    python compare_process.py --part camshaft_journal
"""

import argparse
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from parts_catalog import get_part, PARTS
from qc_inspect import compute_capability, classify_capability


def parse_args():
    parser = argparse.ArgumentParser(description="Baseline vs improved process comparison")
    parser.add_argument("--part", required=True, choices=list(PARTS.keys()))
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--output-dir", default="output")
    return parser.parse_args()


def analyze(df, column, lsl, usl):
    df = df.copy()
    df["result"] = df[column].apply(lambda v: "PASS" if lsl <= v <= usl else "FAIL")
    n_total = len(df)
    n_fail = int((df["result"] == "FAIL").sum())
    cap = compute_capability(df[column].tolist(), lsl, usl)
    avg_time = df["inspection_time_sec"].mean()
    return {
        "n_total": n_total,
        "n_fail": n_fail,
        "fail_rate": 100 * n_fail / n_total,
        "mean": cap["mean"],
        "stdev": cap["stdev"],
        "cp": cap["cp"],
        "cpk": cap["cpk"],
        "avg_inspection_time": avg_time,
        "df": df,
    }


def build_comparison_charts(part_name, column, base, imp, lsl, usl, nominal, out_dir: Path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].hist(base["df"][column], bins=15, alpha=0.6, label="Baseline", color="#b23a48")
    axes[0].hist(imp["df"][column], bins=15, alpha=0.6, label="Improved", color="#1f3864")
    axes[0].axvline(lsl, color="red", linestyle="--", linewidth=1)
    axes[0].axvline(usl, color="red", linestyle="--", linewidth=1)
    axes[0].axvline(nominal, color="green", linestyle="-", linewidth=1)
    axes[0].set_title(f"{part_name}: measurement distribution")
    axes[0].set_xlabel(column)
    axes[0].set_ylabel("Frequency")
    axes[0].legend()

    metrics = ["Cpk", "Fail rate (%)", "Avg inspection time (s)"]
    base_vals = [base["cpk"], base["fail_rate"], base["avg_inspection_time"]]
    imp_vals = [imp["cpk"], imp["fail_rate"], imp["avg_inspection_time"]]

    x = range(len(metrics))
    width = 0.35
    axes[1].bar([i - width / 2 for i in x], base_vals, width, label="Baseline", color="#b23a48")
    axes[1].bar([i + width / 2 for i in x], imp_vals, width, label="Improved", color="#1f3864")
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(metrics, rotation=15)
    axes[1].set_title("Before vs. after — key metrics")
    axes[1].legend()

    fig.tight_layout()
    chart_path = out_dir / f"{part_name}_before_after.png"
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)
    return chart_path


def main():
    args = parse_args()
    part = get_part(args.part)
    column = part["measurement_column"]
    nominal = part["nominal_mm"]
    tolerance = part["tolerance_mm"]
    lsl, usl = nominal - tolerance, nominal + tolerance

    data_dir = Path(args.data_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    base_df = pd.read_csv(data_dir / f"{args.part}_baseline.csv")
    imp_df = pd.read_csv(data_dir / f"{args.part}_improved.csv")

    base = analyze(base_df, column, lsl, usl)
    imp = analyze(imp_df, column, lsl, usl)

    chart_path = build_comparison_charts(args.part, column, base, imp, lsl, usl, nominal, out_dir)

    time_saved_pct = 100 * (1 - imp["avg_inspection_time"] / base["avg_inspection_time"])
    fail_rate_change = base["fail_rate"] - imp["fail_rate"]

    lines = []
    lines.append(f"# Process Optimization Report — {part['description']}\n")
    lines.append(f"**Part:** `{args.part}`  |  **Nominal:** {nominal:.4f} mm  "
                 f"|  **Tolerance:** ±{tolerance:.4f} mm  |  **Gauge:** {part['gauge']}\n")

    lines.append("## Baseline vs. Improved Process\n")
    lines.append("| Metric | Baseline | Improved | Change |")
    lines.append("|---|---|---|---|")
    lines.append(f"| Parts inspected | {base['n_total']} | {imp['n_total']} | - |")
    lines.append(f"| Failed parts | {base['n_fail']} | {imp['n_fail']} | - |")
    lines.append(f"| Fail rate | {base['fail_rate']:.1f}% | {imp['fail_rate']:.1f}% | "
                 f"{fail_rate_change:+.1f} pp |")
    lines.append(f"| Process mean | {base['mean']:.4f} | {imp['mean']:.4f} | - |")
    lines.append(f"| Std. dev. | {base['stdev']:.4f} | {imp['stdev']:.4f} | "
                 f"{100 * (1 - imp['stdev'] / base['stdev']):.1f}% reduction |")
    lines.append(f"| Cp | {base['cp']:.2f} | {imp['cp']:.2f} | - |")
    lines.append(f"| Cpk | {base['cpk']:.2f} | {imp['cpk']:.2f} | - |")
    lines.append(f"| Avg. inspection time | {base['avg_inspection_time']:.1f}s | "
                 f"{imp['avg_inspection_time']:.1f}s | {time_saved_pct:.0f}% faster |\n")

    lines.append("## Interpretation\n")
    lines.append(f"- **Capability:** {classify_capability(base['cpk'])} (baseline) -> "
                 f"{classify_capability(imp['cpk'])} (improved).")
    lines.append(f"- **Inspection cycle time** dropped by about {time_saved_pct:.0f}%, "
                 f"consistent with switching from a manual gauge + paper log to a digital "
                 f"gauge with direct data capture.")
    lines.append(f"- **Fail rate** changed by {fail_rate_change:+.1f} percentage points "
                 f"after the simulated corrective action (tool-offset correction / improved "
                 f"fixturing).\n")

    lines.append("## Chart\n")
    lines.append(f"![Before vs after]({chart_path.name})\n")

    report_path = out_dir / f"{args.part}_process_optimization_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Baseline: Cpk={base['cpk']:.2f}, fail rate={base['fail_rate']:.1f}%, "
          f"avg time={base['avg_inspection_time']:.1f}s")
    print(f"Improved: Cpk={imp['cpk']:.2f}, fail rate={imp['fail_rate']:.1f}%, "
          f"avg time={imp['avg_inspection_time']:.1f}s")
    print(f"Report written to: {report_path}")
    print(f"Chart written to: {chart_path}")


if __name__ == "__main__":
    main()
