from flask import Blueprint, request, jsonify
from services.translator import translate
from services.ai_engine import improve
from services.tts import speak, get_voices
from config import get_db
import datetime
import time

voice_routes = Blueprint("voice", __name__)

LANGUAGES = {
    "1": "en",
    "2": "hi",
    "3": "mr",
    "4": "ta",
    "5": "te",
    "6": "gu",
    "7": "bn",
    "8": "kn"
}


@voice_routes.route("/voice", methods=["POST"])
def voice():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid request"
            }), 400

        text = data.get("text", "").strip()
        lang_option = str(data.get("language", "1"))
        voice_id = data.get("voice", "EXAVITQu4vr4xnSDxMaL")

        if not text:
            return jsonify({
                "success": False,
                "error": "Empty input"
            }), 400

        print("User Input:", text)

        target_lang = LANGUAGES.get(lang_option, "en")
        print("Target Language:", target_lang)

        translated = translate(text, target_lang)
        print("Translated:", translated)

        improved = improve(translated)
        print("Improved:", improved)

        time.sleep(0.5)

        audio_url = speak(improved, voice_id)

        print("Audio URL:", audio_url)

        if not audio_url:
            return jsonify({
                "success": False,
                "error": "TTS generation failed"
            }), 500

        try:

            db = get_db()
            cur = db.cursor()

            cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_text TEXT,
                output_text TEXT,
                language TEXT,
                created_at TEXT
            )
            """)

            cur.execute(
                "INSERT INTO conversations(input_text,output_text,language,created_at) VALUES (?,?,?,?)",
                (text, improved, target_lang, str(datetime.datetime.now()))
            )

            db.commit()

        except Exception as db_error:
            print("Database Error:", db_error)

        return jsonify({
            "success": True,
            "text": improved,
            "audio": audio_url
        })

    except Exception as e:

        print("Voice API Error:", e)

        return jsonify({
            "success": False,
            "error": "Processing failed"
        }), 500


@voice_routes.route("/voices", methods=["GET"])
def voices():

    try:

        voices_list = get_voices()

        return jsonify({
            "success": True,
            "voices": voices_list
        })

    except Exception as e:

        print("Voice Fetch Error:", e)

        return jsonify({
            "success": False,
            "voices": []
        })