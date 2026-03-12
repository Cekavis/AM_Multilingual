# 🎵 Apple Music Metadata Fixer

A tool to automatically fix and localize metadata (song name, artist, album) in your Apple Music library using the **Gemini API** and **MusicBrainz**.

Useful if your library contains:
- Transliterated names (e.g. `Zitan Qi` → `祁紫檀`)
- Wrong language metadata (e.g. Chinese songs displayed with English titles)
- Missing or incorrect album artist fields
- Songs from Asian markets with inaccurate region metadata

---

## ✨ Features

- Exports your full Apple Music library via AppleScript
- Corrects metadata to the **original language** using Gemini AI (with optional Google Search grounding for newer releases)
- Identifies the **original release country** of each song
- Generates romanized sort fields (pinyin, romaji, romanization) for CJK and Korean names
- Writes corrected metadata back to Music.app via AppleScript
- Incremental processing — already-fixed tracks are skipped automatically
- Caches all results locally to avoid redundant API calls
- MusicBrainz integration for artist name localization

---

## Preview

![Preview](https://github.com/user-attachments/assets/418d2d5b-2eb5-46b8-995a-fdf01f91bcc2)

---

## 📋 Requirements

- macOS with **Music.app**
- Python 3.12+
- A **Gemini API key** — free tier available at [aistudio.google.com](https://aistudio.google.com)

Install dependencies:

```bash
pip install google-genai tqdm python-dotenv opencc-python-reimplemented pypinyin pykakasi hangul-romanize
```

---

## ⚙️ Configuration

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
```

In `src/utils.py`, set your tier:

```python
PAID_USER = False  # Set to True if using a paid Gemini API key
```

- `False` (free tier): **500 RPD**
- `True` (paid tier): supports Google Search grounding for newer releases

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/soulofshadow/AM_Multilingual.git
cd AM_Multilingual
```

### 2. Set up your API key

```bash
cp .env.example .env
# edit .env and fill in your GEMINI_API_KEY
```

### 3. Run the one-click fix script

```bash
chmod +x fix_gemini.sh
./fix_gemini.sh
```

This runs all three steps in sequence:
1. **Export** your Music library from Music.app
2. **Fix** metadata using Gemini + MusicBrainz
3. **Write** corrected metadata back to Music.app

Or run each step individually:

```bash
python -m src.get_library      # Step 1: Export library
python -m src.gemini_repair    # Step 2: Fix metadata
python -m src.write_library    # Step 3: Write back to Music.app
```

> ⚠️ Always **back up your library** before running `write_library`.

---

## 📁 File Structure

```
.
├── src/
│   ├── __init__.py
│   ├── get_library.py      # Export library from Music.app via AppleScript
│   ├── gemini_repair.py    # Fix metadata using Gemini API
│   ├── write_library.py    # Write corrected metadata back to Music.app
│   ├── musicbrain.py       # MusicBrainz artist name localization
│   └── utils.py            # Shared helpers (cache, rate limiting, romanization)
├── cache/
│   ├── artist_cache.json   # Cached MusicBrainz artist localization results
│   └── mb_cache.json       # Cached MusicBrainz lookups
├── data/
│   └── music_library.csv   # Raw exported library from Music.app
├── fix_gemini.sh           # One-click fix script
├── README.md
└── .env                    # Your API key (do not commit)
```

---

## 🗃️ Cache Format

Processed results are stored in `cache/recording_cache.json`. Each entry uses `"song|||artist|||album"` as the key:

```json
"コイワズライ|||Aimer|||Sun Dance": {
    "db_id":            "1231",        // Database ID from Music.app
    "name":             "コイワズライ",  // Original name from Music.app (preserved)
    "artist":           "Aimer",       // Original artist from Music.app (preserved)
    "album_artist":     "Aimer",       // Original album artist from Music.app (preserved)
    "album":            "Sun Dance",   // Original album from Music.app (preserved)

    "sort_name":        "Koiwazurai",  // Romanized sort field (corrected)
    "sort_artist":      "Aimer",       // Romanized sort field (corrected)
    "sort_album_artist":"Aimer",       // Romanized sort field (corrected)
    "sort_album":       "Sun Dance",   // Romanized sort field (corrected)

    "song_name":        "コイワズライ",  // Corrected name from Gemini (new field)
    "artist_name":      "Aimer",       // Corrected artist from Gemini (new field)
    "album_artist_name":"Aimer",       // Corrected album artist from Gemini (new field)
    "album_name":       "Sun Dance",   // Corrected album from Gemini (new field)
    "country":          "Japan",       // Original release country from Gemini (new field)
    "language":         "Japanese",    // Original language from Gemini (new field)
    "needs_review":     false          // Whether the result needs manual review (new field)
}
```

Tracks flagged with `"needs_review": true` are skipped during write-back and should be checked manually.

---

## 🌏 Supported Languages

The tool correctly handles metadata in:
- Simplified Chinese (简体中文)
- Traditional Chinese (繁體中文)
- Japanese (日本語)
- Korean (한국어)
- English and other Latin-script languages

---

## ⚠️ Notes

- Always **back up your library** before running `write_library.py`
- Tracks are matched by `database ID` from Music.app — re-importing a track will change its ID and require re-processing
- The `cache/`, `data/`, and `.env` files are gitignored by default to protect your personal data and API keys
- MusicBrainz API has a strict rate limit of **1 request/second** — the tool handles this automatically

---

## 📄 License

MIT
