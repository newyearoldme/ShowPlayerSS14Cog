import requests
import json
from dotenv import load_dotenv
import os
from utils.config_loader import load_online_bots_config, OnlineServerBot


load_dotenv()

CONFIG_PATH = os.path.join("utils", "online_servers_bots.json")
online_servers = load_online_bots_config(CONFIG_PATH)

try:
    servers = load_online_bots_config(CONFIG_PATH)
except (FileNotFoundError, ValueError) as e:
    print(f"Ошибка загрузки конфигурации серверов: {e}")
    servers = []

def fetch_player_list(server: OnlineServerBot):
    headers = {
        "Authorization": f"SS14Token {server.token}",
        "Accept": "application/json",
        "Actor": json.dumps({
            "Guid": os.getenv("ACTOR_GUID"),
            "Name": os.getenv("ACTOR_NAME"),
        }),
    }
    
    try:
        r = requests.get(f"http://{server.ip}/admin/info", headers=headers)
        print(f"Requesting data from {server.ip}")
        print(f"Response: {r.status_code}, {r.text}")
        if r.ok:
            data = r.json()
            players = data.get("Players", [])
            
            # Фильтр по игрокам
            filtered_players = [
                player for player in players
                if not player.get("IsAdmin", False) or player.get("IsDeadminned", False)
            ]
            return filtered_players
        else:
            return {"error": f"HTTP {r.status_code}: {r.text}"}
    except requests.RequestException:
        return (f"Ошибка подключения: невозможно подключиться к серверу {server.ip}. Проверьте соединение или используйте VPN")
    
