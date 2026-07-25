# FIT field reference

What Garmin FIT files from a **Forerunner 255** actually contain, established by inspecting real
files in Phase 0. This is lookup material for writing and debugging the FIT parser — the ground
truth the data model is built on.

## Message types → data model

| FIT message | Maps to | Notes |
|---|---|---|
| `session` | `Activity` (core) | One per file. Sport, sub-sport, duration, distance, avg/max HR. |
| `record` | `ActivitySample` | Per-second. **Present even in strength sessions** (~1584 in a 50-min gym session). |
| `lap` | `ActivityLap` | Cardio structure. **Absent in strength sessions** — laps are a cardio construct. |
| `set` | `StrengthSet` | Strength only. Active sets and rest periods interleaved. |

Plus `time_in_zone`, `device_info`, `event`, and a lot of `unknown_*` messages (Garmin-internal,
ignored).

## Strength sets — the important findings

A `set` message with `set_type = active` is a working set; `set_type = rest` is a rest period.
Roughly half the `set` messages are rests.

Fields on an active set:

| Field | Example | Meaning / caution |
|---|---|---|
| `set_type` | `active` / `rest` | Filter rests out of working-set counts. |
| `repetitions` | `6`, `12` | **Reliably recorded by the watch.** |
| `weight` | `None`, `0.0`, `52.0` | **Three distinct states — do not merge (see below).** |
| `category` | `(65534, 7, 0)` | Exercise, as a FIT enum tuple. `65534` = Garmin "unknown/custom". Needs decoding. |
| `category_subtype` | `(None, None, None)` | Often empty. |
| `duration` | `93.09` | Seconds. |
| `start_time`, `timestamp` | ISO datetime | Set ordering. |

### `weight` has three states — this drives the model

| Raw value | Meaning | Model representation |
|---|---|---|
| `None` | Nothing entered (watch can't measure load) | `WeightKg = null` |
| `0.0` | Deliberate — bodyweight, or "0" typed | `WeightKg = 0`, `IsBodyweight = true` |
| `52.0` | Real entered load | `WeightKg = 52` |

Merging `None` and `0.0` corrupts tonnage. This is the whole reason `WeightKg` is nullable and
`IsBodyweight` exists — see [ADR-0011](../adr/0011-manual-weight-entry.md).

### Exercise decoding

`category` is a FIT enum tuple, not a readable name. The mapping (enum → "Bench Press" etc.) is
defined in the **Garmin FIT SDK** (`exercise_names` / the profile enums), not something to guess.
The parser reads that mapping from the SDK; `65534` and other unknowns fall back to a generic label
and are correctable by the user in the PWA. Tracked as the exercise-vocabulary work in Phase 2/3.

## Sample fields (`record`) present on the FR255

Confirmed carrying data: `heart_rate`, `distance`.
Confirmed **absent / null**: `power` (no power meter), and `cadence`/`speed`/`altitude` vary by
sport. Don't build non-nullable columns for fields the device doesn't provide.

## Practical implications for the parser

- Filter `set_type = rest` out of working-set metrics, but keep rest durations — they characterize
  the session (strength vs. hypertrophy).
- Expect `record` data on strength sessions; `ActivitySample` is populated for gym work too.
- Don't expect `lap` on strength; don't treat its absence as an error.
- Treat `weight = 0.0` and `weight = None` as different at parse time, before anything downstream.
