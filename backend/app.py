from flask import Flask, send_from_directory
from flask_cors import CORS
import os

from routes.auth import auth_routes
from routes.voice import voice_routes

app = Flask(__name__)

CORS(app)

app.register_blueprint(auth_routes)
app.register_blueprint(voice_routes)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_FOLDER = os.path.join(BASE_DIR, "audio")

os.makedirs(AUDIO_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return {"status": "AI Voice System Running"}


@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)