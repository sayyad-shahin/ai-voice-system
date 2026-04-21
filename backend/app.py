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
    return {"status": "VoiceAI backend running", "version": "3.0"}


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/debug")
def debug():
    """
    Check if environment variables are set correctly.
    Visit: https://ai-voice-system-j313.onrender.com/debug
    """
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    smtp    = os.getenv("SMTP_EMAIL", "")
    backend = os.getenv("BACKEND_URL", "")

    return jsonify({
        "ELEVENLABS_API_KEY": f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else ("NOT SET ❌" if not api_key else "TOO SHORT ❌"),
        "ELEVENLABS_KEY_LENGTH": len(api_key),
        "BACKEND_URL":  backend if backend else "NOT SET ❌",
        "SMTP_EMAIL":   smtp    if smtp    else "NOT SET (optional)",
        "DB_PATH":      os.getenv("RENDER_DB_PATH", "using local database folder"),
    })


@app.route("/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)


if __name__ == "__main__":
    init_tables()
    port = int(os.environ.get("PORT", 5000))
    print(f"[App] VoiceAI starting on port {port}")

    # Startup checks
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    if not api_key:
        print("[App] ⚠️  WARNING: ELEVENLABS_API_KEY is not set!")
    else:
        print(f"[App] ✅ ElevenLabs key loaded: {api_key[:8]}...")

    app.run(host="0.0.0.0", port=port, debug=False)