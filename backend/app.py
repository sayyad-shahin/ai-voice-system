import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from config import init_tables
from routes.auth import auth_routes
from routes.voice import voice_routes

app = Flask(__name__)
CORS(app, origins="*")

app.register_blueprint(auth_routes)
app.register_blueprint(voice_routes)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


@app.route("/")
def home():
    return {"status": "VoiceAI backend running", "version": "5.0"}


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/debug")
def debug():
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    smtp    = os.getenv("SMTP_EMAIL", "")
    backend = os.getenv("BACKEND_URL", "")
    db_path = os.getenv("RENDER_DB_PATH", "using local database folder")
    return jsonify({
        "ELEVENLABS_API_KEY":    f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else ("NOT SET" if not api_key else "TOO SHORT"),
        "ELEVENLABS_KEY_LENGTH": len(api_key),
        "BACKEND_URL":           backend  if backend else "NOT SET",
        "SMTP_EMAIL":            smtp     if smtp    else "NOT SET",
        "DB_PATH":               db_path,
    })


@app.route("/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)


if __name__ == "__main__":
    init_tables()
    port = int(os.environ.get("PORT", 5000))
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    print(f"[App] VoiceAI v5.0 starting on port {port}")
    print(f"[App] ElevenLabs key: {'SET ✅' if api_key else 'NOT SET ❌'}")
    app.run(host="0.0.0.0", port=port, debug=False)