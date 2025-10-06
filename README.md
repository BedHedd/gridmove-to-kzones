# GridMove → KZones Converter

Convert classic **GridMove** templates (`.ini` text like `xipergrid2`) into a **KZones** layout JSON for KWin.
Paste your GridMove files, run one script, then paste the generated JSON into KZones.

## Final output
![preview](00-demos/Grid_Demo.webm)

## What this does (in plain terms)

* Treats your monitor as a **0–100%** canvas in both directions.
* Evaluates each group’s `GridTop/Bottom/Left/Right` math (ignores the `Trigger*` lines).
* Builds a deduplicated set of **zones** KZones can show when you drag a window.
* Exports to `03-kzone-output/<name>_kzones.json`.

---

## Repo layout

```
.
├── 01-paste-grids-here/           # put your GridMove .ini files here
├── 02-run-this-script/
│   └── convert_gridmove_to_kzones.py
└── 03-kzone-output/               # converted KZones JSON will appear here
```

---

## Prereqs

This project is **pure Python stdlib** (no third-party deps). Use whichever setup you prefer:

* Plain system **Python 3.10+** (or 3.12+ if you like)
* **uv** (fast Python package & venv manager) — optional but nice
* **Nix** (flakes or classic) — optional dev shell

---

## Quick start (Plain Python)

```bash
cd 02-run-this-script
python3 convert_gridmove_to_kzones.py          # interactive: pick file by index (1..N)

# Non-interactive:
python3 convert_gridmove_to_kzones.py --index 1
python3 convert_gridmove_to_kzones.py --file ../01-paste-grids-here/xipergrid2.ini
```

Outputs: `../03-kzone-output/xipergrid2_kzones.json`

---

## Quick start (uv)

> If you don’t have uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

```bash
cd 02-run-this-script
uv run python convert_gridmove_to_kzones.py        # interactive picker

# Non-interactive:
uv run python convert_gridmove_to_kzones.py --index 1
uv run python convert_gridmove_to_kzones.py --file ../01-paste-grids-here/xipergrid2.grid
```

*No dependencies to install — `uv run` just gives you an isolated, fast Python.*

---

## Quick start (Nix)

### Flakes (recommended)

Create `flake.nix` at the repo root:

```nix
{
  description = "GridMove → KZones converter dev shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
  let
    systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
    forAllSystems = f: nixpkgs.lib.genAttrs systems (system:
      let pkgs = import nixpkgs { inherit system; };
      in f pkgs
    );
  in {
    devShells = forAllSystems (pkgs: {
      default = pkgs.mkShell {
        packages = [ pkgs.python312 ]; # or python311 if you prefer
      };
    });
  };
}
```

Use it:

```bash
# in repo root
nix develop                 # drops you into a shell with python available
cd 02-run-this-script
python3 convert_gridmove_to_kzones.py
```

### Non-flake `shell.nix` (legacy)

```nix
{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = [ pkgs.python312 ];
}
```

```bash
nix-shell
cd 02-run-this-script
python3 convert_gridmove_to_kzones.py
```

---

## Import into KZones

1. **System Settings → Window Management → KWin Scripts → KZones** (install/enable if needed).
2. Open **KZones → Settings → Layouts**.
3. Open the JSON from `03-kzone-output/…_kzones.json`, copy the content, and **Paste** it into the Layouts editor. Click **Apply**.
4. Drag a window (hold **Shift** if you like); drop into a highlighted zone.

---

## CLI usage

Interactive picker (lists files in `01-paste-grids-here/` and asks for **1..N**):

```bash
python3 convert_gridmove_to_kzones.py
```

Flags:

```bash
# Pick by index (sorted file list from 01-paste-grids-here)
python3 convert_gridmove_to_kzones.py --index 1

# Pick by path (relative or absolute)
python3 convert_gridmove_to_kzones.py --file ../01-paste-grids-here/xipergrid2.ini
```

---

## How the conversion works

* Variables like `[Monitor1Width]` are evaluated in a sandbox as **100.0** (i.e., percentages).
* Expressions such as `[Monitor1Top]+([Monitor1Height]/3)` become `0 + 100/3`.
* Rectangles are clamped to `[0, 100]` and zero-area or duplicate zones are dropped.
* Only these keys are used: `GridTop`, `GridBottom`, `GridLeft`, `GridRight`.
  (GridMove’s `Trigger*` strips aren’t needed for KZones.)

---

## Tips & gotchas

* **Multi-monitor:** KZones applies the layout per screen; the percentage zones scale to each monitor.
* **Too many zones?** Your GridMove template might define many overlapping rectangles. That’s fine—KZones will still show them; you can prune in the JSON if desired.
* **Keyboard vs mouse:** KZones overlay appears when dragging. If you prefer a **keyboard toggle**, set a shortcut in *System Settings → Shortcuts → KZones → Toggle zone overlay*.

---

## Troubleshooting

* **No files found:** Make sure your `.ini` is in `01-paste-grids-here/`.
* **Weird math errors:** The parser only allows numbers, `()+-*/`, dots, and the monitor variables. If your template uses something else, open an issue or ping me to extend the parser.
* **Nothing appears in KZones:** Confirm you pasted the JSON into KZones **Layouts** and hit **Apply**, and that the **KZones** script is **enabled**.