"""
inspect_cardio.py — inspect a FIT file, focusing on CARDIO / endurance training.

Both inspect_strength.py and inspect_cardio.py read the same kind of file
(a Garmin .fit activity file). They differ only in what they focus on:

    inspect_strength.py  ->  "set" messages    (sets, reps, weight)
    inspect_cardio.py    ->  "record" messages (HR, speed over time)   <-- this one

For a run or a ride, the watch writes one "record" message per second, each
holding heart rate, speed, cadence, altitude at that moment. That stream is
your "HR over time", and it's what becomes ActivitySample in the data model.

example file for running: $HOME\HealthData\FitFiles\Activities\23737207897_ACTIVITY.fit
example file for swimming: $HOME\HealthData\FitFiles\Activities\23726453055_ACTIVITY.fit
example file for biking: $HOME\HealthData\FitFiles\Activities\23679801955_ACTIVITY.fit

Usage:  python inspect_cardio.py <path-to-file.fit>
Needs:  pip install fitdecode
"""

import sys
import fitdecode


def main(path):
    records = []   # the per-second samples
    laps = 0       # how many laps (intervals) the file has
    sport = None   # what kind of activity this is

    with fitdecode.FitReader(path) as fit:
        for frame in fit:
            if not isinstance(frame, fitdecode.FitDataMessage):
                continue

            if frame.name == "session":
                # The session message holds the summary/header of the activity.
                if frame.has_field("sport"):
                    sport = frame.get_value("sport")

            elif frame.name == "lap":
                laps += 1

            elif frame.name == "record":
                # One per-second sample. Any field can be missing, so read
                # defensively. These are the fields we care about for cardio.
                sample = {}
                for field in ("timestamp", "heart_rate", "speed",
                              "cadence", "altitude", "distance"):
                    sample[field] = frame.get_value(field) if frame.has_field(field) else None
                records.append(sample)

    # ---- Summary ----
    print(f"\nFile:  {path}")
    print(f"Sport: {sport}")
    print(f"Laps:  {laps}")
    print(f"Records (per-second samples): {len(records)}")

    if not records:
        print("\nNo 'record' messages — nothing time-series here.")
        print("For a gym session, use inspect_strength.py.")
        return

    # ---- Which fields actually carry data? ----
    # (Your FR255 has no power meter, for example, so some fields stay empty.)
    print("\nFields that have at least one non-empty value:")
    for field in ("heart_rate", "speed", "cadence", "altitude", "distance"):
        has_data = any(r[field] is not None for r in records)
        print(f"  {'x' if has_data else ' '} {field}")

    # ---- First and last few samples, so you SEE the HR-over-time ----
    print("\nFirst 5 samples:")
    for r in records[:5]:
        print(f"  {r['timestamp']}  HR={r['heart_rate']}  "
              f"speed={r['speed']}  cadence={r['cadence']}  alt={r['altitude']}")

    print("...")
    print("Last 5 samples:")
    for r in records[-5:]:
        print(f"  {r['timestamp']}  HR={r['heart_rate']}  "
              f"speed={r['speed']}  cadence={r['cadence']}  alt={r['altitude']}")

    # ---- A tiny taste of what the metrics engine will do later ----
    hrs = [r["heart_rate"] for r in records if r["heart_rate"] is not None]
    if hrs:
        print(f"\nHeart rate: min={min(hrs)}  max={max(hrs)}  "
              f"avg={round(sum(hrs) / len(hrs))}  (over {len(hrs)} samples)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python inspect_cardio.py <file.fit>")
    else:
        main(sys.argv[1])