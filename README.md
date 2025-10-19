### [specification](https://docs.google.com/document/d/1NWiuwE5Wed-GJe0kkOqNTdrLqy6LxcoW/edit)
### [plan](https://docs.google.com/document/d/1Pi7RIyCG_YTDKf9OB2fm8Qpr_6PD3Okw/edit)

# Repo2 CLI (metrics runner)

This folder contains a small CLI that runs several repository/model/dataset
quality metrics and prints one compact NDJSON record per input URL.

This README explains how to run the tool and the sequential flow it follows
for each URL.

## Quick start

1. From the `phase2/repo2` folder run the CLI on a file of URLs (one URL per line):

```bash
# prints one JSON object per line to stdout
python3 -m cli.main urls.txt
```

See `SETUP.md` for step-by-step local setup and virtualenv instructions (macOS/zsh).

2. Each printed line is a compact JSON object with metric scores and latency
   fields. Example keys: `name`, `category`, `net_score`, `ramp_up_time`,
   `ramp_up_time_latency`, `performance_claims`, `performance_claims_latency`, etc.

## Sequential flow for each URL

When the CLI processes a single URL it follows these steps in order:

1. Build the metric list
   - The CLI instantiates the metric classes defined in `cli/metrics/`.
   - Current metrics: RampUp, BusFactor, PerformanceClaims, License, Size,
     DatasetAndCode, DatasetQuality, CodeQuality.

2. Run each metric with timing
   - For each metric the CLI calls the metric's `timed_calculate(url)` method.
   - `timed_calculate` runs the metric's `calculate(url)` and measures runtime
     in milliseconds, adding a `{metric_name}_latency` field to the result.

3. Collect metric outputs
   - Each metric returns a small dict of scores (e.g. `{"license": 1.0}`) and
     the latency field. The CLI merges these into a single result dict.

4. Compute net score
   - `net_score` is a weighted combination of per-metric scores (see
     `cli/main.py` for the `WEIGHTS` mapping). If a metric returns a complex
     object (for example `size_score` contains per-device numbers) it is
     reduced (averaged) before aggregation.
   - `net_score` is clamped to the range [0.0, 1.0].

5. Add metadata
   - The CLI adds `name` (derived from the URL) and `category` (MODEL, DATASET,
     REPO, or UNKNOWN) and `net_score_latency` (sum of metric latencies).

6. Print NDJSON
   - The combined result is printed as compact JSON (no extra whitespace),
     one line per input URL.



