import os
import json

# Пути к файлам конфигурации
CONFIG_PATH = os.path.join("utils", "config.json")
SERVERS_CONFIG_PATH = os.path.join("utils", "online_servers_bots.json")

def load_config(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл конфигурации не найден: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка чтения JSON: {e}")

def load_main_config():
    return load_config(CONFIG_PATH)

def load_servers_config():
    return load_config(SERVERS_CONFIG_PATH)
