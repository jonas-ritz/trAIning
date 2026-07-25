# GarminDB — local setup

How to run GarminDB by hand, for the Phase 0 spike and for debugging the collector later. In
production this runs as a containerized job (see the spec's architecture section); this page is the
local/manual version.

GarminDB is used as a **downloader only** — the `--download` stage. Its SQLite schema is never used
by this project; FIT parsing happens in C#. See [ADR-0001](../adr/0001-garmindb-as-primary-source.md).

## Install

```powershell
mkdir garmin-spike; cd garmin-spike
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # if blocked: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
pip install garmindb fitdecode
```

## Configure

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.GarminDb"
Copy-Item ".\.venv\Lib\site-packages\garmindb\GarminConnectConfig.json.example" `
          "$HOME\.GarminDb\GarminConnectConfig.json"
notepad "$HOME\.GarminDb\GarminConnectConfig.json"
```

Set in the file:
- **Garmin Connect username and password.** (The account has no 2FA, so login can be automated.)
- **Start dates** — for the first run, set these about a week back, not to your first Garmin year,
  or the download takes forever:
  ```json
  "sleep_start_date": "...", "rhr_start_date": "...",
  "monitoring_start_date": "...", "weight_start_date": "..."
  ```
- **Activity count** — activities are count-driven, not date-driven (this tripped up ADR-0007; see
  its correction). The relevant keys:
  ```json
  "download_latest_activities": 25,
  "download_all_activities": 1000
  ```

## Run

```powershell
# Download only — no SQLite. This is what the production collector does.
python .\.venv\Scripts\garmindb_cli.py --all --download

# Full local build incl. SQLite, if you want to browse Garmin's own schema to learn
python .\.venv\Scripts\garmindb_cli.py --all --download --import --analyze

# Incremental (only what's new)
python .\.venv\Scripts\garmindb_cli.py --all --download --latest

# Re-download files you already have (e.g. after editing an activity in Connect)
python .\.venv\Scripts\garmindb_cli.py --activities --download --latest --overwrite
```

Raw files land under `~/HealthData/`. Activities are FIT files in `FitFiles/Activities/`.

## Inspecting what you got

Find a specific activity by its Garmin Connect ID (the number in the activity URL — it's the
filename):

```powershell
Get-ChildItem "$HOME\HealthData\FitFiles\Activities" -Filter "*<activityId>*"
```

Then use the inspection scripts (`inspect_fit.py`, `scan_fit.py` — kept in `tools/`). What the FIT
files actually contain is documented in [`docs/reference/fit-fields.md`](../reference/fit-fields.md).

## Gotchas

- **Windows script wrapper.** If `garmindb_cli.py` fails with `ImportError: No module named garmindb`,
  call it via the venv's python explicitly (as above) or ensure the venv `Scripts` dir is on PATH.
- **First run is slow** proportional to the start dates. Keep the window small for the spike.
- **`--overwrite` is needed** to re-pull an activity you already downloaded — `--latest` skips
  existing files.
