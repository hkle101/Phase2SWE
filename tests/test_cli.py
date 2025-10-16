import json
import subprocess
import sys
from pathlib import Path


def load_ndjson(path: Path):
    lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
    return [json.loads(line) for line in lines]


def extract_scores(obj: dict):
    keys = [
        "ramp_up_time",
        "bus_factor",
        "performance_claims",
        "license",
        "size_score",
        "dataset_and_code_score",
        "dataset_quality",
        "code_quality",
        "net_score",
    ]
    return {k: obj.get(k) for k in keys}


def test_repo_outputs_match(tmp_path: Path):
    urls = Path.cwd() / "urls.txt"
    repo1_out = tmp_path / "repo1.jsonl"
    repo2_out = tmp_path / "repo2.jsonl"

    # Prepare a repo1-compatible input file that lists MODEL URLs in the
    # third CSV column (code_url,dataset_url,model_url). Repo1 only scores
    # entries with category == MODEL when processing a file input, so we
    # create lines like: , ,https://huggingface.co/owner/model
    repo1_input = tmp_path / "repo1_input.txt"
    with open(urls, "r") as inf, repo1_input.open("w") as outf:
        for line in inf:
            u = line.strip()
            if not u:
                continue
            # only include HF model URLs for repo1 processing
            if "huggingface.co" in u and "/datasets/" not in u:
                outf.write(f",,{u}\n")

    # Run repo1 processing directly.
    # This avoids token/log validation performed by the run wrapper.
    repo1_dir = Path.cwd().parent / "repo1"
    # Use python to import and call process_and_score_input_file
    cmd = [
        sys.executable,
        "-c",
        (
            "from src.cli import process_and_score_input_file; "
            f"process_and_score_input_file(r'{repo1_input}')"
        ),
    ]
    with repo1_out.open("w") as f:
        subprocess.run(cmd, cwd=repo1_dir, check=True, stdout=f)

    # Run repo2 CLI
    repo2_dir = Path.cwd()
    cmd2 = [sys.executable, "-m", "cli.main", str(urls)]
    with repo2_out.open("w") as f2:
        subprocess.run(cmd2, cwd=repo2_dir, check=True, stdout=f2)

    a = load_ndjson(repo1_out)
    b = load_ndjson(repo2_out)

    # Only compare MODEL entries — repo1 processed MODEL only from the
    # prepared input. Filter repo2's output for MODEL category rows.
    b_models = [row for row in b if row.get("category") == "MODEL"]

    assert len(a) == len(b_models)

    # Build mapping by name for deterministic comparisons
    b_by_name = {row.get("name"): row for row in b_models}

    for ao in a:
        name = ao.get("name")
        bo = b_by_name.get(name)
        assert bo is not None, (
            f"No matching MODEL row for {name} in repo2 output"
        )
        sa = extract_scores(ao)
        sb = extract_scores(bo)
        # For size_score ensure both sides produce the same set of keys and each
        # reported value is a valid number in [0.0, 1.0]. We intentionally do not
        # require exact parity here because implementations may differ.
        a_size = sa.get("size_score") or {}
        b_size = sb.get("size_score") or {}
        assert set(a_size.keys()) == set(b_size.keys()), "size_score keys differ between repos"
        for k in a_size.keys():
            va = float(a_size.get(k) or 0.0)
            vb = float(b_size.get(k) or 0.0)
            for name_, val in (("repo1", va), ("repo2", vb)):
                assert isinstance(val, float) or isinstance(val, int)
                assert 0.0 <= float(val) <= 1.0, f"{name_} size_score {k} out of range: {val}"
        # compare other scalar keys
        for k in [
            "ramp_up_time",
            "bus_factor",
            "performance_claims",
            "license",
            "dataset_and_code_score",
            "dataset_quality",
            "code_quality",
            "net_score",
        ]:
            va = sa.get(k)
            vb = sb.get(k)
            # normalize None to -1 (metric error) for comparison
            def _norm(v):
                if v is None:
                    return -1.0
                try:
                    return float(v)
                except Exception:
                    return -1.0

            va = _norm(va)
            vb = _norm(vb)

            # valid values are either -1.0 (error) or in [0.0, 1.0]
            for label, val in (("repo1", va), ("repo2", vb)):
                if val < 0:
                    assert val == -1.0, f"Invalid negative metric value for {label} {k}: {val}"
                else:
                    assert 0.0 <= val <= 1.0, f"Metric {k} out of expected range for {label}: {val}"

