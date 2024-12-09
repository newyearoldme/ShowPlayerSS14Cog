import aiohttp
import json
from .utils.config_loader import OnlineServerBot


def create_headers(server: OnlineServerBot):
    return {
        "Authorization": f"SS14Token {server.token}",
        "Accept": "application/json",
        "Actor": json.dumps({
            "Guid": "4ea95dec-2225-4fa2-ba15-68af263873b0",
            "Name": "newyear",
        }),
    }

async def fetch_data(url: str, headers: dict):
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, headers=headers) as r:
                if r.ok:
                    return await r.json()
                else:
                    return {"error": f"HTTP {r.status}: {await r.text()}"}
    except aiohttp.ClientError as e:
        return {"error": f"Ошибка подключения: {e}"}

async def fetch_player_list(server: OnlineServerBot):
    url = f"http://{server.ip}/admin/info"
    headers = create_headers(server)
    data = await fetch_data(url, headers)

    if "error" in data:
        return data

    players = data.get("Players", [])
    return [
        player for player in players
        if not player.get("IsAdmin", False) or player.get("IsDeadminned", True)
    ]

async def fetch_admin_players(server: OnlineServerBot):
    url = f"http://{server.ip}/admin/players"
    headers = create_headers(server)
    data = await fetch_data(url, headers)

    if "error" in data:
        return data

    admins = data.get("admins", {})
    return {
        admin_name: attributes.get("title", "Без титула")
        for admin_name, attributes in admins.items()
    }
