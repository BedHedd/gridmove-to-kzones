#!/usr/bin/env python3
"""
Convert GridMove templates (.ini-like text) to KZones layout JSON.

Repo layout (expected):
  01-paste-grids-here/
  02-run-this-script/convert_gridmove_to_kzones.py   <-- run me
  03-kzone-output/

Usage (interactive picker):
  python3 convert_gridmove_to_kzones.py

Non-interactive:
  python3 convert_gridmove_to_kzones.py --index 1
  python3 convert_gridmove_to_kzones.py --file ../01-paste-grids-here/xipergrid2.ini
"""
from __future__ import annotations
import argparse, re, json, sys, os
from pathlib import Path
from typing import List, Dict

# ---------- Repo helpers --------------------------------------------------------

def repo_root_from_script() -> Path:
    # .../02-run-this-script/convert.py -> repo root is parent of parent
    return Path(__file__).resolve().parent.parent

def input_dir(root: Path) -> Path:
    return root / "01-paste-grids-here"

def output_dir(root: Path) -> Path:
    return root / "03-kzone-output"

def rel_to_root(p: Path, root: Path) -> str:
    try:
        return p.relative_to(root).as_posix()
    except ValueError:
        return os.path.relpath(str(p), str(root)).replace(os.sep, "/")

# ---------- GridMove parser / converter ----------------------------------------

# Treat monitor as percentage space: origin (0,0), size (100,100)
VARS = {
    'Monitor1Left':   0.0,
    'Monitor1Top':    0.0,
    'Monitor1Width':  100.0,
    'Monitor1Height': 100.0,
    'Monitor1Right':  100.0,
    'Monitor1Bottom': 100.0,
}

SAFE_PATTERN = re.compile(r'^[A-Za-z0-9_\.\+\-\*\/\(\)\s]+$')

def safe_eval(expr: str) -> float:
    # Replace [Name] -> Name and evaluate with restricted globals
    expr = expr.replace('[','').replace(']','')
    if not SAFE_PATTERN.fullmatch(expr):
        raise ValueError(f"Unsafe/unsupported expression: {expr}")
    return float(eval(expr, {"__builtins__": None}, VARS))

def clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))

def parse_groups(text: str) -> List[Dict[str, str]]:
    groups = []
    cur: Dict[str,str] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(';'):
            continue
        m = re.match(r'^\[(\d+)\]', line)
        if m:
            if cur: groups.append(cur)
            cur = {}
            continue
        if cur is None:
            continue
        kv = re.match(r'^(GridTop|GridBottom|GridLeft|GridRight)\s*=\s*(.+)$', line)
        if kv:
            cur[kv.group(1)] = kv.group(2)
    if cur: groups.append(cur)
    return groups

def convert(groups: List[Dict[str,str]]):
    zones = []
    for g in groups:
        if not all(k in g for k in ("GridLeft","GridRight","GridTop","GridBottom")):
            continue
        L = safe_eval(g["GridLeft"])
        R = safe_eval(g["GridRight"])
        T = safe_eval(g["GridTop"])
        B = safe_eval(g["GridBottom"])
        x = clamp(min(L, R))
        y = clamp(min(T, B))
        w = clamp(max(L, R)) - x
        h = clamp(max(T, B)) - y
        x, y = clamp(x), clamp(y)
        w, h = clamp(w), clamp(h)
        if w > 0 and h > 0:
            zones.append({"x": round(x,3), "y": round(y,3), "width": round(w,3), "height": round(h,3)})
    # dedupe by coordinates
    uniq = []
    seen = set()
    for z in zones:
        key = (z["x"], z["y"], z["width"], z["height"])
        if key not in seen:
            seen.add(key)
            uniq.append(z)
    return uniq

def make_layout(zones, name: str):
    return [{
        "name": f"{name} (converted)",
        "padding": 0,
        "zones": zones
    }]

# ---------- File selection & I/O -----------------------------------------------

def find_ini_files(indir: Path):
    # Prefer .ini/.txt; if none, list any files
    files = sorted([p for p in indir.glob("*") if p.is_file() and p.suffix.lower() in (".ini", ".txt")])
    if not files:
        files = sorted([p for p in indir.glob("*") if p.is_file()])
    return files

def choose_file(files):
    print("\nFound these files in 01-paste-grids-here:")
    for i, p in enumerate(files, 1):
        print(f"  {i:2d}. {p.name}")
    while True:
        choice = input(f"Select file [1-{len(files)}] (q to quit): ").strip().lower()
        if choice in ("q", "quit", "exit"):
            sys.exit(0)
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(files):
                return files[idx-1]
        print("Invalid choice, try again.")

def convert_file(src_path: Path, outdir: Path, root: Path) -> Path:
    text = src_path.read_text(encoding="utf-8", errors="ignore")
    groups = parse_groups(text)
    zones = convert(groups)
    layout = make_layout(zones, src_path.stem)
    outdir.mkdir(parents=True, exist_ok=True)
    dst = outdir / f"{src_path.stem}_kzones.json"
    dst.write_text(json.dumps(layout, indent=2), encoding="utf-8")

    dst_rel = rel_to_root(dst, root)
    print(f"\nConverted: {src_path.name}")
    print(f"  Groups parsed: {len(groups)}")
    print(f"  Zones generated (deduped): {len(zones)}")
    print(f"  Output (relative to project): {dst_rel}")
    return dst

# ---------- CLI ----------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description="GridMove → KZones converter")
    parser.add_argument("--index", type=int, help="Pick file by index from 01-paste-grids-here (1..N)")
    parser.add_argument("--file", type=str, help="Explicit file path")
    args = parser.parse_args(argv)

    root = repo_root_from_script()
    indir = input_dir(root)
    outdir = output_dir(root)

    if args.file:
        src = Path(args.file)
        if not src.is_absolute():
            src = (Path.cwd() / src).resolve()
        if not src.exists():
            print(f"File not found: {src}")
            sys.exit(1)
        convert_file(src, outdir, root)
        return

    files = find_ini_files(indir)
    if not files:
        print(f"No files found in: {indir}")
        print("Put your GridMove .ini files there and re-run.")
        sys.exit(1)

    if args.index is not None:
        idx = args.index
        if not (1 <= idx <= len(files)):
            print(f"--index must be between 1 and {len(files)}")
            sys.exit(1)
        src = files[idx-1]
    else:
        src = choose_file(files)

    convert_file(src, outdir, root)

if __name__ == "__main__":
    main()
