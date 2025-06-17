import sqlite3

def list_songs():
    conn = sqlite3.connect("lyrics_catalog.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, artist FROM songs ORDER BY title")
    songs = cursor.fetchall()
    conn.close()
    return songs

def get_lyrics_by_id(song_id):
    conn = sqlite3.connect("lyrics_catalog.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, lyrics FROM songs WHERE id = ?", (song_id,))
    result = cursor.fetchone()
    conn.close()
    return result

if __name__ == "__main__":
    songs = list_songs()
    if not songs:
        print("No songs found in the database.")
    else:
        print("Available Songs:\n")
        for song in songs:
            print(f"{song[0]}. {song[1]} - {song[2]}")

        try:
            selection = int(input("\nEnter the ID of the song to view lyrics: "))
            song = get_lyrics_by_id(selection)
            if song:
                print(f"\n--- {song[0]} ---\n")
                print(song[1])
            else:
                print("Song not found.")
        except ValueError:
            print("Invalid input.")
