import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from config import init_tables
from routes.auth import auth_routes
from routes.voice import voice_routes

app = Flask(__name__)

# ── CORS: allow ALL origins on ALL routes including error responses ──────────
CORS(app,
     resources={r"/*": {"origins": "*"}},
     supports_credentials=False,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# ── Explicitly handle OPTIONS preflight for ALL routes ────────────────────────
@app.before_request
def handle_preflight():
    from flask import request, Response
    if request.method == "OPTIONS":
        res = Response()
        res.headers["Access-Control-Allow-Origin"]  = "*"
        res.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        res.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        res.headers["Access-Control-Max-Age"]       = "86400"
        return res

# ── Add CORS headers to EVERY response (including 404/500 errors) ────────────
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

app.register_blueprint(auth_routes)
app.register_blueprint(voice_routes)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


@app.route("/")
def home():
    return {"status": "VoiceAI running", "version": "6.1"}


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
        "SMTP_EMAIL":            os.getenv("SMTP_EMAIL",  "NOT SET"),
        "DB_PATH":               os.getenv("RENDER_DB_PATH", "local folder"),
        "REGISTER_ROUTE":        "active",
    })


@app.route("/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)


@app.route("/test-register", methods=["GET"])
def test_register():
    """Quick test to confirm /register/request route is reachable."""
    return jsonify({"status": "register route is reachable", "method": "use POST /register/request"})


if __name__ == "__main__":
    init_tables()
    port = int(os.environ.get("PORT", 5000))
    key  = os.getenv("ELEVENLABS_API_KEY", "")
    print(f"[App] VoiceAI v6.1 on port {port}")
    print(f"[App] ElevenLabs: {'SET' if key else 'NOT SET'}")
    app.run(host="0.0.0.0", port=port, debug=False)