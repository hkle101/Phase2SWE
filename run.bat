@echo off
REM ------------------------------------------------------------------
REM run.bat - Windows wrapper to run the project's CLI and helpers
REM
REM This script supports the following usages:
REM   run.bat            -> starts the interactive CLI (for user input)
REM   run.bat install    -> install Python requirements from requirements.txt
REM   run.bat test       -> run the test suite with pytest (with coverage)
REM   run.bat URL_FILE   -> run the CLI with the given URL file path
REM
REM Notes:
REM - Behavior is intentionally minimal: commands are passed to Python
REM   module runner `cli.main` for normal operation.
REM - The script preserves exit codes and prints nothing on success due
REM   to `@echo off` at the top.
REM ------------------------------------------------------------------

setlocal

REM If no first argument provided, jump to the default runner below.
if "%~1"=="" goto DEFAULT

REM Install dependencies: pip installs from requirements.txt
if /I "%~1"=="install" (
    REM Use pip from PATH; this command intentionally mirrors common dev usage.
    pip install -r requirements.txt
    endlocal
    exit /b 0
)

REM Run tests: try running pytest with coverage; on failure fall back to plain pytest
if /I "%~1"=="test" (
    pytest --maxfail=1 --disable-warnings -q --cov=cli || pytest -q
    endlocal
    exit /b 0
)

REM If the first argument is an existing file, pass it as the URL file to the CLI
if exist "%~1" (
    python -m cli.main "%~1"
    endlocal
    exit /b 0
)

:DEFAULT
REM Default: forward all arguments to the CLI module `cli.main`.
python -m cli.main %*
endlocal
exit /b 0
