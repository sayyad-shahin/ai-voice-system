import datetime
from flask import Blueprint, request, jsonify
from services.translator import translate
from services.ai_engine import improve
from services.tts import speak, get_voices
from config import get_db, init_tables

voice_routes = Blueprint("voice", __name__)

LANG_MAP = {
    "1": "en",  "2": "hi",  "3": "mr",
    "4": "ta",  "5": "te",  "6": "gu",
    "7": "bn",  "8": "kn",
}

LANG_NAMES = {
    "en": "English", "hi": "Hindi",   "mr": "Marathi",
    "ta": "Tamil",   "te": "Telugu",  "gu": "Gujarati",
    "bn": "Bengali", "kn": "Kannada",
}


@voice_routes.route("/voice", methods=["POST"])
def voice():
    try:
        init_tables()
        data = request.get_json(silent=True) or {}

        text        = (data.get("text") or "").strip()
        lang_code   = str(data.get("language", "1"))
        voice_id    = data.get("voice") or "EXAVITQu4vr4xnSDxMaL"
        username    = (data.get("username") or "anonymous").strip()

        if not text:
            return jsonify({"success": False, "error": "No text received."}), 400
        if len(text) > 15000:
            return jsonify({"success": False,
                            "error": "Input too long. Please limit to 15,000 characters."}), 400

        target_lang = LANG_MAP.get(lang_code, "en")
        lang_name   = LANG_NAMES.get(target_lang, "English")
        print(f"[Voice] user={username} lang={target_lang} chars={len(text)}")

        # 1. Translate
        try:
            translated = translate(text, target_lang)
        except Exception as exc:
            print(f"[Voice] Translation error: {exc}")
            return jsonify({"success": False,
                            "error": "Translation failed. Please try again."}), 500

        if not translated or not translated.strip():
            return jsonify({"success": False,
                            "error": "Translation returned an empty result."}), 500

        # 2. Post-process
        final_text = improve(translated)

        # 3. TTS
        try:
            audio_url = speak(final_text, voice_id)
        except Exception as exc:
            print(f"[Voice] TTS error: {exc}")
            return jsonify({"success": False,
                            "error": "Voice generation failed. Please try again."}), 500

        if not audio_url:
            return jsonify({
                "success": False,
                "error": "Audio generation failed. Verify your ElevenLabs API key on Render."
            }), 500

        # 4. Persist (non-blocking)
        try:
            db  = get_db()
            row = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
            uid = row["id"] if row else None
            db.execute(
                "INSERT INTO conversations"
                "(user_id,username,input_text,output_text,language,audio_url,created_at)"
                " VALUES(?,?,?,?,?,?,?)",
                (uid, username, text, final_text, target_lang, audio_url,
                 datetime.datetime.now().isoformat())
            )
            db.commit()
            db.close()
        except Exception as exc:
            print(f"[Voice] DB error (non-fatal): {exc}")

        return jsonify({
            "success":   True,
            "text":      final_text,
            "audio":     audio_url,
            "lang_name": lang_name,
        })

    except Exception as exc:
        print(f"[Voice] Unhandled error: {exc}")
        return jsonify({"success": False, "error": "Processing failed. Please try again."}), 500


@voice_routes.route("/voices", methods=["GET"])
def voices():
    try:
        return jsonify({"success": True, "voices": get_voices()})
    except Exception as exc:
        print(f"[Voice] /voices error: {exc}")
        return jsonify({"success": False, "voices": []})