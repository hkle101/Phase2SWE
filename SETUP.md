<<<<<<< HEAD
Setup and run instructions

Windows (PowerShell)
---------------------

Follow these steps to run this repository locally on Windows using PowerShell.
These instructions create and use a Python virtual environment under the
project folder, install dependencies from `requirements.txt`, and show how to
run the CLI and tests.

1) Open PowerShell and change to the repo folder

```powershell
Set-Location 'C:to the path
```

2) Create and activate a virtual environment (PowerShell)

```powershell
# create
python -m venv .venv
# activate (PowerShell)
.\.venv\Scripts\Activate.ps1
```

3) Upgrade pip and install requirements

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4) (Optional) Set GITHUB_TOKEN to avoid rate limits from the GitHub API

```powershell
# create a GitHub personal access token (no special scopes required for public repo reads)
# then in your shell (PowerShell):
$Env:GITHUB_TOKEN = 'ghp_your_token_here'
```

5) Run the CLI

```powershell
# default: interactive menu (Windows)
.\run

# run the CLI against a file of URLs (one URL per line)
.\run urls.txt

# score a single URL directly
python -m cli.main --url https://huggingface.co/bert-base-uncased
```

6) Run the tests

```powershell
# run the project tests for this repo using the Windows wrapper
.\run test

# or run pytest directly inside the venv
pytest -q
```

7) Deactivate the virtualenv when done

```powershell
deactivate
```

Troubleshooting (Windows)
- If you see GitHub API 403 responses, set `GITHUB_TOKEN` as shown above.
- If PowerShell prevents activation due to script execution policy, run
  PowerShell as Administrator and allow the script for this session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

--------------------------------------------------------------------------------

macOS (zsh)
-----------
=======
Setup and run instructions (macOS / Linux / Windows)
>>>>>>> 4e5cd2f6ab79e343b16bf9008acf2a7f3920ad27

This document explains how to run the repository locally on macOS/Linux
using zsh/bash and on Windows (PowerShell or Command Prompt). The
instructions create an isolated Python virtual environment, install
dependencies from `requirements.txt`, and show how to run the CLI and
tests.

Note: Some packages (for example PyTorch) provide platform-specific
wheels. On Windows you may need to follow the vendor install instructions
for the correct CPU/CUDA build. See the "Troubleshooting" section below.

1) Open a terminal and change to the repo folder

macOS / Linux (example):

```bash
<<<<<<< HEAD
cd /path/to/Phase2SWE
=======
cd /path/to/phase2/repo2
```

Windows (example):

PowerShell:

```powershell
cd 'C:\path\to\phase2\repo2'
```

Command Prompt (cmd.exe):

```cmd
cd C:\path\to\phase2\repo2
>>>>>>> 4e5cd2f6ab79e343b16bf9008acf2a7f3920ad27
```

2) Create and activate a virtual environment

macOS / Linux:

```bash
# create
python3 -m venv .venv
# activate (zsh / bash)
source .venv/bin/activate
```

Windows PowerShell:

```powershell
# create
python -m venv .venv
# activate (PowerShell)
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt (cmd.exe):

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

3) Upgrade pip and install requirements

macOS / Linux / Windows (inside the activated virtualenv):

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If you need a specific PyTorch build on Windows, follow the instructions
at https://pytorch.org to pick the correct wheel (CPU vs CUDA).

Example (CPU-only) install on Windows inside an activated venv:

```powershell
python -m pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

If you need CUDA-enabled PyTorch, use the selector on the PyTorch site to
generate the correct `pip` command for your CUDA version.

4) (Optional) Set GITHUB_TOKEN to avoid rate limits from the GitHub API

macOS / Linux / PowerShell (temporary for session):

```bash
# create a GitHub personal access token (no special scopes required for public repo reads)
# then in your shell (bash / zsh / PowerShell):
export GITHUB_TOKEN=ghp_your_token_here    # macOS / Linux / bash
$env:GITHUB_TOKEN = 'ghp_your_token_here'  # PowerShell
```

Windows Command Prompt (cmd.exe):

```cmd
set GITHUB_TOKEN=ghp_your_token_here
```

If you want to persist the token on Windows you can use `setx` (note that
setx changes persist for new shells):

```cmd
setx GITHUB_TOKEN "ghp_your_token_here"
```

5) Run the CLI

macOS / Linux:

```bash
# default: interactive menu
./run

# run the CLI against a file of URLs (one URL per line)
./run urls.txt

# score a single URL directly
python3 -m cli.main --url https://huggingface.co/bert-base-uncased
```

Windows (PowerShell / cmd):

```powershell
# run the CLI (use python to launch the module)
python -m cli.main

# score using a file of URLs
python -m cli.main --file urls.txt

# score a single URL
python -m cli.main --url https://huggingface.co/bert-base-uncased
```

Alternatively, this repository includes Windows wrappers that mirror the
Unix `./run` helper. From the repo root you can use:

PowerShell:

```powershell
.\run.ps1 urls.txt   # run with a URL file
.\run.ps1            # interactive menu
```

Command Prompt:

```cmd
run.bat urls.txt
run.bat
```

6) Run the tests

macOS / Linux:

```bash
# run the project tests for this repo
./run test

# or run pytest directly
pytest -q
```

Windows (PowerShell / cmd):

```powershell
python -m pytest -q
```

7) Deactivate the virtualenv when done

macOS / Linux:

```bash
deactivate
```

Windows (PowerShell / cmd):

```powershell
deactivate
```

Troubleshooting
- If you see GitHub API 403 responses, set `GITHUB_TOKEN` as shown above.
- If pip install fails for any package, copy the failing package name and
  install it manually to see the error. Some dev tools (flake8, mypy)
  may require optional system libraries on older OSes.
- On Windows, PyTorch should be installed using the official wheel for
  your Python and CUDA configuration. See https://pytorch.org for
  platform-specific instructions.
 - PowerShell script execution may be restricted by policy. If you see
   an error when activating the venv with `Activate.ps1`, check your
   policy with:

  ```powershell
  Get-ExecutionPolicy -Scope CurrentUser
  ```

  To allow local activation scripts for the current user run (PowerShell
  as Admin is not required for CurrentUser scope):

  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

  If you prefer not to change policy, use the cmd activation script:

  ```cmd
  .venv\Scripts\activate.bat
  ```

 - If you prefer a Unix-like terminal on Windows, consider using WSL
   (recommended) or Git Bash. Running `./run` will work under WSL or
   Git Bash, since they provide a bash environment.

That's it — you should now be able to run the CLI locally and run the
<<<<<<< HEAD
tests in an isolated virtual environment.

````
=======
tests in an isolated virtual environment on macOS, Linux, or Windows.
>>>>>>> 4e5cd2f6ab79e343b16bf9008acf2a7f3920ad27
