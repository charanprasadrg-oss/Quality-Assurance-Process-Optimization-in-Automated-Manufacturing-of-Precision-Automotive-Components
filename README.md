# Quality-Assurance-Process-Optimization-in-Automated-Manufacturing-of-Precision-Automotive-Components
This is a Python-based tool that simulates the full quality-assurance and process-optimization workflow used around precision automotive machining, built to combine my mechanical engineering background — particularly my hands-on experience with precision measuring instruments — with practical software development and statistical process control (SPC).

The project includes a small catalog of automotive-style components: a brake caliper piston bore, a camshaft journal diameter, and a connecting-rod small-end bore, each defined with a realistic nominal dimension, tolerance band, and inspection gauge. For any of these parts, the tool can generate two simulated production scenarios: a baseline batch, representing manual inspection with looser process control, and an improved batch, representing the same part after a corrective action such as a tool-offset correction, better fixturing, or a switch from a manual gauge and paper log to a digital gauge with direct data capture.

For a single batch, the core inspection engine checks each part against its lower and upper specification limits, flags it PASS or FAIL, and calculates key process-capability indices, Cp and Cpk. It also builds an Individuals and Moving-Range (I-MR) control chart to catch subtle process drift, such as gradual tool wear, before it causes a spike in failures, along with a histogram comparing the measurement distribution to the tolerance band. All of this is compiled into a self-contained Markdown inspection report with embedded charts and a short list of recommended corrective actions.

The process-optimization module goes a step further: it compares the baseline and improved batches directly and quantifies the effect of the simulated corrective action across three dimensions — process capability (Cp/Cpk), scrap/fail rate, and average inspection cycle time. For example, on the camshaft journal scenario, the tool showed Cpk improving from 0.63 ("not capable") to 1.52 ("capable"), fail rate dropping from 2.5% to 0%, and inspection time falling by roughly 54% after switching to a digital gauge. This is the kind of before/after evidence a quality or production engineer would present to justify a process change.

Software and tools used:

Python 3 – core language for the entire pipeline
pandas – reading, structuring, and annotating measurement data
matplotlib – control charts, histograms, and before/after comparison charts
Python's built-in statistics module – mean, standard deviation, Cp/Cpk calculations
argparse – command-line configuration for parts, scenarios, and file paths
Markdown – lightweight, portable inspection and comparison reports

Why I built it:
During my project work, I worked directly with precision measuring instruments and was responsible for verifying part conformity and documenting results. I wanted to build a tool that reflects the complete quality-engineering loop — measurement, capability analysis, control charting, and quantified process improvement — specifically framed around automotive-style components, since that's a domain where dimensional tolerances and process capability matter enormously.

Possible extensions include reading measurements directly from a digital gauge or CMM export, adding X-bar/R charts for subgrouped sampling, exporting reports as PDF, and adding automated alerts when a part fails or a control limit is breached.
