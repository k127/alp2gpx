# alp2gpx

AlpineQuest TRK ➜ GPX converter, ported from flipflip’s original Perl implementation to Python.

## Features
- Parses AlpineQuest TRK v3 and v4 (metadata, segments, waypoints) and writes GPX 1.1.
- Optional AlpineQuest trackpoint extensions (`aq:` namespace) to preserve accuracy, satellites, network, battery, and related metadata.
- Optional `pyproj` support for improved elevation (downloads geoid grid on first use).
- CLI entrypoint `alp2gpx` with single-file and batch modes.
- Optional GeoJSON export of trackpoints (with extras) for quick slippy-map viewing.

## Installation
- With uv (recommended): `uv sync` to install locally; add `--group pyproj` if you want `pyproj` included.
- Plain pip: `pip install -e .` and optionally `pip install '.[pyproj]'` for elevation refinement.

## Usage
Single file:
```shell
uv run alp2gpx path/to/input.trk -o path/to/output.gpx
# output defaults to <input>.gpx if -o/--output is omitted
```

Include AlpineQuest extensions:
```shell
uv run alp2gpx --aq-extensions path/to/input.trk -o out.gpx
```

GeoJSON for mapping:
```shell
uv run alp2gpx --aq-extensions path/to/input.trk --points-geojson dist/points.geojson
```
Append into an existing GeoJSON (grows across runs):
```shell
uv run alp2gpx --aq-extensions path/to/input.trk --points-geojson dist/all.geojson --append-points-geojson
```
Batch GeoJSON per file (directory expected):
```shell
uv run alp2gpx --batch-dir path/to/tracks --out-dir dist/converted --points-geojson dist/geojson
```
Batch merged GeoJSON (single file collects all tracks):
```shell
uv run alp2gpx --batch-dir path/to/tracks --out-dir dist/converted --points-geojson dist/all.geojson
# make it cumulative across batches
uv run alp2gpx --batch-dir path/to/tracks --out-dir dist/converted --points-geojson dist/all.geojson --append-points-geojson
```

Summary only (no GPX written):
```shell
uv run alp2gpx --summary-only path/to/input.trk
# prints version and header info
```

Batch conversion and scanning:
```shell
# List versions/headers under a directory
uv run alp2gpx --batch-dir path/to/tracks --summary-only

# Convert all TRKs under a directory (recursive) into dist/converted
uv run alp2gpx --batch-dir path/to/tracks --out-dir dist/converted

# Limit how many files are processed
uv run alp2gpx --batch-dir path/to/tracks --out-dir dist/converted --limit 2
# GeoJSON per file (directory expected)
uv run alp2gpx --batch-dir path/to/tracks --out-dir dist/converted --points-geojson dist/geojson
```

AlpineQuest extensions emit under `xmlns:aq="https://alpinequest.net/xmlschemas/gpx/trackpoint/1"` and include fields like accuracy, satellites (gps/glo/bds/gal), battery, network signal/type, and vertical accuracy when present.
Track segments also emit metadata (e.g., activity type) under `<trkseg><extensions><aq:segmentMeta>`.

Progress: add `--progress` to print a simple trackpoint counter to stderr during parsing.
Pretty-print GPX: add `--pretty` to indent XML output (handy for diffing).
Accuracy contours: add `--accuracy-contours` to emit left/right tracks offset by horizontal accuracy.
Verbosity: `-v` prints loc/seg/wpt counts; `-vv` also adds length/elevation gain/duration in the status line.

## AlpineQuest GPX extensions
- Enable with `--aq-extensions`; defaults to off for backward-compatible GPX.
- Namespace: `xmlns:aq="https://alpinequest.net/xmlschemas/gpx/trackpoint/1"`.
- Per-trackpoint `<extensions>` include: `aq:accuracy`, `aq:accuracyVertical`, `aq:satellites` (gps/glo/bds/gal), `aq:battery`, `aq:network` (signalPercent/signalDbm/type), `aq:inclination`, `aq:magneticField`, plus optional pressure/elevation sources when available.

## Tips
- Elevation: install `pyproj` (see above). The first run may download `us_nga_egm96_15.tif` for geoid corrections.
- Legacy LDK parsing exists but GPX output currently targets TRK workflows.

## Developer notes
- Profiling: `uv run python -m cProfile -o /tmp/profile.out -m alp2gpx path/to/input.trk -o /tmp/out.gpx` (optionally add `--aq-extensions`). Inspect with `uv run python -m pstats /tmp/profile.out` then run `sort cumulative` + `stats 10`.
- `python -m alp2gpx` works because `__main__.py` forwards to the CLI entry point; use this form for tooling that requires module execution.
- Automated profiling from CLI: use `--profile-out path/to/file` for a single conversion to emit cProfile stats while running the command.
- Quick viewer: generate GeoJSON as above, put it next to `viewer.html`, then run `python -m http.server` and open `http://localhost:8000/viewer.html` (or use the file picker in the page).

## Acknowledgements
Based on flipflip’s apq2gpx; thanks to @dhicks for TRK v4 parsing and I/O args, and @ydespond for elevation/timestamp improvements. Special thanks to the AlpineQuest community and “Amici Alpinisti.” 
