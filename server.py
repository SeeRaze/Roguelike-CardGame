import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# !!! СЮДА ВСТАВЬ ССЫЛКУ, КОТОРУЮ СКОПИРОВАЛ НА ШАГЕ 1.8 !!!
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzTwddpcppYIajl_kFBE6Eog16zhhwWEfef6hE6NcIROK6VizjPxWufR9Nt2gMk2hsH/exec"

@app.route('/api/leaderboard', methods=['POST'])
def save_score():
    if not request.json:
        return jsonify({"status": "error"}), 400
    # Просто перекидываем данные в Гугл
    response = requests.post(GOOGLE_SCRIPT_URL, json=request.json)
    return jsonify(response.json()), response.status_code

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    # Запрашиваем ТОП-10 из Гугла
    response = requests.get(GOOGLE_SCRIPT_URL)
    return jsonify(response.json()), response.status_code

if __name__ == '__main__':
    print("[СЕРВЕР] Мост успешно запущен по упрощенной схеме! Жду подключений...")
    app.run(host='0.0.0.0', port=5000)
