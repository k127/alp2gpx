"""Support functions for inspecting and batch-converting TRK fixtures."""

from __future__ import annotations

from pathlib import Path
from struct import unpack
from typing import Iterable, Tuple

from .alp2gpx import alp2gpx


def find_tracks(base_dir: Path) -> list[Path]:
    return sorted(base_dir.rglob("*.trk"))


def read_header(path: Path) -> Tuple[int | None, int | None]:
    with path.open("rb") as f:
        raw = f.read(8)
        if len(raw) < 8:
            return None, None
        version, header = unpack(">ll", raw)
        if version and version > 3:
            version = 4
        return version, header


def batch_convert(
    tracks: Iterable[Path],
    out_dir: Path,
    summary_only: bool = False,
    limit: int | None = None,
    include_extensions: bool = False,
    pretty: bool = False,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for idx, path in enumerate(tracks, start=1):
        version, header = read_header(path)
        print(f"[{idx:02}] {path}\tversion={version}\theader={header}")
        if summary_only:
            if limit and idx >= limit:
                break
            continue

        out_path = out_dir / f"{path.stem}.gpx"
        result = alp2gpx(str(path), str(out_path), include_extensions=include_extensions, pretty=pretty)
        segments = len(result.segments or [])
        points = sum(len(seg.points) for seg in result.segments or [])
        print(f"     -> {out_path} (segments={segments}, points={points}, version={result.fileVersion})")
        if limit and idx >= limit:
            break
