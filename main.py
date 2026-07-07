import socket
import time
from pypresence import Presence
import json
import os
import sys
import urllib.request
import tempfile
import hashlib

CONFIG_FILE = "config.json"
GAMES_FILE = "games.json"
GAMES_URL = "https://mazegroup.org/download/wiiurpc/games.json"

print("WiiU RPC - By Yanis Roca--Boyer")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"The configuration file '{CONFIG_FILE}' is missing.")
        create_config()
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading the config file: {e}")
        sys.exit(1)
    for key in ["CLIENT_ID", "IP", "PORT"]:
        if key not in config or not config[key]:
            print(f"The parameter '{key}' is not configured in '{CONFIG_FILE}'.")
            create_config()
            return load_config()
    return config

def create_config():
    print("Please configure the missing parameters in 'config.json'.")
    client_id = input("CLIENT_ID (required): ").strip()
    ip = input("IP (e.g. 0.0.0.0): ").strip()
    port = input("PORT (e.g. 5005): ").strip()
    if not client_id or not ip or not port:
        print("All fields are required.")
        sys.exit(1)
    try:
        port = int(port)
    except ValueError:
        print("PORT must be an integer.")
        sys.exit(1)
    config = {
        "CLIENT_ID": client_id,
        "IP": ip,
        "PORT": port
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    print("Configuration file updated.")

def file_hash(filename):
    """Retourne le hash SHA256 du fichier fourni."""
    h = hashlib.sha256()
    with open(filename, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def url_file_hash(url):
    h = hashlib.sha256()
    
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    req = urllib.request.Request(url, headers=headers)
    
    with urllib.request.urlopen(req) as response:
        content = response.read()
        h.update(content)
        try:
            data = json.loads(content.decode("utf-8"))
        except Exception:
            data = {}
    return h.hexdigest(), data, content
def ensure_latest_games_file():
    need_update = False
    local_hash = None
    remote_hash = None

    try:
        remote_hash, remote_data, remote_bytes = url_file_hash(GAMES_URL)
    except Exception as e:
        print(f"❌ Impossible de télécharger la liste des jeux ({e})")
        return

    if not os.path.exists(GAMES_FILE):
        print("Le fichier games.json n'existe pas localement, téléchargement de la dernière version...")
        need_update = True
    else:
        try:
            local_hash = file_hash(GAMES_FILE)
            if local_hash != remote_hash:
                print("games.json différent de la version distante, mise à jour...")
                need_update = True
        except Exception as e:
            print(f"Erreur lors de la vérification de games.json : {e}")
            need_update = True

    if need_update:
        try:
            with open(GAMES_FILE, "wb") as f:
                f.write(remote_bytes)
            print("games.json mis à jour avec succès !")
        except Exception as e:
            print(f"Erreur lors de l'écriture de games.json : {e}")

ensure_latest_games_file()

config = load_config()
DEFAULT_CLIENT_ID = str(config["CLIENT_ID"])
UDP_IP = str(config["IP"])
UDP_PORT = int(config["PORT"])

RPC = None
current_client_id = DEFAULT_CLIENT_ID

def connect_to_discord(client_id):
    """Handles dynamic connection and disconnection for Discord RPC"""
    global RPC, current_client_id

    if RPC is not None:
        try:
            RPC.close()
            print("Disconnecting from the previous Discord application...")
        except Exception:
            pass

    print(f"Connecting to Discord with ID: {client_id}...")
    try:
        RPC = Presence(client_id)
        RPC.connect()
        current_client_id = client_id
        print("Successfully connected to Discord!")
        return True
    except Exception as e:
        print(f"Failed to connect to Discord: {e}")
        RPC = None
        return False

connect_to_discord(DEFAULT_CLIENT_ID)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Waiting for Wii U packets on port {UDP_PORT}...")

last_update = 0

try:
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            try:
                message = json.loads(data.decode('utf-8', errors='ignore').strip())
            except Exception:
                message = {}
        except Exception:
            continue

        if message and (time.time() - last_update > 15):
            print(f"Received from Wii U ({addr[0]}): {message}")

            game_name = message.get("app", "Unknown game")
            nnid = message.get("nnid", "Unknown")
            details = "In game"

            if os.path.exists(GAMES_FILE):
                with open(GAMES_FILE, "r", encoding="utf-8") as f:
                    games_data = json.load(f)
            else:
                games_data = {}

            game_entry = games_data.get(game_name.upper())

            logo_name = game_entry.get("logo", "wiiu_logo") if game_entry else "wiiu_logo"
            if game_entry and "name" in game_entry:
                game_name = game_entry["name"]

            target_client_id = DEFAULT_CLIENT_ID
            if game_entry and "client_id" in game_entry:
                target_client_id = str(game_entry["client_id"])

            game_desc = f"In game | {game_name}"
            if game_entry and "description" in game_entry:
                game_desc = str(game_entry["description"])

            if target_client_id != current_client_id:
                connect_to_discord(target_client_id)

            if RPC:
                try:
                    RPC.update(
                        state=details,
                        details=game_desc,
                        large_image=logo_name,
                        large_text=game_name
                    )
                    last_update = time.time()
                except Exception as e:
                    print(f"Error updating status: {e}")
except Exception:
    print(f"❌ Error: {Exception}")
except KeyboardInterrupt:
    print("\nStopping RPC client.")
    if RPC:
        RPC.close()