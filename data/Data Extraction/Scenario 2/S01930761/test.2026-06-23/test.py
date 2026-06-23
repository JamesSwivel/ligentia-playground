import json
from collections import defaultdict
import os

scriptDir = f"{os.path.dirname(__file__)}"
print(f"scriptDir: {scriptDir}")

groups = defaultdict(lambda: {
    "qty": 0,
    "cartonQty": 0,
    "grossWeight": 0.0,
    "netWeight": 0.0,
    "cbm": 0.0,
    "rows": [],
})

jsonBaseName = "BV2503-0030 PL.json"

js = json.load(open(os.path.join(scriptDir, jsonBaseName)))
items = js["result"]["jsonData"]["packingListItems"]

for item in items:
    key = (
        item["PONum"],
        item["code"],
        item["extra"]["size"],
        item["extra"]["channel"],
    )

    g = groups[key]
    g["qty"] += item["qty"]
    g["cartonQty"] += item["cartonQty"]
    g["grossWeight"] += item["grossWeight"]
    g["netWeight"] += item["netWeight"]
    g["cbm"] += item["cbm"] 
    g["rows"].append(item)

for key, g in groups.items():
    print(key, g["qty"], g["cartonQty"], g["cbm"])