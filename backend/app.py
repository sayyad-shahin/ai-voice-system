import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from config import init_tables
from routes.auth import auth_routes
from routes.voice import voice_routes

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=False)

app.register_blueprint(auth_routes)
app.register_blueprint(voice_routes)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

@app.route("/")
def home():
    return {"status": "VoiceAI running", "version": "6.0"}

@app.route("/health")
def health():
    return {"status": "ok"}

@app.route("/debug")
def debug():
    key = os.getenv("ELEVENLABS_API_KEY", "")
    return jsonify({
        "ELEVENLABS_API_KEY":    f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "NOT SET",
        "ELEVENLABS_KEY_LENGTH": len(key),
        "BACKEND_URL":           os.getenv("BACKEND_URL", "NOT SET"),
        "SMTP_EMAIL":            os.getenv("SMTP_EMAIL", "NOT SET"),
    })

@app.route("/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)

if __name__ == "__main__":
    init_tables()
    port = int(os.environ.get("PORT", 5000))
    print(f"[App] VoiceAI v6.0 on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)