import time
import requests
import subprocess
import os
import json
from pypresence import Presence
from dotenv import load_dotenv
from urllib.parse import unquote, urlparse
from colorama import init, Fore, Style

# --- CONFIGURATION ---
load_dotenv()
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
VLC_HTTP_HOST = os.getenv("VLC_HTTP_HOST")
VLC_HTTP_PORT = int(os.getenv("VLC_HTTP_PORT", "8080"))
VLC_HTTP_PASSWORD = os.getenv("VLC_HTTP_PASSWORD")
VLC_PATH = os.getenv("VLC_PATH")
DEFAULT_LARGE_IMAGE_URL = os.getenv("DEFAULT_LARGE_IMAGE_URL", "vlc")
STOPPED_ICON = os.getenv("STOPPED_ICON", "stopped")
PLAYING_ICON = os.getenv("PLAYING_ICON", "playing")
PAUSED_ICON = os.getenv("PAUSED_ICON", "paused")
STRIP_WORDS = [w.strip() for w in os.getenv("STRIP_WORDS", "").split(",") if w.strip()]

# Initialize colorama
init(autoreset=True)

# Global variable to prevent concurrent uploads
currently_uploading = False

def upload_to_uguu(filepath: str) -> str:
    """Upload file to uguu and return the URL"""
    url = "https://uguu.se/upload?output=json"
    with open(filepath, "rb") as f:
        files = {"files[]": f}
        response = requests.post(url, files=files)
    response.raise_for_status()

    data = response.json()
    if data.get("success") and "files" in data:
        return data["files"][0]["url"]
    else:
        raise RuntimeError(f"Unexpected response: {data}")

def load_art_cache():
    """Load the art.json cache file"""
    try:
        with open("art.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_art_cache(cache):
    """Save the art cache to art.json"""
    with open("art.json", "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def is_url_valid(url):
    """Check if URL is valid and accessible"""
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def get_album_art_url(album, art_path):
    """Get album art URL, either from cache or by uploading"""
    global currently_uploading
    
    if not album or not art_path:
        # Only print if user is expecting album art but it's missing
        return DEFAULT_LARGE_IMAGE_URL
    
    # Load art cache
    art_cache = load_art_cache()
    # Check if album is already cached
    if album in art_cache:
        cached_url = art_cache[album]
        if is_url_valid(cached_url):
            return cached_url
        else:
            del art_cache[album]
            save_art_cache(art_cache)
    if currently_uploading:
        return DEFAULT_LARGE_IMAGE_URL
    try:
        if not os.path.exists(art_path):
            return DEFAULT_LARGE_IMAGE_URL
        currently_uploading = True
        print(f"Uploading album art for: {album}")
        art_url = upload_to_uguu(art_path)
        art_cache[album] = art_url
        save_art_cache(art_cache)
        print(f"Album art uploaded and cached at {art_url}.")
        return art_url
    except Exception as e:
        print(f"Album art upload failed: {e}")
        return DEFAULT_LARGE_IMAGE_URL
    finally:
        currently_uploading = False

def launch_vlc():
    if not VLC_PATH or not os.path.exists(VLC_PATH):
        print(Fore.RED + Style.BRIGHT + f"[ERROR] VLC executable not found at: {VLC_PATH}")
        return
    cmd = [
        VLC_PATH,
        "--extraintf=http",
        f"--http-host=0.0.0.0",
        f"--http-port={VLC_HTTP_PORT}",
        f"--http-password={VLC_HTTP_PASSWORD}"
    ]
    print(Fore.CYAN + Style.BRIGHT + "Launching VLC with HTTP interface...")
    subprocess.Popen(cmd)

def get_vlc_status():
    url = f"http://{VLC_HTTP_HOST}:{VLC_HTTP_PORT}/requests/status.json"
    try:
        resp = requests.get(url, auth=("", VLC_HTTP_PASSWORD))
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def get_song_info(status):
    if not status or "information" not in status:
        return None, None, None, None
    info = status["information"].get("category", {}).get("meta", {})
    def safe_decode(val):
        if isinstance(val, bytes):
            try:
                return val.decode("utf-8")
            except Exception:
                return val.decode("latin1", errors="replace")
        elif isinstance(val, str):
            try:
                return val.encode("latin1").decode("utf-8")
            except Exception:
                return val
        return str(val)
    title = safe_decode(info.get("title") or info.get("filename") or "Unknown")
    artist = safe_decode(info.get("artist") or "")
    album = safe_decode(info.get("album") or "")
    art_path = safe_decode(info.get("artwork_url") or info.get("artwork") or "")
    return title, artist, album, art_path

def main():
    launch_vlc()
    time.sleep(2)  # Give VLC time to start
    rpc = Presence(DISCORD_CLIENT_ID)
    while True:
        try:
            rpc.connect()
            break
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"[ERROR] Could not connect to Discord: {e}")
            print(Fore.YELLOW + "Retrying in 10 seconds...")
            time.sleep(10)
    print(Fore.GREEN + Style.BRIGHT + "[INFO] Discord Rich Presence started.")
    last_title = last_artist = last_album = last_art_path = None
    last_start = last_end = None

    while True:
        status = get_vlc_status()
        title, artist, album, art_path = get_song_info(status)
        # Decode album and art_path here
        album = unquote(album) if album else album
        if art_path and art_path.startswith("file://"):
            parsed = urlparse(art_path)
            decoded_path = unquote(parsed.path)
            if decoded_path.startswith("/") and ":" in decoded_path:
                decoded_path = decoded_path[1:]
            art_path = decoded_path
        elif art_path:
            art_path = unquote(art_path)
        # Timing fix and state handling
        start = end = None
        vlc_state = status.get("state") if status else None
        if vlc_state == "playing":
            position = status.get("time", 0)
            duration = status.get("length", 0)
            now = int(time.time())
            start = now - position
            end = start + duration
        if (title != last_title or artist != last_artist or album != last_album or art_path != last_art_path or start != last_start or end != last_end or vlc_state):
            # Strip configured words from title
            stripped_title = title if title else None
            if stripped_title:
                for word in STRIP_WORDS:
                    if word:
                        stripped_title = stripped_title.replace(word, "")
            details = f"{stripped_title}" if stripped_title else None
            state = f"{artist}" if artist else None

            # Only update if details is not None
            if details:
                large_image_url = get_album_art_url(album, art_path)
                update_args = dict(details=details, large_image=large_image_url, large_text="VLC Media Player")
                if state:
                    update_args["state"] = state
                # Handle playing/paused time and icon
                if vlc_state == "playing" and start and end and duration > 0:
                    update_args["start"] = start
                    update_args["end"] = end
                    if large_image_url == DEFAULT_LARGE_IMAGE_URL:
                        update_args["small_image"] = PLAYING_ICON
                elif vlc_state == "paused":
                    update_args["small_image"] = PAUSED_ICON
                    update_args["small_text"] = "Paused"
                    update_args.pop("start", None)
                    update_args.pop("end", None)
                else:
                    if large_image_url == DEFAULT_LARGE_IMAGE_URL:
                        update_args["small_image"] = PLAYING_ICON
                try:
                    rpc.update(**update_args)
                    print(Fore.GREEN + Style.BRIGHT + f"[INFO] Now playing: {details} {'-' if state else ''} {state if state else ''} [{vlc_state}]")
                except Exception as e:
                    print(Fore.RED + Style.BRIGHT + f"[ERROR] Failed to update Rich Presence: {e}")
            else:
                # Update with stopped/idle state
                update_args = dict(
                    details="Idling",
                    state="Nothing is playing",
                    large_image=DEFAULT_LARGE_IMAGE_URL,
                    large_text="VLC Media Player",
                    small_image=STOPPED_ICON
                )
                try:
                    rpc.update(**update_args)
                    print(Fore.YELLOW + Style.BRIGHT + "[INFO] VLC is stopped or no song info available. Updated to idle status.")
                except Exception as e:
                    print(Fore.RED + Style.BRIGHT + f"[ERROR] Failed to update Rich Presence: {e}")
            last_title, last_artist, last_album, last_art_path, last_start, last_end = title, artist, album, art_path, start, end
        time.sleep(5)

if __name__ == "__main__":
    print(Fore.CYAN + Style.BRIGHT + f"Make sure VLC is installed at {VLC_PATH}")
    main()
