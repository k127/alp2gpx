# alp2gpx

AlpineQuest TRK ➜ GPX converter, ported from flipflip’s original Perl implementation to Python.

## Features
- Parses AlpineQuest TRK v3 and v4 (metadata, segments, waypoints) and writes GPX 1.1.
- Optional `pyproj` support for improved elevation (downloads geoid grid on first use).
- CLI entrypoint `alp2gpx` with single-file and batch modes.

## Installation
- With uv (recommended): `uv sync` to install locally; add `--group pyproj` if you want `pyproj` included.
- Plain pip: `pip install -e .` and optionally `pip install '.[pyproj]'` for elevation refinement.

## Usage
Single file:
```shell
uv run alp2gpx path/to/input.trk -o path/to/output.gpx
# output defaults to <input>.gpx if -o/--output is omitted
```

Summary only (no GPX written):
```shell
uv run alp2gpx --summary-only path/to/input.trk
# prints version and header info
```

Batch conversion and scanning:
```shell
# List versions/headers under a directory
uv run alp2gpx --batch-dir data --summary-only

# Convert all TRKs under a directory (recursive) into dist/converted
uv run alp2gpx --batch-dir data --out-dir dist/converted

# Limit how many files are processed
uv run alp2gpx --batch-dir data --out-dir dist/converted --limit 2
```

## Tips
- Elevation: install `pyproj` (see above). The first run may download `us_nga_egm96_15.tif` for geoid corrections.
- Legacy LDK parsing exists but GPX output currently targets TRK workflows.

## Acknowledgements
Based on flipflip’s apq2gpx; thanks to @dhicks for TRK v4 parsing and I/O args, and @ydespond for elevation/timestamp improvements. Special thanks to the AlpineQuest community and “Amici Alpinisti.” 
