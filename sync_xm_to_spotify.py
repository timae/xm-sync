#!/usr/bin/env python3
import os, requests
from datetime import datetime, timedelta
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

CLIENT_ID     = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
REDIRECT_URI  = os.environ["SPOTIFY_REDIRECT_URI"]
PLAYLIST_ID   = os.getenv("SPOTIFY_PLAYLIST_ID")  # optional
SCOPE         = "playlist-modify-public playlist-modify-private"

STATION_SLUG  = "lifewithjohnmayer"
XM_API_BASE   = "https://xmplaylist.com/api"

def get_xm_tracks(since_ms):
    resp = requests.get(f"{XM_API_BASE}/station/{STATION_SLUG}/history",
                        params={"since": since_ms, "limit": 500})
    resp.raise_for_status()
    return resp.json().get("tracks", [])

def auth_spotify():
    return Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    ))

def ensure_playlist(sp):
    global PLAYLIST_ID
    if PLAYLIST_ID:
        return PLAYLIST_ID
    user_id = sp.current_user()["id"]
    pl = sp.user_playlist_create(
        user_id,
        name="Life with John Mayer – Last 12h",
        public=False,
        description="Auto-updated via Deploio"
    )
    PLAYLIST_ID = pl["id"]
    print(f"Created playlist {pl['name']} ({PLAYLIST_ID})")
    return PLAYLIST_ID

def find_uris(sp, tracks):
    uris, seen = [], set()
    for t in tracks:
        q = f"artist:{t['artist']} track:{t['title']}"
        items = sp.search(q=q, type="track", limit=1)["tracks"]["items"]
        if items:
            uri = items[0]["uri"]
            if uri not in seen:
                seen.add(uri)
                uris.append(uri)
    return uris

def update_playlist(sp, pid, uris):
    for i in range(0, len(uris), 100):
        chunk = uris[i:i+100]
        if i==0:
            sp.playlist_replace_items(pid, chunk)
        else:
            sp.playlist_add_items(pid, chunk)

def main():
    since = int((datetime.utcnow() - timedelta(hours=12)).timestamp() * 1000)
    print(f"Fetching since {datetime.utcnow() - timedelta(hours=12)} UTC…")
    tracks = get_xm_tracks(since)
    if not tracks:
        print("No tracks found.")
        return

    sp = auth_spotify()
    pid = ensure_playlist(sp)
    uris = find_uris(sp, tracks)
    if not uris:
        print("No matches found on Spotify.")
        return

    update_playlist(sp, pid, uris)
    print(f"Updated playlist {pid} with {len(uris)} tracks.")

if __name__ == "__main__":
    main()
EOF

chmod +x sync_xm_to_spotify.py
