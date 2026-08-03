"""
inspect.py

Dimensional Quality Inspection & Statistical Process Control (SPC) tool.

Reads a CSV of part measurements, checks each part against a tolerance
band (LSL/USL), computes process-capability indices (Cp, Cpk), builds an
Individuals & Moving-Range (I-MR) control chart, and writes a Markdown
inspection report summarizing the results.

Usage:
    python inspect.py --input data/bore_diameter_measurements.csv \
                       --nominal 10.00 --tolerance 0.05 \
                       --column diameter_mm --output-dir output

If --nominal/--tolerance/--column are omitted, the defaults below (matching
the bundled demo dataset) are used.
"""

import argparse
import statistics
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser(description="Dimensional QC / SPC inspection tool")
    parser.add_argument("--input", default="data/bore_diameter_measurements.csv",
                         help="Path to input CSV file")
    parser.add_argument("--column", default="diameter_mm",
                         help="Name of the measurement column to analyze")
    parser.add_argument("--nominal", type=float, default=10.00,
                         help="Nominal (target) dimension")
    parser.add_argument("--tolerance", type=float, default=0.05,
                         help="Symmetric tolerance band (+/-) around nominal")
    parser.add_argument("--output-dir", default="output",
                         help="Directory to write charts and report into")
    return parser.parse_args()


def moving_ranges(values):
    return [abs(values[i] - values[i - 1]) for i in range(1, len(values))]


def compute_capability(values, lsl, usl):
    mean = statistics.mean(values)
    stdev = statistics.stdev(values)  # sample std dev
    cp = (usl - lsl) / (6 * stdev) if stdev > 0 else float("inf")
    cpu = (usl - mean) / (3 * stdev) if stdev > 0 else float("inf")
    cpl = (mean - lsl) / (3 * stdev) if stdev > 0 else float("inf")
    cpk = min(cpu, cpl)
    return {"mean": mean, "stdev": stdev, "cp": cp, "cpk": cpk}


def classify_capability(cpk):
    if cpk >= 1.33:
        return "Capable (Cpk >= 1.33) - process comfortably meets tolerance."
    elif cpk >= 1.00:
        return "Marginally capable (1.00 <= Cpk < 1.33) - monitor closely."
    else:
        return "Not capable (Cpk < 1.00) - process centering/variation needs correction."


def build_control_chart(df, column, mean, path):
    values = df[column].tolist()
    mr = moving_ranges(values)
    mr_bar = statistics.mean(mr)

    ucl_i = mean + 2.66 * mr_bar
    lcl_i = mean - 2.66 * mr_bar
    ucl_mr = 3.267 * mr_bar

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=False)

    ax1.plot(range(1, len(values) + 1), values, marker="o", markersize=3, linewidth=1, color="#1f3864")
    ax1.axhline(mean, color="green", linestyle="-", linewidth=1, label="Mean")
    ax1.axhline(ucl_i, color="red", linestyle="--", linewidth=1, label="UCL")
    ax1.axhline(lcl_i, color="red", linestyle="--", linewidth=1, label="LCL")
    ax1.set_title("Individuals Chart (I-chart)")
    ax1.set_ylabel(column)
    ax1.set_xlabel("Part sequence")
    ax1.legend(loc="upper left", fontsize=8)

    ax2.plot(range(2, len(values) + 1), mr, marker="o", markersize=3, linewidth=1, color="#8a5a00")
    ax2.axhline(mr_bar, color="green", linestyle="-", linewidth=1, label="Mean MR")
    ax2.axhline(ucl_mr, color="red", linestyle="--", linewidth=1, label="UCL")
    ax2.set_title("Moving Range Chart (MR-chart)")
    ax2.set_ylabel("Moving Range")
    ax2.set_xlabel("Part sequence")
    ax2.legend(loc="upper left", fontsize=8)

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)

    out_of_control = [
        i + 1 for i, v in enumerate(values) if v > ucl_i or v < lcl_i
    ]
    return out_of_control, ucl_i, lcl_i


def build_histogram(df, column, lsl, usl, nominal, path):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(df[column], bins=15, color="#1f3864", edgecolor="white", alpha=0.85)
    ax.axvline(lsl, color="red", linestyle="--", label="LSL")
    ax.axvline(usl, color="red", linestyle="--", label="USL")
    ax.axvline(nominal, color="green", linestyle="-", label="Nominal")
    ax.set_title(f"Distribution of {column}")
    ax.set_xlabel(column)
    ax.set_ylabel("Frequency")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    column = args.column
    lsl = args.nominal - args.tolerance
    usl = args.nominal + args.tolerance

    # --- Pass/fail inspection ---
    df["result"] = df[column].apply(lambda v: "PASS" if lsl <= v <= usl else "FAIL")
    n_total = len(df)
    n_fail = (df["result"] == "FAIL").sum()
    n_pass = n_total - n_fail
    fail_rate = 100 * n_fail / n_total

    failed_parts = df[df["result"] == "FAIL"]

    # --- Capability analysis ---
    cap = compute_capability(df[column].tolist(), lsl, usl)
    capability_note = classify_capability(cap["cpk"])

    # --- Charts ---
    control_chart_path = output_dir / "control_chart.png"
    histogram_path = output_dir / "histogram.png"
    ooc_points, ucl_i, lcl_i = build_control_chart(df, column, cap["mean"], control_chart_path)
    build_histogram(df, column, lsl, usl, args.nominal, histogram_path)

    # --- Annotated results CSV ---
    results_csv_path = output_dir / "inspection_results.csv"
    df.to_csv(results_csv_path, index=False)

    # --- Markdown report ---
    report_path = output_dir / "inspection_report.md"
    lines = []
    lines.append("# Dimensional Quality Inspection Report\n")
    lines.append(f"**Input file:** `{input_path.name}`  ")
    lines.append(f"**Measurement:** `{column}`  ")
    lines.append(f"**Nominal:** {args.nominal:.4f}  |  **Tolerance:** ±{args.tolerance:.4f}  "
                 f"|  **LSL:** {lsl:.4f}  |  **USL:** {usl:.4f}\n")

    lines.append("## Summary\n")
    lines.append(f"- Parts inspected: **{n_total}**")
    lines.append(f"- Passed: **{n_pass}**")
    lines.append(f"- Failed: **{n_fail}** ({fail_rate:.1f}%)")
    lines.append(f"- Process mean: **{cap['mean']:.4f}**")
    lines.append(f"- Process std. dev.: **{cap['stdev']:.4f}**")
    lines.append(f"- Cp: **{cap['cp']:.2f}**")
    lines.append(f"- Cpk: **{cap['cpk']:.2f}** — {capability_note}\n")

    if n_fail > 0:
        lines.append("## Failed Parts\n")
        lines.append("| Part ID | Measurement | Result |")
        lines.append("|---|---|---|")
        for _, row in failed_parts.iterrows():
            lines.append(f"| {row['part_id']} | {row[column]:.4f} | FAIL |")
        lines.append("")
    else:
        lines.append("## Failed Parts\n\nNone — all parts within tolerance.\n")

    if ooc_points:
        lines.append("## Control Chart — Out-of-Control Points\n")
        lines.append(f"UCL: {ucl_i:.4f} | LCL: {lcl_i:.4f}\n")
        lines.append(f"Sequence positions flagged as out-of-control: {ooc_points}\n")
        lines.append("This pattern is consistent with a gradual process shift "
                     "(e.g. tool wear) rather than a single random outlier, and "
                     "warrants a tooling/setup check.\n")
    else:
        lines.append("## Control Chart\n\nNo points exceeded the control limits.\n")

    lines.append("## Charts\n")
    lines.append(f"![Histogram]({histogram_path.name})\n")
    lines.append(f"![Control Chart]({control_chart_path.name})\n")

    lines.append("## Recommended Corrective Actions\n")
    if n_fail > 0 or ooc_points:
        lines.append("- Inspect and, if needed, replace/adjust the tool on the flagged machine.")
        lines.append("- Re-measure parts produced after the first out-of-control point.")
        lines.append("- Tighten the inspection interval until the process is confirmed stable.")
    else:
        lines.append("- No corrective action required; continue routine monitoring.")

    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Inspected {n_total} parts — {n_fail} failed ({fail_rate:.1f}%).")
    print(f"Cp={cap['cp']:.2f}, Cpk={cap['cpk']:.2f} -> {capability_note}")
    print(f"Report written to: {report_path}")
    print(f"Charts written to: {histogram_path}, {control_chart_path}")
    print(f"Annotated results written to: {results_csv_path}")


if __name__ == "__main__":
    main()
