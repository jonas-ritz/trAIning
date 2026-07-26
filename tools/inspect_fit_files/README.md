# Inspecting FIT files

> Repo path: `tools/inspect_fit_files/README.md`

Phase 0 exploration tools. They read raw Garmin `.fit` files and print what's inside, so you can
check the data model against real data. **Not part of the app** — real FIT parsing happens in C#
later. This is just for exploration purposes; findings are written up in [`docs/reference/fit-fields.md`](../../docs/reference/fit-fields.md).

| Script | For | Reads |
|---|---|---|
| `inspect_strength.py` | Gym sessions | frame name: `set` (reps, weight, exercise) |
| `inspect_cardio.py` | Runs, rides, swims, ... | frame name: `record` messages (HR, speed over time) |

Both read the same type of file `.fit`; they just focus on different parts.

## Setup (once)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # if blocked: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
pip install fitdecode
```

## 1. Download the files

```powershell
python .\.venv\Scripts\garmindb_cli.py --all --download --latest
```

Parameters:
- `--all` — every data type (activities, monitoring, sleep, resting HR, weight). Use `--activities`
  to limit it to workouts (i.e. no sleep, no monitoring, ...)
- `--download` — fetch the raw files from Garmin. **On its own it does *not* touch SQLite**, which is
  all you need in case you want to use the scripts in this directory 
- `--import --analyze` is used if you also want GarminDB's own database to browse.
- `--latest` — only recent data, not your whole history: the last N activities (`download_latest_activities`
  in the config) and wellness back to the configured start dates. Without it, GarminDB tries to pull
  everything.
- `--overwrite` — (optional) re-download files you already have, e.g. after editing an activity in
  Garmin Connect. Normally omitted.

Files land in `%USERPROFILE%\HealthData\FitFiles\Activities\`, each named after its Garmin activity ID.

## 2. Find the right file

Filenames are just IDs that match the id on the garmin connect URL in the browser. You can extract the ids from there.
If you have used `--import --analyze` as explained above, you can also find the file names in by exploring 
the sqlite database stored in `$HOME\HealthData\DBs` and browse the files inside with your preferred tool.

## 3. Inspect it

```powershell
python inspect_strength.py "$HOME\HealthData\FitFiles\Activities\<file>.fit"   # gym
python inspect_cardio.py   "$HOME\HealthData\FitFiles\Activities\<file>.fit"   # run / ride / swim
```

A run has no sets and a gym session has no laps — that's expected, not an error. These scripts only
*show* data; writing every sample into the database is the C# parser's job in Phase 2.

If you want to explore further, I propose to consider using `--import --analyze` as explained above, so you can also explore 
the sqlite databases themselves stored in `$HOME\HealthData\DBs` and browse the files inside with your preferred tool.