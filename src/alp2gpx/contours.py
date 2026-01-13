"""Utilities to build left/right contour tracks based on horizontal accuracy."""

from __future__ import annotations

import math
from typing import Iterable, List, Tuple

from .trackpoint import TrackPoint

EARTH_RADIUS_M = 6371000.0


def _initial_bearing(p1: TrackPoint, p2: TrackPoint) -> float:
    """Return initial bearing from p1 to p2 in radians."""
    lat1 = math.radians(p1.lat)
    lat2 = math.radians(p2.lat)
    dlon = math.radians(p2.lon - p1.lon)
    if lat1 == lat2 and dlon == 0:
        return 0.0
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return math.atan2(y, x)


def _offset_point(lat: float, lon: float, distance_m: float, bearing_rad: float) -> Tuple[float, float]:
    """Move lat/lon by distance (m) along bearing (rad); returns new lat/lon degrees."""
    d_div_r = distance_m / EARTH_RADIUS_M
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)

    lat2 = math.asin(math.sin(lat1) * math.cos(d_div_r) + math.cos(lat1) * math.sin(d_div_r) * math.cos(bearing_rad))
    lon2 = lon1 + math.atan2(
        math.sin(bearing_rad) * math.sin(d_div_r) * math.cos(lat1),
        math.cos(d_div_r) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lat2), math.degrees(lon2)


def _heading_for_index(points: List[TrackPoint], idx: int) -> float:
    """Estimate heading (radians) at index using neighbor points."""
    if len(points) == 1:
        return 0.0
    if idx == 0:
        return _initial_bearing(points[idx], points[idx + 1])
    if idx == len(points) - 1:
        return _initial_bearing(points[idx - 1], points[idx])
    # Average of inbound/outbound bearings
    b1 = _initial_bearing(points[idx - 1], points[idx])
    b2 = _initial_bearing(points[idx], points[idx + 1])
    # Normalize average on circle
    x = math.cos(b1) + math.cos(b2)
    y = math.sin(b1) + math.sin(b2)
    if x == 0 and y == 0:
        return b1
    return math.atan2(y, x)


def build_accuracy_contours(segment: Iterable[TrackPoint]) -> Tuple[List[TrackPoint], List[TrackPoint]]:
    """Return (left_segment, right_segment) offset by accuracy radius where available."""
    pts = list(segment)
    if not pts:
        return [], []

    left: List[TrackPoint] = []
    right: List[TrackPoint] = []

    for idx, p in enumerate(pts):
        if p.accuracy is None or p.accuracy <= 0:
            # No accuracy -> reuse original point to keep index alignment
            left.append(p)
            right.append(p)
            continue
        heading = _heading_for_index(pts, idx)
        # Perpendicular bearings
        left_bearing = heading + math.pi / 2
        right_bearing = heading - math.pi / 2

        lat_l, lon_l = _offset_point(p.lat, p.lon, p.accuracy, left_bearing)
        lat_r, lon_r = _offset_point(p.lat, p.lon, p.accuracy, right_bearing)

        left.append(
            TrackPoint(
                lat=lat_l,
                lon=lon_l,
                elevation=p.elevation,
                timestamp=p.timestamp,
                accuracy=p.accuracy,
                vertical_accuracy=p.vertical_accuracy,
                pressure=p.pressure,
                battery=p.battery,
                sat_gps=p.sat_gps,
                sat_glo=p.sat_glo,
                sat_bds=p.sat_bds,
                sat_gal=p.sat_gal,
                network_type=p.network_type,
                network_signal_percent=p.network_signal_percent,
                network_signal_dbm=p.network_signal_dbm,
                network_code=p.network_code,
                network_signal_raw=p.network_signal_raw,
                inclination=p.inclination,
                magnetic_field=p.magnetic_field,
                elevation_wgs84=p.elevation_wgs84,
                elevation_dem=p.elevation_dem,
            )
        )
        right.append(
            TrackPoint(
                lat=lat_r,
                lon=lon_r,
                elevation=p.elevation,
                timestamp=p.timestamp,
                accuracy=p.accuracy,
                vertical_accuracy=p.vertical_accuracy,
                pressure=p.pressure,
                battery=p.battery,
                sat_gps=p.sat_gps,
                sat_glo=p.sat_glo,
                sat_bds=p.sat_bds,
                sat_gal=p.sat_gal,
                network_type=p.network_type,
                network_signal_percent=p.network_signal_percent,
                network_signal_dbm=p.network_signal_dbm,
                network_code=p.network_code,
                network_signal_raw=p.network_signal_raw,
                inclination=p.inclination,
                magnetic_field=p.magnetic_field,
                elevation_wgs84=p.elevation_wgs84,
                elevation_dem=p.elevation_dem,
            )
        )

    return left, right
