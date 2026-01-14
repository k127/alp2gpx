from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Callable, Iterable, Optional

from .trackpoint import Segment, TrackPoint


def _clean_meta(meta: dict) -> dict:
    cleaned = {}
    for key, value in (meta or {}).items():
        if isinstance(value, bytes):
            cleaned[key] = base64.b64encode(value).decode("ascii")
        else:
            cleaned[key] = value
    return cleaned


def _build_point_properties(
    track_name: str,
    segment_index: int,
    point_index: int,
    segment_meta: dict,
    trkpoint: TrackPoint,
    track_file: str,
    track_stem: str,
    format_time: Callable[[Optional[float]], Optional[str]],
    track_index: Optional[int] = None,
) -> dict:
    props = {
        "trackName": track_name,
        "segmentIndex": segment_index,
        "pointIndex": point_index,
        "trackFile": track_file,
        "trackStem": track_stem,
    }
    if track_index is not None:
        props["trackIndex"] = track_index

    def add_if_present(key: str, value):
        if value is not None:
            props[key] = value

    time_str = format_time(trkpoint.timestamp)
    add_if_present("timeUnix", trkpoint.timestamp)
    if time_str:
        props["time"] = time_str

    field_map = {
        "elevation": trkpoint.elevation,
        "accuracy": trkpoint.accuracy,
        "accuracyVertical": trkpoint.vertical_accuracy,
        "pressure": trkpoint.pressure,
        "battery": trkpoint.battery,
        "satGps": trkpoint.sat_gps,
        "satGlo": trkpoint.sat_glo,
        "satBds": trkpoint.sat_bds,
        "satGal": trkpoint.sat_gal,
        "networkType": trkpoint.network_type,
        "networkSignalPercent": trkpoint.network_signal_percent,
        "networkSignalDbm": trkpoint.network_signal_dbm,
        "networkCode": trkpoint.network_code,
        "networkSignalRaw": trkpoint.network_signal_raw,
        "inclination": trkpoint.inclination,
        "magneticField": trkpoint.magnetic_field,
        "elevationWgs84": trkpoint.elevation_wgs84,
        "elevationDem": trkpoint.elevation_dem,
    }
    for key, value in field_map.items():
        add_if_present(key, value)

    return props


def build_geojson_collection(
    track_name: str,
    track_file: str,
    segments: Iterable[Segment],
    format_time: Callable[[Optional[float]], Optional[str]],
    file_version: int,
    track_index: Optional[int] = None,
) -> dict:
    track_stem = os.path.splitext(os.path.basename(track_file))[0]
    idx = track_index
    features = []
    segment_lookup = []
    for s_idx, seg in enumerate(segments or []):
        coords_line = []
        for p_idx, p in enumerate(seg.points):
            coords = [p.lon, p.lat]
            if p.elevation is not None:
                coords.append(p.elevation)
            coords_line.append(coords)
            props = _build_point_properties(
                track_name=track_name,
                segment_index=s_idx,
                point_index=p_idx,
                segment_meta=seg.meta,
                trkpoint=p,
                track_file=track_file,
                track_stem=track_stem,
                format_time=format_time,
                track_index=idx,
            )
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": coords},
                    "properties": props,
                }
            )
        if coords_line:
            line_props = {
                "trackName": track_name,
                "trackFile": track_file,
                "trackStem": track_stem,
                "segmentIndex": s_idx,
            }
            if idx is not None:
                line_props["trackIndex"] = idx
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords_line},
                    "properties": line_props,
                }
            )
            if seg.meta:
                segment_lookup.append(
                    {"segmentIndex": s_idx, "segmentMeta": _clean_meta(seg.meta)}
                )

    collection = {
        "type": "FeatureCollection",
        "name": track_name,
        "source": {
            "file": track_file,
            "version": file_version,
        },
        "features": features,
    }
    if segment_lookup:
        collection["segments"] = segment_lookup
    return collection


def append_geojson(path: Path, collection: dict, pretty: bool = False) -> None:
    """Append features (and segments) to an existing GeoJSON FeatureCollection, creating if missing."""
    target: dict
    if path.exists():
        try:
            target = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            target = {}
    else:
        target = {}

    if not target:
        target.update({"type": "FeatureCollection", "features": []})

    target.setdefault("type", "FeatureCollection")
    target.setdefault("features", [])
    target["features"].extend(collection.get("features", []))

    if "segments" in collection:
        target.setdefault("segments", [])
        target["segments"].extend(collection["segments"])

    if "name" not in target and "name" in collection:
        target["name"] = collection["name"]
    if "source" not in target and "source" in collection:
        target["source"] = collection["source"]

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        if pretty:
            json.dump(target, fh, ensure_ascii=False, indent=2)
        else:
            json.dump(target, fh, ensure_ascii=False, separators=(",", ":"))
