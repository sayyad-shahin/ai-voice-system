from flask import Flask, send_from_directory
from flask_cors import CORS
import os

# IMPORT ROUTES
from routes.auth import auth_routes
from routes.voice import voice_routes

app = Flask(__name__)

# ENABLE CORS (important for Netlify)
CORS(app)

# REGISTER ROUTES
app.register_blueprint(auth_routes)
app.register_blueprint(voice_routes)

# AUDIO FOLDER SETUP
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_FOLDER = os.path.join(BASE_DIR, "audio")

os.makedirs(AUDIO_FOLDER, exist_ok=True)

# =============================
# HOME ROUTE
# =============================
@app.route("/")
def home():
    return {"status": "AI Voice System Running "}


# =============================
# SERVE AUDIO FILES
# =============================
@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)


# =============================
# RUN SERVER (RENDER READY)
# =============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  #Render uses PORT
    app.run(host="0.0.0.0", port=port)