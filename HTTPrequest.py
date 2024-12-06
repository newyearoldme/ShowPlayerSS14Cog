import requests
import json
from utils.config_manager import load_main_config


config = load_main_config()

def fetch_player_list(server):
    headers = {
        "Authorization": f"SS14Token {server['token']}",
        "Accept": "application/json",
        "Actor": json.dumps({
            "Guid": config["actor"]["guid"],
            "Name": config["actor"]["name"],
        }),
    }

    try:
        # Выполняем запрос к API
        r = requests.get(f"http://{server['ip']}/admin/info", headers=headers)
        print(f"Запрос к серверу: {r}")
        if r.ok:
            data = r.json()
            players = data.get("Players", [])
            
            filtered_players = [
                player for player in players
                if not player.get("IsAdmin", False) or player.get("IsDeadminned", True)
            ]
            return filtered_players
        else:
            return {"error": f"HTTP {r.status_code}: {r.text}"}
    except requests.RequestException as e:
        return {"error": f"Ошибка подключения: {e}"}
