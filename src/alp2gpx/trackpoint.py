from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

AQ_NS = "https://alpinequest.net/xmlschemas/gpx/trackpoint/1"


@dataclass
class TrackPoint:
    lat: float
    lon: float
    elevation: Optional[float]
    timestamp: Optional[float]
    accuracy: Optional[int] = None
    vertical_accuracy: Optional[float] = None
    pressure: Optional[float] = None
    battery: Optional[int] = None
    sat_gps: Optional[int] = None
    sat_glo: Optional[int] = None
    sat_bds: Optional[int] = None
    sat_gal: Optional[int] = None
    network_type: Optional[str] = None
    network_signal_percent: Optional[int] = None
    network_signal_dbm: Optional[int] = None
    network_code: Optional[int] = None
    network_signal_raw: Optional[int] = None
    inclination: Optional[float] = None
    magnetic_field: Optional[float] = None
    elevation_wgs84: Optional[float] = None
    elevation_dem: Optional[float] = None

    def has_extensions(self) -> bool:
        return any(
            value is not None
            for value in [
                self.accuracy,
                self.vertical_accuracy,
                self.pressure,
                self.battery,
                self.sat_gps,
                self.sat_glo,
                self.sat_bds,
                self.sat_gal,
                self.network_type,
                self.network_signal_percent,
                self.network_signal_dbm,
                self.inclination,
                self.magnetic_field,
                self.elevation_wgs84,
                self.elevation_dem,
            ]
        )


def parse_satellites(raw: bytes) -> Tuple[int | None, int | None, int | None, int | None]:
    """Return GPS, GLONASS, BEIDOU, GALILEO counts from eight-byte constellation array."""
    values = list(raw) + [None] * (8 - len(raw))
    gps = values[1] if len(values) > 1 else None
    glo = values[3] if len(values) > 3 else None
    bds = values[5] if len(values) > 5 else None
    gal = values[6] if len(values) > 6 else None
    return gps, glo, bds, gal


def decode_network(code: Optional[int], signal: Optional[int]) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """Decode network info byte pair to a human-friendly type and strength hints."""
    network_type = None
    if code is not None:
        generation = code // 10
        protocol = code % 10
        generation_labels = {0: "NONE", 1: "2G", 2: "3G", 3: "4G", 4: "5G"}
        protocol_labels = {0: "", 1: "GSM", 2: "CDMA", 3: "UMTS", 4: "LTE", 5: "NR"}
        gen = generation_labels.get(generation, f"{generation}G")
        proto = protocol_labels.get(protocol, "")
        if gen == "NONE":
            network_type = "NONE"
        elif proto:
            network_type = f"{gen}/{proto}"
        else:
            network_type = gen

    percent = None
    if signal is not None:
        percent = max(0, min(100, round((signal - 1) / 126 * 100)))

    dbm = None
    if signal is not None:
        # Heuristic often used for ASU→dBm. Keeps the data visible without AlpineQuest docs.
        dbm = -113 + 2 * signal

    return network_type, percent, dbm
