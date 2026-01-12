import argparse
import os
from pathlib import Path
from typing import Optional

from .alp2gpx import alp2gpx
from .ops import batch_convert, find_tracks, read_header


def _default_output(input_path: str) -> str:
    return "%s.gpx" % os.path.splitext(input_path)[0]


def _require_input(input_path: Optional[str], batch_dir: Optional[Path]) -> None:
    if not input_path and not batch_dir:
        raise SystemExit("Provide an input file or --batch-dir to process.")


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "input",
        nargs="?",
        help="input file to convert (.trk, etc.)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,  # Handled after parser.parse_args()
        help="output base name (default input file path and base name)",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print TRK header info without producing GPX output.",
    )
    parser.add_argument(
        "--batch-dir",
        type=Path,
        help="Convert all .trk files under this directory (recursive).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("dist/converted"),
        help="Output directory for batch conversion (defaults to dist/converted).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit when running batch conversion.",
    )

    args = parser.parse_args()
    _require_input(args.input, args.batch_dir)

    # Batch workflow: scan versions and optionally convert all tracks.
    if args.batch_dir:
        tracks = find_tracks(args.batch_dir)
        if not tracks:
            raise SystemExit(f"No .trk files found under {args.batch_dir}")

        print(f"Found {len(tracks)} TRK files under {args.batch_dir}")
        batch_convert(
            tracks=tracks,
            out_dir=args.out_dir,
            summary_only=args.summary_only,
            limit=args.limit,
        )
        return

    # Single-file workflow (backwards compatible).
    if args.summary_only:
        version, header = read_header(Path(args.input))
        print(f"{args.input}\tversion={version}\theader={header}")
        return

    if args.output is None:
        args.output = _default_output(args.input)

    alp2gpx(args.input, args.output)
