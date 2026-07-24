"""Fonctions utilitaires : géométrie et calcul des dates de collecte."""

from __future__ import annotations

import calendar
from datetime import date, timedelta

WEEKDAYS = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
}

MONTHS = {
    "janvier": 1,
    "février": 2,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
    "decembre": 12,
}

NO_COLLECTION = ("pas de collecte", "", "aucune")


# --------------------------------------------------------------------------- #
# Géométrie : point dans polygone (algorithme du lancer de rayon)
# --------------------------------------------------------------------------- #
def get_geometry(geo_shape: dict | None) -> dict:
    """Extrait la géométrie GeoJSON, que geo_shape soit une Feature ou une géométrie."""
    if not geo_shape:
        return {}
    if "geometry" in geo_shape:
        return geo_shape.get("geometry") or {}
    if geo_shape.get("type") in ("Polygon", "MultiPolygon"):
        return geo_shape
    return {}


def _point_in_ring(lon: float, lat: float, ring: list) -> bool:
    inside = False
    n = len(ring)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i
    return inside


def _polygon_contains(lon: float, lat: float, rings: list) -> bool:
    if not rings:
        return False
    if not _point_in_ring(lon, lat, rings[0]):
        return False
    # Un point situé dans un trou (anneau intérieur) est hors du polygone
    for hole in rings[1:]:
        if _point_in_ring(lon, lat, hole):
            return False
    return True


def point_in_geometry(lon: float, lat: float, geometry: dict) -> bool:
    """Teste si (lon, lat) est à l'intérieur d'une géométrie Polygon/MultiPolygon."""
    if not geometry:
        return False
    gtype = geometry.get("type")
    coords = geometry.get("coordinates")
    if not coords:
        return False
    if gtype == "Polygon":
        return _polygon_contains(lon, lat, coords)
    if gtype == "MultiPolygon":
        return any(_polygon_contains(lon, lat, poly) for poly in coords)
    return False


# --------------------------------------------------------------------------- #
# Analyse de la période annuelle (« De début Mars à mi-Décembre »)
# --------------------------------------------------------------------------- #
def parse_perioann(perioann: str | None):
    """Retourne (mois_début, mod_début, mois_fin, mod_fin) ou None (toute l'année)."""
    if not perioann:
        return None
    text = perioann.lower()
    if any(x in text for x in ("pas de collecte", "toute l")):
        return None

    parts = text.split(" à ")
    if len(parts) == 2:
        start_txt, end_txt = parts
    else:
        start_txt, end_txt = text, text

    def _bound(chunk: str):
        month = None
        for name, num in MONTHS.items():
            if name in chunk:
                month = num
                break
        if month is None:
            return None
        if "début" in chunk or "debut" in chunk:
            mod = "start"
        elif "mi" in chunk:
            mod = "mid"
        elif "fin" in chunk:
            mod = "end"
        else:
            mod = None
        return (month, mod)

    start = _bound(start_txt)
    end = _bound(end_txt)
    if start is None or end is None:
        return None
    return (start[0], start[1] or "start", end[0], end[1] or "end")


def _resolve_day(month: int, mod: str, year: int) -> int:
    if mod == "start":
        return 1
    if mod == "mid":
        return 15
    return calendar.monthrange(year, month)[1]  # "end"


def _in_season(day: date, bounds) -> bool:
    if bounds is None:
        return True
    sm, smod, em, emod = bounds
    start = date(day.year, sm, _resolve_day(sm, smod, day.year))
    end = date(day.year, em, _resolve_day(em, emod, day.year))
    if start <= end:
        return start <= day <= end
    # Saison à cheval sur le nouvel an
    return day >= start or day <= end


# --------------------------------------------------------------------------- #
# Calcul des prochaines dates de collecte
# --------------------------------------------------------------------------- #
def is_collection(jours: str | None) -> bool:
    if not jours:
        return False
    return jours.strip().lower() not in NO_COLLECTION


def next_dates(
    jours: str | None,
    perioann: str | None,
    count: int,
    from_date: date | None = None,
) -> list[date]:
    """Prochaines dates de collecte à partir de from_date (inclus)."""
    if not is_collection(jours):
        return []
    weekday = WEEKDAYS.get(jours.strip().lower())
    if weekday is None:
        return []
    if from_date is None:
        from_date = date.today()
    bounds = parse_perioann(perioann)

    day = from_date + timedelta(days=(weekday - from_date.weekday()) % 7)
    results: list[date] = []
    guard = 0
    while len(results) < count and guard < 300:
        if _in_season(day, bounds):
            results.append(day)
        day += timedelta(days=7)
        guard += 1
    return results


def dates_in_range(
    jours: str | None,
    perioann: str | None,
    start_date: date,
    end_date: date,
) -> list[date]:
    """Toutes les dates de collecte comprises dans [start_date, end_date]."""
    if not is_collection(jours):
        return []
    weekday = WEEKDAYS.get(jours.strip().lower())
    if weekday is None:
        return []
    bounds = parse_perioann(perioann)
    day = start_date + timedelta(days=(weekday - start_date.weekday()) % 7)
    out: list[date] = []
    while day <= end_date:
        if _in_season(day, bounds):
            out.append(day)
        day += timedelta(days=7)
    return out
