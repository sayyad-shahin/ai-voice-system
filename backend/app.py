import os
from flask import Flask, send_from_directory
from flask_cors import CORS

from config import init_tables
from routes.auth import auth_routes
from routes.voice import voice_routes

app = Flask(__name__)
CORS(app, origins="*")

app.register_blueprint(auth_routes)
app.register_blueprint(voice_routes)

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR  = os.path.join(BASE_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


@app.route("/")
def home():
    return {"status": "VoiceAI backend running", "version": "2.1"}


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)


if __name__ == "__main__":
    init_tables()
    port = int(os.environ.get("PORT", 5000))
    print(f"[App] VoiceAI backend starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)