#!/usr/bin/env python3
# deploy.py  —  run from C:\dev\ec-repo :   python deploy.py
# Swaps in the qa_handoff image tree, builds a self-describing session_base.csv,
# protects the 75MB zip from being committed, and verifies before you push.
import os, csv, io, shutil, zipfile, sys

HZIP = "qa_handoff.zip"
H    = "qa_handoff"
FOLDERS = ["REGULATORY_SIGNS","WARNING_SIGNS","DESTINATION_SIGNS","ROUTE_MARKER_SIGNS",
           "FREEWAY_AND_EXPRESSWAY_SIGNS","MOTORIST_SERVICES","GENERAL_INFORMATION",
           "SCHOOL_SIGNS","EMERGENCY_MANAGEMENT_SIGNS","CONSTRUCTION_INFORMATION_SIGNS","_NEW_VERSIONS"]

def rd(p):
    return list(csv.DictReader(io.StringIO("".join(l for l in open(p, encoding="utf-8") if not l.startswith("#")))))

# ---- 0. sanity + index.html freshness ----
if not os.path.exists("index.html"):   sys.exit("STOP: run from the repo root (no index.html here).")
if not os.path.isdir("word_images"):   sys.exit("STOP: word_images/ missing — do not proceed (the Word pane needs it).")
if "lbStage" not in open("index.html", encoding="utf-8", errors="ignore").read():
    print("!! WARNING: index.html has no zoom lightbox — it looks like an OLDER build.")
    print("!! Replace it with the latest index.html before pushing, or the live tool won't have zoom.\n")

# ---- 1. protect the zip, extract the handoff ----
gi = ".gitignore"; lines = open(gi, encoding="utf-8").read().splitlines() if os.path.exists(gi) else []
for e in ("qa_handoff.zip", "qa_handoff/"):
    if e not in lines: lines.append(e)
open(gi, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("gitignore: qa_handoff.zip + qa_handoff/ excluded from commits")

if not os.path.isdir(H):
    if not os.path.exists(HZIP): sys.exit("STOP: neither qa_handoff/ nor qa_handoff.zip found.")
    with zipfile.ZipFile(HZIP) as z: z.extractall(".")
    print("extracted", HZIP)

# locate the real handoff root (zip may or may not nest a top folder)
root = H
if not os.path.isdir(os.path.join(root, "REGULATORY_SIGNS")):
    root = None
    for dp, dns, fns in os.walk("."):
        if "REGULATORY_SIGNS" in dns and "session_base_corrected.csv" in fns:
            root = dp; break
    if not root: sys.exit("STOP: could not find the handoff root (REGULATORY_SIGNS + session_base_corrected.csv).")
print("handoff root:", root)

# ---- 2. swap the image folders ----
for d in FOLDERS:
    src = os.path.join(root, d)
    if not os.path.isdir(src): print("  WARN not in handoff:", d); continue
    if os.path.isdir(d): shutil.rmtree(d)
    shutil.copytree(src, d)
    print(f"  replaced {d:34} {len(os.listdir(d))} files")

nvfiles = set(os.listdir("_NEW_VERSIONS")) if os.path.isdir("_NEW_VERSIONS") else set()

# ---- 3. build self-describing session_base.csv (strip internal cols) ----
corr = rd(os.path.join(root, "session_base_corrected.csv"))
try:    rec = rd(os.path.join(root, "reconciliation_word_categories.csv"))
except Exception: rec = []
h = lambda s, x: x in (s or "").lower()
tag_by_key  = {(r.get("mutcd_code"), r.get("output_file")): r.get("tag","") for r in rec}
tag_by_code = {}
for r in rec: tag_by_code.setdefault(r.get("mutcd_code"), r.get("tag",""))
subtype = lambda t: next((s for s in ("street-name","bicycle-facility","destination") if h(t, s)), "")

DROP = {"platform_db_name", "shared_with", "name_status"}
base_cols = [c for c in corr[0].keys() if c not in DROP]
cols = []
for c in base_cols:
    cols.append(c)
    if c == "category"  and "sub_type"    not in cols: cols.append("sub_type")
    if c == "hq_status" and "new_version" not in cols: cols.append("new_version")
for e in ("sub_type", "new_version"):
    if e not in cols: cols.append(e)

out = []
for r in corr:
    fi = r.get("folder_image", ""); b = os.path.basename(fi) if fi else ""
    tag = tag_by_key.get((r.get("mutcd_code"), b)) or tag_by_code.get(r.get("mutcd_code"), "")
    row = {k: v for k, v in r.items() if k not in DROP}
    # sub_type: keep if already present, else derive from reconciliation tag
    row["sub_type"] = r.get("sub_type") or subtype(tag)
    # new_version: authoritative = the file is present in _NEW_VERSIONS/
    row["new_version"] = "true" if (b and b in nvfiles) else ""
    out.append(row)

with open("session_base.csv", "w", newline="", encoding="utf-8") as f:
    f.write("# base_commit,seed\n")
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in out: w.writerow({c: r.get(c, "") for c in cols})

sub_n = sum(1 for r in out if r["sub_type"]); nv_n = sum(1 for r in out if r["new_version"])
print(f"session_base.csv: {len(out)} rows | sub_type {sub_n} | new_version {nv_n} | cols {len(cols)}")

# ---- 4. verify ----
miss = [r["folder_image"] for r in out if r.get("folder_image") and not os.path.exists(r["folder_image"])]
leak = any(("platform" in c or "shared_with" in c) for c in cols)
if not os.path.exists(".nojekyll"): open(".nojekyll", "w").close(); print("created .nojekyll")
print("\nVERIFY  missing_images=%d  new_version=%d  _NEW_VERSIONS=%d  word_images=%s  internal_leak=%s"
      % (len(miss), nv_n, len(nvfiles), os.path.isdir("word_images"), leak))
for m in miss[:15]: print("  MISSING", m)
if miss or nv_n != 11 or leak or not os.path.isdir("word_images"):
    sys.exit("\n*** STOP: fix the above before committing. ***")
print("\nOK — clean. Next: git add -A  ->  git status (confirm qa_handoff.zip NOT listed)  ->  commit  ->  push")
