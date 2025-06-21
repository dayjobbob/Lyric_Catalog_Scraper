import sqlite3
import time
from unidecode import unidecode
import re
import lyricsgenius
import csv

# Set your Genius API access token
ACCESS_TOKEN = "1-viKB1s7zv38w5S1t9CxOmW0g2BZBxRA8XS7uc2IQWUAWAlxfFqxQGHoe3lGkBr"
genius = lyricsgenius.Genius(ACCESS_TOKEN, skip_non_songs=True, excluded_terms=["(Remix)", "(Live)"], remove_section_headers=True)

# Database setup
conn = sqlite3.connect("lyrics_catalog.db")
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY,
        genius_id INTEGER UNIQUE,
        title TEXT,
        artist TEXT,
        album TEXT,
        release_year TEXT,
        url TEXT,
        lyrics TEXT,
        popularity INTEGER
    )
''')
# Delete existing entries
cursor.execute("DELETE FROM songs")
conn.commit()

# Clean lyrics text
def clean_lyrics(raw_lyrics):
    if not raw_lyrics:
        return ""
    
    # Convert special characters to ASCII
    text = unidecode(raw_lyrics)

    # Remove contributor attribution at the top
    text = re.sub(r"^\d+\s+Contributors", "", text)

    # Remove "Read More" text
    text = re.sub(r"Read More", "", text, flags=re.IGNORECASE)

    # Remove title + "Lyrics" patterns that often precede the actual lyrics
    text = re.sub(r"^.*?Lyrics\n", "", text, flags=re.DOTALL)
    text = re.sub(r"^.*?Lyrics", "", text, flags=re.DOTALL)

    # Remove trailing blurbs that end in ellipses
    text = re.sub(r"^.*?\.\.\.\s*", "", text, flags=re.DOTALL)

    # Remove section labels like [Chorus], [Verse 1], etc.
    text = re.sub(r"\[.*?\]", "", text)

    # Split into lines and clean duplicates / unwanted content
    lines = text.split('\n')
    cleaned_lines = []
    seen_lines = set()
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.lower().startswith(('see', 'about', 'lyrics powered')):
            if stripped not in seen_lines:
                cleaned_lines.append(stripped)
                seen_lines.add(stripped)

    return '\n'.join(cleaned_lines)

# Safe extraction helper
def get_attr_safe(obj, attr):
    try:
        value = getattr(obj, attr)
        return str(value) if value else ""
    except:
        return ""

# Save song to database
def save_song_to_db(song_id, title, artist, album, release_year, url, lyrics, popularity):
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO songs (genius_id, title, artist, album, release_year, url, lyrics, popularity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (song_id, title, artist, album, release_year, url, lyrics, popularity))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving to DB: {e}")

# CSV export setup
EXPORT_CSV_PATH = "lyrics_export.csv"
SKIPPED_SONGS_LOG = "skipped_songs.txt"

exported_rows = []
skipped_titles = []

# Main
if __name__ == "__main__":
    artist_name = "Erykah Badu"
    print(f"Fetching songs for {artist_name}...")
    artist = genius.search_artist(artist_name, sort="title")

    for song in artist.songs:
        print(f"Processing: {song.title}")
        try:
            # Ensure song has lyrics before attempting to clean or save
            if not song.lyrics:
                print(f"No lyrics found for: {song.title}")
                skipped_titles.append(song.title)
                continue

            cleaned_lyrics = clean_lyrics(song.lyrics)
            album = song.album.name if song.album else ""
            year = get_attr_safe(song, 'year')
            popularity = song._body.get("stats", {}).get("pageviews", 0)
            print(f"Lyrics preview: {cleaned_lyrics[:100]}...")
            save_song_to_db(song.id, song.title, artist_name, album, year, song.url, cleaned_lyrics, popularity)
            exported_rows.append([song.id, song.title, artist_name, album, year, song.url, cleaned_lyrics, popularity])
            time.sleep(1)
        except Exception as e:
            print(f"Error processing {song.title}: {e}")
            skipped_titles.append(song.title)

    print("All songs saved to database.")

    # Write CSV export
    with open(EXPORT_CSV_PATH, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["genius_id", "title", "artist", "album", "release_year", "url", "lyrics", "popularity"])
        writer.writerows(exported_rows)

    # Write skipped song titles
    with open(SKIPPED_SONGS_LOG, "w", encoding="utf-8") as skipfile:
        for title in skipped_titles:
            skipfile.write(title + "\n")

    conn.close()
    print(f"Exported to {EXPORT_CSV_PATH} with {len(exported_rows)} songs. Skipped {len(skipped_titles)} songs.")
