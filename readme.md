# WiiU Discord RPC
Python script to link your WiiU activity to your Discord activity.
Compatible only with the [aroma Discord Rich Presence plugin](https://hb-app.store/wiiu/RichPresence).

You can view the list of games with a custom RPC in `games.json`. If the game does not appear in this file, the rich presence will display as "Nintendo WiiU" with the title of the game you are playing. (Note: Homebrew applications are all grouped under "Homebrew Applications," so you won’t see their individual names.)

## Compatibility
The Python script is compatible with Windows, MacOS, and Linux on both x64 and arm64.

## Installation
1. Copy the git repo into a folder.
2. Install `pypresence` using `pip install pypresence`
3. Set your WiiU's IP address (leave it as `0.0.0.0` if you’re not sure) and the port (leave it as `5005` if you haven’t changed the port) in the `config.json` file.
