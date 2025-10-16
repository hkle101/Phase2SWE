Setup and run instructions (macOS / zsh)

Follow these steps to run this repository locally on macOS using zsh. The
instructions create an isolated Python virtual environment, install
dependencies from `requirements.txt`, and show how to run the CLI and tests.

1) Open a terminal (zsh) and change to the repo folder

```bash
cd /Users/hehkle/Desktop/SWE/phase2/repo2
```

2) Create and activate a virtual environment

```bash
# create
python3 -m venv .venv
# activate (zsh)
source .venv/bin/activate
```

3) Upgrade pip and install requirements

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4) (Optional) Set GITHUB_TOKEN to avoid rate limits from the GitHub API

```bash
# create a GitHub personal access token (no special scopes required for public repo reads)
# then in your shell:
export GITHUB_TOKEN=ghp_your_token_here
```

5) Run the CLI

```bash
# default: interactive menu
./run

# run the CLI against a file of URLs (one URL per line)
./run urls.txt

# score a single URL directly
python3 -m cli.main --url https://huggingface.co/bert-base-uncased
```

6) Run the tests

```bash
# run the project tests for this repo
./run test

# or run pytest directly
pytest -q
```

7) Deactivate the virtualenv when done

```bash
deactivate
```

Troubleshooting
- If you see GitHub API 403 responses, set `GITHUB_TOKEN` as shown above.
- If pip install fails for any package, copy the failing package name and
  install it manually to see the error. Some dev tools (flake8, mypy)
  may require optional system libraries on older macOS versions.

That's it — you should now be able to run the CLI locally and run the
tests in an isolated virtual environment.
