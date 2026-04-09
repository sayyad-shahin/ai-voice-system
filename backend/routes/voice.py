from flask import Blueprint, request, jsonify
from services.translator import translate
from services.ai_engine import improve
from services.tts import speak, get_voices
from config import get_db
import datetime
import time  # 

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

# =============================
#  VOICE API (WITH DELAY)
# =============================
@voice_routes.route("/voice", methods=["POST"])
def voice():
    try:
        data = request.json

        text = data.get("text", "").strip()
        lang_option = str(data.get("language", "1"))
        voice_id = data.get("voice", "EXAVITQu4vr4xnSDxMaL")

        if not text:
            return jsonify({
                "success": False,
                "error": "Empty input"
            }), 400

        target_lang = LANGUAGES.get(lang_option, "en")

        print("Input:", text)

        #  Translate (AUTO DETECT → SELECTED LANGUAGE)
        translated = translate(text, target_lang)

        #  Improve (AFTER translation)
        improved = improve(translated)

        time.sleep(1.0)  # Response build delay

        #  TTS
        audio_url = speak(improved, voice_id)

        # Save to DB
        try:
            db = get_db()
            cur = db.cursor()

            cur.execute(
                "INSERT INTO conversations(input_text, output_text, language, created_at) VALUES (?,?,?,?)",
                (text, improved, target_lang, str(datetime.datetime.now()))
            )

            db.commit()

        except Exception as e:
            print("DB Error:", e)

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


# =============================
#  VOICES API
# =============================
@voice_routes.route("/voices", methods=["GET"])
def voices():
    return jsonify({
        "success": True,
        "voices": get_voices()
    })