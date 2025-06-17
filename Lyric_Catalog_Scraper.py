import sqlite3
import time
from unidecode import unidecode
import re
import lyricsgenius

# Set your Genius API access token
ACCESS_TOKEN = "1-viKB1s7zv38w5S1t9CxOmW0g2BZBxRA8XS7uc2IQWUAWAlxfFqxQGHoe3lGkBr"
genius = lyricsgenius.Genius(ACCESS_TOKEN, skip_non_songs=True, excluded_terms=["(Remix)", "(Live)"])

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
        lyrics TEXT
    )
''')
# Delete existing entries
cursor.execute("DELETE FROM songs")
conn.commit()

# Clean lyrics text
def clean_lyrics(raw_lyrics):
    text = unidecode(raw_lyrics)
    text = re.sub(r"^\d+\s+Contributors", "", text)
    text = re.sub(r"Read More", "", text, flags=re.IGNORECASE)

    # Remove any leading title + Lyrics (e.g., "Song Title Lyrics")
    text = re.sub(r"^.*?Lyrics\n", "", text, flags=re.DOTALL)
    text = re.sub(r"^.*?Lyrics", "", text, flags=re.DOTALL)  # For cases with no \n after Lyrics

    # Remove blurbs ending in ellipsis
    text = re.sub(r"^.*?\.\.\.\s*", "", text, flags=re.DOTALL)

    # Remove brackets like [Chorus], [Verse], etc.
    text = re.sub(r"\[.*?\]", "", text)

    # Clean and deduplicate lines
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
def save_song_to_db(song_id, title, artist, album, release_year, url, lyrics):
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO songs (genius_id, title, artist, album, release_year, url, lyrics)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (song_id, title, artist, album, release_year, url, lyrics))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving to DB: {e}")

# Main
BASE_URL = "https://api.genius.com"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

# Helper function to search for an artist and get their Genius ID
def get_artist_id(artist_name):
    search_url = f"{BASE_URL}/search"
    params = {"q": artist_name}
    response = requests.get(search_url, params=params, headers=HEADERS)
    response.raise_for_status()
    results = response.json()["response"]["hits"]
    for hit in results:
        if hit["result"]["primary_artist"]["name"].lower() == artist_name.lower():
            return hit["result"]["primary_artist"]["id"]
    return None

# Helper function to get all songs by artist ID (paginated)
def get_artist_songs(artist_id, per_page=20, sleep_time=1):
    page = 1
    songs = []
    while True:
        url = f"{BASE_URL}/artists/{artist_id}/songs"
        params = {"page": page, "per_page": per_page}
        response = requests.get(url, params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()["response"]
        page_songs = data["songs"]
        if not page_songs:
            break
        songs.extend(page_songs)
        page += 1
        time.sleep(sleep_time)
    return songs

# Helper function to output songs to a text file
def write_songs_to_file(songs, filename="songs.txt"):
    """Write song titles and URLs to a text file.

    Parameters
    ----------
    songs : list
        List of song dictionaries as returned by ``get_artist_songs``.
    filename : str, optional
        Destination filename, by default ``"songs.txt"``.
    """
    with open(filename, "w", encoding="utf-8") as f:
        for song in songs:
            f.write(f"{song['title']} ({song['url']})\n")

# Example usage
if __name__ == "__main__":
    artist_name = "Kendrick Lamar"
    print(f"Fetching songs for {artist_name}...")
    artist = genius.search_artist(artist_name, max_songs=5, sort="title")

    song_titles = [song.title for song in artist.songs]
    for title in song_titles:
        print(f"Searching for lyrics: {title}")
        try:
            song = genius.search_song(title, artist_name)
            if not song:
                print(f"Could not find lyrics for: {title}")
                continue
            cleaned_lyrics = clean_lyrics(song.lyrics)
            album = get_attr_safe(song, 'album')
            year = get_attr_safe(song, 'year')
            print(f"Lyrics preview: {cleaned_lyrics[:100]}...")
            save_song_to_db(song.id, song.title, artist_name, album, year, song.url, cleaned_lyrics)
            time.sleep(1)
        except Exception as e:
            print(f"Error processing {title}: {e}")

    print("5 songs saved to database.")
    conn.close()
    artist_name = "Kendrick Lamar"  # Change to desired artist
    artist_id = get_artist_id(artist_name)
    if artist_id:
        print(f"Artist ID for {artist_name}: {artist_id}")
        all_songs = get_artist_songs(artist_id)
        print(f"Total songs retrieved: {len(all_songs)}")
        for song in all_songs:
            print(f"{song['title']} ({song['url']})")
        write_songs_to_file(all_songs)
        print("Song list written to songs.txt")
    else:
        print("Artist not found.")
