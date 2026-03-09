from google import genai
from google.genai import types
import json, csv, time

from utils import GEMINI_API, load_json, save_json
from utils import split_artists, join_artists
from utils import SPOTIFY_CACHE_FILE, FIXED_ID_FILE
from utils import to_sort_string
from musicbrain import localize_artist, get_artist_locale

_spotify_cache  = load_json(SPOTIFY_CACHE_FILE)
_fixed_ids:set  = set(load_json(FIXED_ID_FILE) or [])

client = genai.Client(api_key=GEMINI_API)

def llm_correct_metadata(song: str, artist: str, album: str) -> dict:
    prompt = f"""
I have a song with possibly incorrect or transliterated metadata:
Song: {song}
Artist: {artist}
Album: {album}

1. Identify the original release country of this song.
2. Return the correct metadata in the original language (e.g. Chinese characters for Chinese songs).
3. Return ONLY a JSON object with these fields:
   - song_name
   - artist_name        (ALL artists separated by ", " and "&" for the last one, e.g. "A, B & C". Do NOT use "feat.", "ft.", "with" or any other prefix. Just list all artist names.)
   - album_artist       (main album artist, usually just the primary artist)
   - album_name
   - country (e.g. "China", "Japan", "Hong Kong", "Taiwan", "USA" )
   - language (e.g. "Traditional Chinese", "Japanese", "Simplified Chinese", "English")

No explanation, just JSON.
"""
    
    resp = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt,
    )
    text = resp.text.strip()
    start = text.find("{")
    end   = text.rfind("}") + 1
    return json.loads(text[start:end])

def patch_sort_fields(row: dict):

    locale = get_artist_locale(row["artist"])
    if not locale:
        return row
    
    row["sort_name"]         = to_sort_string(row["name"], locale)
    row["sort_artist"]       = to_sort_string(row["artist"], locale)
    row["sort_album_artist"] = to_sort_string(row["album_artist"], locale)
    row["sort_album"]        = to_sort_string(row["album"], locale)
    return row

def gemini_main():
    with open("data/music_library.csv", encoding="utf-8") as f:
        tracks = list(csv.DictReader(f))

    print(f"📚 In total {len(tracks)} songs, starting...\n")

    for i, t in enumerate(tracks):
        song   = t["name"].strip()
        artist = t["artist"].strip()
        album  = t["album"].strip()
        db_id = t["db_id"].strip()

        if db_id in _fixed_ids:
            continue

        cache_key = f"{song}|||{artist}|||{album}"
        if cache_key in _spotify_cache:
            continue

        print(f"[{i+1}/{len(tracks)}] {song} — {artist}")
        corrected = None
        raw_track_artist = artist
        raw_album_artist = artist
        try:
            corrected = llm_correct_metadata(song, artist, album)
            raw_track_artist = corrected.get("artist_name", artist)
            raw_album_artist = corrected.get("album_artist", artist)

        except Exception as e:
            print(f"  ⚠️  Gemini Fail: {e}")

        row = dict(t)
        track_artists = [localize_artist(a) for a in split_artists(raw_track_artist)]
        album_artists = [localize_artist(a) for a in split_artists(raw_album_artist)]

        if corrected:
            row["name"]         = corrected.get("song_name", song)
            row["artist"]       = join_artists(track_artists)
            row["album"]        = corrected.get("album_name", album)
            row["album_artist"] = join_artists(album_artists)
            row["country"]      = corrected.get("country", "")
            row["language"]     = corrected.get("language", "")
            row["sort_name"]         = row["name"]
            row["sort_artist"]       = join_artists(track_artists)
            row["sort_album_artist"] = join_artists(album_artists)
            row["sort_album"]        = row["album"]

            row = patch_sort_fields(row)
            _spotify_cache[cache_key] = row
            save_json(SPOTIFY_CACHE_FILE, _spotify_cache)
        else:
            print(f"  {song} ❌ Gemini correction failed")
            _spotify_cache[cache_key] = None
            save_json(SPOTIFY_CACHE_FILE, _spotify_cache)

        time.sleep(4)  # 15 RPM 

    print(f"\n✅ Done!")


if __name__ == "__main__":
    resp = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents='Reply with this exact JSON only: {"status": "ok", "model": "gemini-2.0-flash"}'
    )
    print(resp.text)
    resp = json.loads(resp.text)

    if resp['status'] == 'ok':
        gemini_main()
