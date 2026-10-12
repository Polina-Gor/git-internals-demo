import random
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

MOODS = [
    {"name": "sunset",  "color": "#ff7e5f", "text": "Тёплый закат"},
    {"name": "ocean",   "color": "#2193b0", "text": "Спокойный океан"},
    {"name": "forest",  "color": "#11998e", "text": "Лесная свежесть"},
    {"name": "night",   "color": "#2c3e50", "text": "Ночная тишина"},
    {"name": "candy",   "color": "#ee9ca7", "text": "Сладкое настроение"},
    {"name": "lemon",   "color": "#f7971e", "text": "Лимонный день"},
]

@app.route("/api/mood")
def mood():
    m = random.choice(MOODS)
    return jsonify({
        "mood": m["name"],
        "color": m["color"],
        "text": m["text"],
        "service": "backend"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
