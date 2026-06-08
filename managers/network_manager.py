import os
import threading
import requests

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzEHCwtWOoLS4WSGvtSYxkFdfZ5x9biAYc_kYBNdADbHBmX_DqosyxDaNmv_vOhYoIp/exec"

leaderboard_cache = []

def _get_username() -> str:
    """БАГ 6: os.getlogin() падает на некоторых системах — используем fallback."""
    try:
        return os.getlogin()
    except OSError:
        return os.environ.get("USERNAME", os.environ.get("USER", "Unknown"))

def _send_in_background(payload: dict):
    """Внутренняя функция — выполняется в отдельном потоке."""
    global leaderboard_cache
    try:
        print("[СЕТЬ] Отправляем рекорд в Google...")
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
        if response.status_code == 200:
            raw_data = response.json()
            if isinstance(raw_data, list):
                leaderboard_cache = raw_data
                print(f"[СЕТЬ] Успешно! Записей прилетело: {len(leaderboard_cache)}")
                return
        print(f"[СЕТЬ] Ошибка сервера: {response.status_code}")
    except requests.RequestException as e:
        print(f"[СЕТЬ] Ошибка отправки: {e}")

def send_run_record(max_floor: int, kills: int, max_damage: int,
                    player_class: str = "—"):
    """БАГ 5: запускает отправку в фоновом потоке — игра не зависает."""
    payload = {
        "username": _get_username(),
        "class": player_class,
        "max_floor": max_floor,
        "kills": kills,
        "max_damage": max_damage,
    }
    thread = threading.Thread(target=_send_in_background, args=(payload,), daemon=True)
    thread.start()

def fetch_top_scores() -> list:
    """Возвращает закэшированные данные (обновляются эхом POST при смерти + фоновым
    GET при открытии доски через refresh_leaderboard)."""
    return leaderboard_cache


def _fetch_in_background():
    """Внутренняя функция — тянет ТОП из таблицы в отдельном потоке."""
    global leaderboard_cache
    try:
        print("[СЕТЬ] Запрашиваем доску из Google...")
        response = requests.get(GOOGLE_SCRIPT_URL, timeout=10)
        if response.status_code == 200:
            raw_data = response.json()
            if isinstance(raw_data, list):
                leaderboard_cache = raw_data
                print(f"[СЕТЬ] Доска получена. Записей: {len(leaderboard_cache)}")
                return
        print(f"[СЕТЬ] Ошибка получения доски: {response.status_code}")
    except (requests.RequestException, ValueError) as e:
        print(f"[СЕТЬ] Ошибка получения доски: {e}")


def refresh_leaderboard():
    """Обновить кэш доски из таблицы в фоне (не блокирует UI). Зовётся при открытии
    доски трофеев. Офлайн/ошибка → кэш не меняется (last-known остаётся)."""
    thread = threading.Thread(target=_fetch_in_background, daemon=True)
    thread.start()