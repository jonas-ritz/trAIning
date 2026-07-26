"""
inspect_strength.py — inspect a FIT file, focusing on STRENGTH training.

Both inspect_strength.py and inspect_cardio.py read the same kind of file
(a Garmin .fit activity file). They differ only in what they focus on:

    inspect_strength.py  ->  "set" messages   (sets, reps, weight)   <-- this one
    inspect_cardio.py    ->  "record" messages (HR, speed over time)

A FIT file is a sequence of small "messages", each with a name and some fields.
This script walks through them, counts the types, and shows the strength sets,
so you can confirm your StrengthSet data model matches what the watch records.

example file for biking: $HOME\HealthData\FitFiles\Activities\23692195364_ACTIVITY.fit

Usage:  python inspect_strength.py <path-to-file.fit>
Needs:  pip install fitdecode
"""

import sys
import fitdecode


def main(path):
    # We'll collect the sets we find so we can print them nicely at the end.
    strength_sets = []

    # How many of each message type did we see? Starts empty, we count as we go.
    message_counts = {}

    # Open the file and loop over every message in it.
    with fitdecode.FitReader(path) as fit:
        for frame in fit:
            # Only FitDataMessage frames hold real data; skip the rest.
            if not isinstance(frame, fitdecode.FitDataMessage):
                continue

            # Count this message type. E.g. message_counts["record"] += 1
            message_counts[frame.name] = message_counts.get(frame.name, 0) + 1

            # Turn the message's fields into a plain dict {field_name: value}.
            fields = {f.name: f.value for f in frame.fields}

            # If it's a strength "set" message, remember it for later.
            if frame.name == "set":
                strength_sets.append(fields)

    # ---- What message types were in the file, most common first ----
    print(f"\nFile: {path}\n")
    print("Message types found:")
    for name, count in sorted(message_counts.items(), key=lambda x: -x[1]):
        print(f"  {name:20} {count}")

    # ---- The strength sets, if there were any ----
    if not strength_sets:
        print("\nNo 'set' messages — this isn't a strength session (or the")
        print("watch didn't record sets). For a run or ride, use inspect_cardio.py.")
        return

    print(f"\nFound {len(strength_sets)} set messages:\n")
    for i, s in enumerate(strength_sets, start=1):
        # set_type is "active" (a working set) or "rest".
        # reps/weight may be None — that's meaningful, so show it as-is.
        print(f"  {i:2}. type={s.get('set_type')}   "
              f"reps={s.get('repetitions')}   "
              f"weight={s.get('weight')}   "
              f"exercise={s.get('category')}")

    # ---- Every field of the first set, so you see what a set can hold ----
    print("\nAll fields of the first set (this is what StrengthSet could store):")
    for field_name, value in strength_sets[0].items():
        print(f"  {field_name:22} = {value}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python inspect_strength.py <file.fit>")
    else:
        main(sys.argv[1])