import argparse
import os
import sys
import cProfile
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
    parser.add_argument(
        "-x",
        "--aq-extensions",
        dest="aq_extensions",
        action="store_true",
        help="Emit AlpineQuest trackpoint metadata as GPX extensions.",
    )
    parser.add_argument(
        "-X",
        "--no-aq-extensions",
        dest="aq_extensions",
        action="store_false",
        help="Disable AlpineQuest GPX extensions (default).",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Print a simple progress ticker while reading trackpoints.",
    )
    parser.add_argument(
        "--profile-out",
        type=Path,
        default=None,
        help="Write a cProfile stats file for a single conversion.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print GPX output (indent XML) for readability.",
    )
    parser.add_argument(
        "--accuracy-contours",
        action="store_true",
        help="Emit left/right accuracy contour tracks offset by horizontal accuracy.",
    )
    parser.add_argument(
        "--points-geojson",
        type=Path,
        default=None,
        help="Write GeoJSON with trackpoints and extras (file or directory; file merges batch outputs).",
    )
    parser.add_argument(
        "--append-points-geojson",
        action="store_true",
        help="Append to an existing GeoJSON file instead of overwriting.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase status detail on stdout (repeat for more detail).",
    )
    parser.set_defaults(aq_extensions=False)

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
            include_extensions=args.aq_extensions,
            pretty=args.pretty,
            verbose=args.verbose,
            accuracy_contours=args.accuracy_contours,
            geojson=args.points_geojson,
            geojson_append=args.append_points_geojson,
        )
        return

    if args.profile_out and args.batch_dir:
        raise SystemExit("--profile-out is only supported for single-file conversions.")

    # Single-file workflow (backwards compatible).
    if args.summary_only:
        version, header = read_header(Path(args.input))
        if args.verbose > 0 and version and version <= 3:
            from .ops import quick_stats_v3, format_summary_line

            stats = quick_stats_v3(Path(args.input))
            print(format_summary_line(Path(args.input), stats, args.verbose))
            return
        print(f"{args.input}\tversion={version}\theader={header}")
        return

    if args.output is None:
        args.output = _default_output(args.input)

    run_kwargs = dict(
        include_extensions=args.aq_extensions,
        progress=args.progress,
        pretty=args.pretty,
        accuracy_contours=args.accuracy_contours,
        geojson_output=str(args.points_geojson) if args.points_geojson else None,
        geojson_append=args.append_points_geojson,
    )

    if args.profile_out:
        args.profile_out.parent.mkdir(parents=True, exist_ok=True)
        cProfile.runctx(
            "alp2gpx(args.input, args.output, verbose=args.verbose, **run_kwargs)",
            globals(),
            locals(),
            filename=str(args.profile_out),
        )
        print(f"Profile written to {args.profile_out}", file=sys.stderr)
    else:
        alp2gpx(args.input, args.output, verbose=args.verbose, **run_kwargs)
