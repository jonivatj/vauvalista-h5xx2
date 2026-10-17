"""Build data.json for the public page from an ArtifactData dump.

Usage: python3 tools/snapshot.py <dump_dir> <output data.json>
<dump_dir> holds items/*.json, suggestions/*.json and meta/status.json
as written by ArtifactData list/get with out_dir.
Notes and internal fields are left out on purpose: only whitelisted fields are copied.
"""
import json, sys, glob, os
from datetime import datetime, timezone

dump, out = sys.argv[1], sys.argv[2]

def load(pattern):
    res = []
    for p in sorted(glob.glob(os.path.join(dump, pattern))):
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        d["_id"] = os.path.splitext(os.path.basename(p))[0]
        res.append(d)
    return res

def pick(d, keys):
    return {k: d[k] for k in keys if isinstance(d, dict) and d.get(k) not in (None, "", [])}

def alt_out(a):
    x = pick(a, ["model", "variant", "price", "shop", "url", "caveat"])
    x["offers"] = [pick(o, ["shop", "price", "url", "checked", "note"]) for o in a.get("offers") or []]
    x["history"] = [pick(h, ["date", "price"]) for h in (a.get("history") or [])][-40:]
    t = a.get("tori")
    if isinstance(t, dict):
        x["tori"] = pick(t, ["checked", "range", "warning"])
        if isinstance(t.get("pick"), dict):
            x["tori"]["pick"] = pick(t["pick"], ["title", "price", "location", "date", "condition", "url", "why"])
    return x

items = []
for it in load("items/*.json"):
    x = pick(it, ["name", "status", "method", "timing", "kela", "paidPrice"])
    alts = it.get("alts") if isinstance(it.get("alts"), list) and it.get("alts") else [it]  # older items kept the model fields at top level
    x["alts"] = [alt_out(a) for a in alts if isinstance(a, dict)]
    for k in ("favorite", "chosen"):
        if isinstance(it.get(k), int) and 0 <= it[k] < len(x["alts"]):
            x[k] = it[k]
    items.append(x)

suggs = [pick(s, ["name", "category", "timing", "kela", "note", "order"]) for s in load("suggestions/*.json")]

meta = {}
mp = os.path.join(dump, "meta", "status.json")
if os.path.exists(mp):
    with open(mp, encoding="utf-8") as f:
        m = json.load(f)
    meta = pick(m, ["lastRun", "campaigns"])

data = {"generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": items, "suggestions": suggs, "meta": meta}
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print(f"{len(items)} tuotetta, {len(suggs)} ehdotusta -> {out}")
