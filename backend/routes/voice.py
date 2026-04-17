from flask import Blueprint, request, jsonify
from services.translator import translate
from services.tts import speak, get_voices
from config import get_db
import datetime

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

        text = data.get("text", "").strip()
        source_option = str(data.get("source_language", "1"))
        target_option = str(data.get("target_language", "1"))
        voice_id = data.get("voice", "EXAVITQu4vr4xnSDxMaL")

        if not text:
            return jsonify({"success": False, "error": "Empty input"}), 400

        source_lang = LANGUAGES.get(source_option, "en")
        target_lang = LANGUAGES.get(target_option, "en")

        print("Input:", text)
        print("Source:", source_lang)
        print("Target:", target_lang)

        translated = translate(text, source_lang, target_lang)

        print("Translated:", translated)

        audio_url = speak(translated, voice_id)

        if not audio_url:
            return jsonify({
                "success": False,
                "error": "TTS failed"
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
                (text, translated, target_lang, str(datetime.datetime.now()))
            )

            db.commit()

        except Exception as db_error:
            print("DB Error:", db_error)

        return jsonify({
            "success": True,
            "text": translated,
            "audio": audio_url
        })

    except Exception as e:
        print("Error:", e)
        return jsonify({
            "success": False,
            "error": "Processing failed"
        }), 500


@voice_routes.route("/voices", methods=["GET"])
def voices():
    return jsonify({
        "success": True,
        "voices": get_voices()
    })