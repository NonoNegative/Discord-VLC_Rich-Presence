
# Discord-VLC Rich Presence

This project binds Discord and VLC Media Player to display your currently playing media as your Discord Rich Presence. It supports dynamic album art, song details, and idle status, making your Discord profile reflect exactly what you're listening to in VLC.

## Features
- Shows currently playing song title and artist in Discord Rich Presence
- Displays album art (auto-uploaded to uguu and cached)
- Shows idle status when VLC is stopped or not playing music
- Custom configurable icons for playing and stopped states
- Easy configuration via `.env` file

---

## Setup Instructions

### 1. Clone the Repository

Clone this project to your local machine:

```sh
git clone git@github.com:NonoNegative/Discord-VLC_Rich-Presence.git
cd Discord-VLC_Rich-Presence
```

### 2. Install Python Dependencies

Install the required packages using pip:

```sh
pip install -r requirements.txt
```

### 3. Configure the `.env` File

Copy `.env.example` to `.env` and fill in your values:

```sh
cp .env.example .env
```

Edit `.env` with your favorite editor. Example:

```
DISCORD_CLIENT_ID=YOUR_DISCORD_APP_CLIENT_ID
VLC_HTTP_HOST=localhost
VLC_HTTP_PORT=8080
VLC_HTTP_PASSWORD=YOUR_VLC_PASSWORD
VLC_PATH=C:\Program Files\VideoLAN\VLC\vlc.exe
DEFAULT_LARGE_IMAGE_URL=https://i.pinimg.com/474x/0c/14/ca/0c14cab2d11fb8591224b1fcd8b049da.jpg
STOPPED_ICON=stopped
PLAYING_ICON=playing
```

#### `.env` Variable Descriptions
- `DISCORD_CLIENT_ID`: Your Discord application's client ID (see below)
- `VLC_HTTP_HOST`, `VLC_HTTP_PORT`, `VLC_HTTP_PASSWORD`: VLC web interface settings
- `VLC_PATH`: Path to your VLC executable
- `DEFAULT_LARGE_IMAGE_URL`: Fallback image for album art
- `STOPPED_ICON`, `PLAYING_ICON`: Icon keys for Discord Rich Presence (must be uploaded to your Discord app)

---

## Setting Up the Discord Developer Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name. This will appear as your 'Playing' status on your discord profile (e.g., Set name to `VLC Media Player` to show profile status as `Playing VLC Media Player`)
3. **OPTIONAL:** Go to "Rich Presence > Art Assets" and upload your icons (Not necessary if you do not want to, there are already pre-configured URLs in the env file.):
	- Upload images for your album art, playing icon, and stopped icon. Remember their names.
	- Set their names to the keys you use here to match `STOPPED_ICON` and `PLAYING_ICON` in your `.env`
4. Copy your application's **Client ID** and paste it into your `.env` as `DISCORD_CLIENT_ID`
5. Save your changes

---

## Configuring VLC for HTTP Interface

1. Open VLC and go to `Tools > Preferences > Show Settings: All`
2. Navigate to `Interface > Main interfaces`, check `Web`
3. Under `Main interfaces > Lua`, set your password and port (use in `.env`)
4. Restart VLC
5. VLC should now be accessible at `http://localhost:8080` (or your configured host/port)

---

## Running the Program

Simply run:

```sh
python main.py
```

If everything is configured correctly, your Discord profile will update with your VLC media info!

---

## Troubleshooting

- Make sure your Discord app is running and you are logged in
- Ensure VLC is running with the web interface enabled
- Check your `.env` values for typos
- If album art is not showing, make sure the image keys are uploaded to your Discord app
- For more info, see error messages printed in the terminal

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.
