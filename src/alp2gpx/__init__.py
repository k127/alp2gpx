import argparse
import os

from .alp2gpx import alp2gpx


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("input", help="input file to convert (.trk, etc.)")
    parser.add_argument("-o", "--output",
                        default=None,  # Handled after parser.parse_args()
                        help="output base name (default input file path and base name)")

    args = parser.parse_args()
    if args.output is None:
        args.output = '%s.gpx' % os.path.splitext(args.input)[0]

    q = alp2gpx(args.input, args.output)
