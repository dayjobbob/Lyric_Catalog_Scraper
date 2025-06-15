import requests
import time

# Set your Genius API access token
ACCESS_TOKEN = "1-viKB1s7zv38w5S1t9CxOmW0g2BZBxRA8XS7uc2IQWUAWAlxfFqxQGHoe3lGkBr"
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
