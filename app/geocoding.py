"""
Forward geocoding via Mapbox's v6 API — turns a typed address into
(lat, lng). Used once, at ServiceRequest creation time (see
requests.py:new); never called on every page load.

MAPBOX_ACCESS_TOKEN is a public token by design (starts with pk.), safe
to read from the environment and also used directly in client-side JS
for map rendering — see app/routes/main.py's mapbox_token context or
wherever the map templates pull it from.
"""
import os

import requests

GEOCODE_URL = "https://api.mapbox.com/search/geocode/v6/forward"


def mapbox_configured():
    return bool(os.environ.get("MAPBOX_ACCESS_TOKEN"))


def geocode(address_text):
    """
    Returns (lat, lng) or None. Never raises — a bad address, an API
    outage, or a missing token are all just "we don't have coordinates
    for this one," not a reason to fail the whole request. Scoped to
    Nigeria (country=NG) since that's the only market this app serves.
    """
    token = os.environ.get("MAPBOX_ACCESS_TOKEN")
    if not token or not address_text:
        return None

    try:
        resp = requests.get(
            GEOCODE_URL,
            params={"q": address_text, "access_token": token, "country": "NG", "limit": 1},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None

    features = data.get("features") or []
    if not features:
        return None

    # GeoJSON coordinate order is always [lng, lat] -- the opposite of
    # how humans normally say "lat, lng". Mixing this up silently
    # produces a coordinate on the wrong side of the world, not an
    # error, so it's worth this comment existing at all.
    coords = features[0].get("geometry", {}).get("coordinates")
    if not coords or len(coords) != 2:
        return None

    lng, lat = coords
    return (lat, lng)


def haversine_km(lat1, lng1, lat2, lng2):
    """Great-circle distance in km between two lat/lng points. Good
    enough for "how far is this job from me" sorting at city scale —
    no need for anything more precise than that here."""
    from math import asin, cos, radians, sin, sqrt

    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))  # 6371 = Earth's radius in km
