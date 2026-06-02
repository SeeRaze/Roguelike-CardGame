import os
import requests

# Твоя ссылка на веб-приложение (из блока "Веб-приложение" в Google)
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzTwddpcppYIajl_kFBE6Eog16zhhwWEfef6hE6NcIROK6VizjPxWufR9Nt2gMk2hsH/exec"

leaderboard_cache = []
is_loading = False
is_sending = False

def send_run_record(max_floor: int, kills: int, max_damage: int) -> bool:
    """Прямая синхронная отправка и скачивание ТОПа за один присест"""
    global leaderboard_cache
    try:
        payload = {
            "username": os.getlogin(),
            "max_floor": max_floor,
            "kills": kills,
            "max_damage": max_damage
        }
        
        print("[СЕТЬ] Отправляем рекорд напрямую в Google...")
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            raw_data = response.json()
            if isinstance(raw_data, list):
                leaderboard_cache = raw_data
                print(f"[СЕТЬ] Успешно! Записей прилетело: {len(leaderboard_cache)}")
                return True
        print(f"[СЕТЬ] Ошибка сервера: {response.status_code}")
        return False
        
    except requests.RequestException as e:
        print(f"[NETWORK] Ошибка отправки напрямую в Google: {e}")
        return False

def fetch_top_scores() -> list:
    """Просто отдает то, что скачали при смерти"""
    global leaderboard_cache
    return leaderboard_cache
