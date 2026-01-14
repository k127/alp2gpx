"""Support functions for inspecting and batch-converting TRK fixtures."""

from __future__ import annotations

import os
from pathlib import Path
from struct import unpack
from typing import Iterable, Tuple
import json

from .alp2gpx import alp2gpx
from .geojson import append_geojson


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


def quick_stats_v3(path: Path) -> dict:
    with path.open("rb") as f:
        f.seek(0)
        version, header = unpack(">ll", f.read(8))
        f.seek(8)
        nloc = unpack(">l", f.read(4))[0]
        nseg = unpack(">l", f.read(4))[0]
        nwpt = unpack(">l", f.read(4))[0]
        lon = unpack(">l", f.read(4))[0] * 1e-7
        lat = unpack(">l", f.read(4))[0] * 1e-7
        ts_ms = unpack(">q", f.read(8))[0]
        f.seek(36)
        total_len = unpack(">d", f.read(8))[0]
        total_len_3d = unpack(">d", f.read(8))[0]
        gain = unpack(">d", f.read(8))[0]
        duration = unpack(">q", f.read(8))[0]
    return {
        "version": version,
        "header": header,
        "loc": nloc,
        "seg": nseg,
        "wpt": nwpt,
        "lon0": lon,
        "lat0": lat,
        "ts0": ts_ms / 1000.0,
        "length": total_len,
        "length3d": total_len_3d,
        "gain": gain,
        "duration": duration,
    }


def format_summary_line(path: Path, stats: dict, verbose: int) -> str:
    parts = [f"{path}", f"version={stats['version']}", f"header={stats['header']}"]
    if verbose >= 1:
        parts.append(f"loc={stats['loc']}")
        parts.append(f"seg={stats['seg']}")
        parts.append(f"wpt={stats['wpt']}")
    if verbose >= 2:
        parts.append(f"len={stats['length']:.1f}m")
        parts.append(f"gain={stats['gain']:.1f}m")
        parts.append(f"dur={stats['duration']}s")
    if verbose >= 3:
        parts.append(f"len3d={stats['length3d']:.1f}m")
        parts.append(f"lon0={stats['lon0']:.6f}")
        parts.append(f"lat0={stats['lat0']:.6f}")
    return " ".join(parts)


def batch_convert(
    tracks: Iterable[Path],
    out_dir: Path,
    summary_only: bool = False,
    limit: int | None = None,
    include_extensions: bool = False,
    pretty: bool = False,
    verbose: int = 0,
    accuracy_contours: bool = False,
    geojson: Path | None = None,
    geojson_append: bool = False,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    geojson_dir: Path | None = None
    geojson_file: Path | None = None
    merged_features = []
    track_count = 0
    if geojson:
        if geojson.exists() and geojson.is_dir():
            geojson_dir = geojson
        elif geojson.suffix:
            geojson_file = geojson
        else:
            geojson_dir = geojson
        if geojson_dir:
            geojson_dir.mkdir(parents=True, exist_ok=True)
        if geojson_file:
            geojson_file.parent.mkdir(parents=True, exist_ok=True)

    for idx, path in enumerate(tracks, start=1):
        version, header = read_header(path)
        if summary_only and verbose > 0 and version and version <= 3:
            stats = quick_stats_v3(path)
            print(format_summary_line(path, stats, verbose))
            if limit and idx >= limit:
                break
            continue
        else:
            print(f"[{idx:02}] {path}\tversion={version}\theader={header}")
            if summary_only:
                if limit and idx >= limit:
                    break
                continue

        out_path = out_dir / f"{path.stem}.gpx"
        geojson_path = None
        if geojson_dir:
            geojson_path = geojson_dir / f"{path.stem}.geojson"
        result = alp2gpx(
            str(path),
            str(out_path),
            include_extensions=include_extensions,
            pretty=pretty,
            verbose=verbose,
            accuracy_contours=accuracy_contours,
            geojson_output=str(geojson_path) if geojson_path else None,
            track_index=idx,
            geojson_append=geojson_append,
        )
        if geojson_file:
            collection = result.build_geojson_collection(track_index=idx)
            merged_features.extend(collection.get("features", []))
        segments = len(result.segments or [])
        points = sum(len(seg.points) for seg in result.segments or [])
        print(f"     -> {out_path} (segments={segments}, points={points}, version={result.fileVersion})")
        track_count += 1
        if limit and idx >= limit:
            break
    if geojson_file and merged_features:
        merged = {
            "type": "FeatureCollection",
            "name": geojson_file.stem,
            "source": {"batch": True, "tracks": track_count},
            "features": merged_features,
        }
        if geojson_append:
            append_geojson(geojson_file, merged, pretty=pretty)
        else:
            with geojson_file.open("w", encoding="utf-8") as fh:
                if pretty:
                    json.dump(merged, fh, ensure_ascii=False, indent=2)
                else:
                    json.dump(merged, fh, ensure_ascii=False, separators=(",", ":"))
