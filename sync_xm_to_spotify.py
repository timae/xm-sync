import os
import requests
import time
from datetime import datetime, timedelta
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

# Configuration from environment variables
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')
SCOPE = 'playlist-modify-public playlist-modify-private'
PLAYLIST_ID = os.getenv('SPOTIFY_PLAYLIST_ID')  # optional: if not set, a new playlist will be created
XM_STATION_SLUG = 'lifewithjohnmayer'
XM_API_BASE = 'https://xmplaylist.com/api'


def get_xm_tracks(since_ms: int):
    """
    Fetch tracks played on the station since the given timestamp (ms).
    """
    url = f"{XM_API_BASE}/station/{XM_STATION_SLUG}/history"
    params = {'since': since_ms, 'limit': 500}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json().get('tracks', [])


def auth_spotify():
    """
    Authenticate via OAuth and return Spotipy client.
    """
    return Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE
    ))


def ensure_playlist(sp: Spotify):
    """
    Create a new playlist in your account if PLAYLIST_ID isn't set.
    Returns the playlist ID to use.
    """
    global PLAYLIST_ID
    if PLAYLIST_ID:
        return PLAYLIST_ID
    user = sp.current_user()
    user_id = user['id']
    playlist = sp.user_playlist_create(
        user_id,
        name='Life with John Mayer - Last 12h',
        public=False,
        description='Auto-updated playlist of last 12h from Life with John Mayer'
    )
    PLAYLIST_ID = playlist['id']
    print(f"Created new playlist: {playlist['name']} (ID: {PLAYLIST_ID})")
    return PLAYLIST_ID


def find_spotify_uris(sp: Spotify, tracks):
    """
    Search Spotify for each track and return unique URIs.
    """
    uris, seen = [], set()
    for t in tracks:
        query = f"artist:{t['artist']} track:{t['title']}"
        results = sp.search(q=query, type='track', limit=1)
        items = results.get('tracks', {}).get('items', [])
        if items:
            uri = items[0]['uri']
            if uri not in seen:
                seen.add(uri)
                uris.append(uri)
    return uris


def update_playlist(sp: Spotify, playlist_id: str, uris):
    """
    Replace playlist contents with new URIs (up to 100 per request).
    """
    for i in range(0, len(uris), 100):
        slice_ = uris[i:i+100]
        if i == 0:
            sp.playlist_replace_items(playlist_id, slice_)
        else:
            sp.playlist_add_items(playlist_id, slice_)


def main():
    # Calculate timestamp for 12 hours ago (ms)
    since = int((datetime.utcnow() - timedelta(hours=12)).timestamp() * 1000)
    print(f"Fetching tracks since {datetime.utcnow() - timedelta(hours=12)} UTC...")
    tracks = get_xm_tracks(since)
    if not tracks:
        print("No new tracks found in the last 12h.")
        return

    sp = auth_spotify()
    playlist_id = ensure_playlist(sp)
    uris = find_spotify_uris(sp, tracks)
    if not uris:
        print("No matching tracks found on Spotify.")
        return

    update_playlist(sp, playlist_id, uris)
    print(f"Playlist (ID: {playlist_id}) updated with {len(uris)} tracks.")

if __name__ == '__main__':
    main()
