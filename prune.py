from datetime import datetime, timedelta
import json


KEEP_LATEST = timedelta(days=50)
PRUNE_GAP = timedelta(days=7)

today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

with open("results.json", "r+") as f:
    old_data = json.load(f)
    data = []

    last_kept = None
    for entry in old_data:
        date = datetime.strptime(entry[0], "%Y-%m-%d")
        delta = today - date
        if delta > KEEP_LATEST:
            if last_kept is None:
                last_kept = date
            elif (date - last_kept) > PRUNE_GAP:
                last_kept = None
            else:
                continue

        data.append(entry)

sorted(data, key=lambda x: x[0])

with open("results.json", "w") as f:
    json.dump(data, f, indent=4)
