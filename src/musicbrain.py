# ── MusicBrainz ───────────────────────────────────────
import requests, time

from .utils import MB_HEADERS
from .utils import _s2t, _t2s, save_json, load_json
from .utils import ARTIST_CACHE_FILE, MB_CACHE_FILE, AREA_TO_LOCALE

_artist_cache   = load_json(ARTIST_CACHE_FILE)  
_mb_cache       = load_json(MB_CACHE_FILE)  

def mb_get(path, params):
    for attempt in range(3):
        try:
            resp = requests.get(
                f"https://musicbrainz.org/ws/2/{path}",
                params={**params, "fmt": "json"},
                headers=MB_HEADERS, timeout=15,
            )
            resp.raise_for_status()
            time.sleep(1.1)
            return resp.json()
        except Exception as e:
            wait = (attempt + 1) * 3
            print(f"    ⚠️  MB error (attempt {attempt+1}/3), wait {wait}s: {e}")
            time.sleep(wait)
    return None

def find_in_cache_by_alias(artist_name: str) -> dict | None:
    for cached_name, info in _mb_cache.items():
        if info is None:
            continue
        aliases = info.get("aliases", {})
        if artist_name in aliases.values():
            return info
    return None

def get_mb_info(artist_name: str) -> dict:
    """Check MusicBrainz: return area + aliases"""
    if artist_name in _mb_cache:
        return _mb_cache[artist_name]

    found = find_in_cache_by_alias(artist_name)
    if found:
        _mb_cache[artist_name] = found
        save_json(MB_CACHE_FILE, _mb_cache)
        return found
    
    # Step 1: Search artist by Spotify name to get MBID and area
    data = mb_get("artist", {"query": f'{artist_name}', "limit": 1})
    if not data or not data.get("artists"):
        result = {"area": None, "aliases": {}}
        _mb_cache[artist_name] = result
        save_json(MB_CACHE_FILE, _mb_cache)
        return result

    artist  = data["artists"][0]
    area    = artist.get("area", {}).get("name")
    mbid    = artist["id"]

    # Step 2: Search artist detail by MBID to get aliases
    detail  = mb_get(f"artist/{mbid}", {"inc": "aliases"})
    aliases = {}
    if detail:
        primary_name = detail.get("name", "")
        if area in AREA_TO_LOCALE:
            aliases[AREA_TO_LOCALE.get(area)] = primary_name

        for a in detail.get("aliases", []):
            locale = a.get("locale")
            if not locale:
                continue
            # primary alias takes precedence if multiple aliases share the same locale
            if locale not in aliases or a.get("primary") is True:
                aliases[locale] = a["name"]

    if area in ["China", "Taiwan", "Hong Kong", "Singapore", "Malaysia"]:
        # For Chinese artists, also add a fallback alias without locale to handle cases where locale is missing or incorrect in MB
        zh_value = None
        for key, val in aliases.items():
            if "zh" in key.lower():
                zh_value = val
                break
        if zh_value:
            if "zh_Hans" not in aliases:
                aliases["zh_Hans"] = _t2s.convert(zh_value)
            if "zh_Hant" not in aliases:
                aliases["zh_Hant"] = _s2t.convert(zh_value)

    result = {"area": area, "aliases": aliases}
    _mb_cache[artist_name] = result
    save_json(MB_CACHE_FILE, _mb_cache)
    return result

def get_artist_locale(artist_name: str) -> str | None:
    mb = _mb_cache.get(artist_name)
    if not mb:
        mb = find_in_cache_by_alias(artist_name)
    if not mb:
        return None
    area = mb.get("area")
    return AREA_TO_LOCALE.get(area)

def localize_artist(artist_name: str) -> str:
    if artist_name in _artist_cache:
        return _artist_cache[artist_name]

    mb    = get_mb_info(artist_name)
    area  = mb["area"]
    locale = AREA_TO_LOCALE.get(area)

    if not locale:
        result = artist_name
    else:
        result = mb["aliases"].get(locale, artist_name)

    _artist_cache[artist_name] = result
    save_json(ARTIST_CACHE_FILE, _artist_cache)
    return result