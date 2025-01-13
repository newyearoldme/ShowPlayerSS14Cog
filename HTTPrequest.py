import requests
import json
from utils.config_loader import OnlineServerBot


def create_headers(server: OnlineServerBot):
    return {
        "Authorization": f"SS14Token {server.admin_token}",
        "Accept": "application/json",
        "Actor": json.dumps({
            "Guid": "4ea95dec-2225-4fa2-ba15-68af263873b0",
            "Name": "newyear",
        }),
    }


def fetch_data(url: str, headers: dict):
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.ok:
            return r.json()
        
        response_data = r.json()
        if "ErrorCode" in response_data:
            match response_data["ErrorCode"]:
                case 2:
                    return {"error": "Токен невалидный"}
                case 6:
                    return {"error": "Недействительное значение в заголовке авторизации. Проверьте токен"}
                case _:
                    return {"error": f"Сервер вернул ошибку: {response_data.get('Message', 'Неизвестная ошибка')}"}
        
        match r.status_code:
            case 401:
                return {"error": "Недействительный токен авторизации"}
            case 403:
                return {"error": "Доступ запрещен. Возможно, токен невалидный"}
            case 404:
                return {"error": "Сервер не найден"}
            case _:
                return {"error": f"HTTP {r.status_code}: {r.text}"}
    except requests.Timeout:
        return {"error": "Превышено время ожидания запроса"}
    except requests.RequestException as e:
        return {"error": f"Ошибка подключения: {e}"}


def fetch_player_list(server: OnlineServerBot):
    url = f"http://{server.ip}/admin/info"
    headers = create_headers(server)
    data = fetch_data(url, headers)

    if "error" in data:
        return data

    players = data.get("Players", [])
    return [
        player.get("Name") for player in players
        if not player.get("IsAdmin", False) or player.get("IsDeadminned", True)
    ]


def fetch_admin_players(server: OnlineServerBot):
    url = f"http://{server.ip}/admin/players"
    headers = create_headers(server)
    data = fetch_data(url, headers)

    if "error" in data:
        return data

    admins = data.get("admins", {})
    return {
        admin_name: {
            "title": attributes.get("title", "Без поста"),
            "readmin": attributes.get("isActive", False)
        }
        for admin_name, attributes in admins.items()
    }
