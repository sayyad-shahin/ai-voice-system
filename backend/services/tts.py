import requests
import uuid
import os

# ==============================
# ELEVENLABS API KEY
# ==============================

API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not API_KEY:
    print("ERROR: ELEVENLABS_API_KEY not set")


# ==============================
# PATHS
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_FOLDER = os.path.join(BASE_DIR, "..", "audio")

os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Backend URL (Render or Local)
BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://ai-voice-system-j313.onrender.com"
)


# ==============================
# TEXT TO SPEECH
# ==============================

def speak(text, voice_id):

    try:

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "xi-api-key": API_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2"
        }

        # Send request
        r = requests.post(url, json=payload, headers=headers, timeout=30)

        # ==============================
        # FALLBACK VOICE
        # ==============================

        if r.status_code != 200:

            print("Voice failed. Trying fallback voice...")

            fallback_voice = "EXAVITQu4vr4xnSDxMaL"

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{fallback_voice}"

            r = requests.post(url, json=payload, headers=headers, timeout=30)

        if r.status_code != 200:

            print("TTS API Error:", r.text)
            return ""

        # ==============================
        # SAVE AUDIO FILE
        # ==============================

        filename = str(uuid.uuid4()) + ".mp3"
        filepath = os.path.join(AUDIO_FOLDER, filename)

        with open(filepath, "wb") as f:
            f.write(r.content)

        # ==============================
        # GENERATE AUDIO URL
        # ==============================

        audio_url = f"{BACKEND_URL}/audio/{filename}"

        print("Audio Generated:", audio_url)

        return audio_url

    except Exception as e:

        print("TTS Error:", str(e))
        return ""


# ==============================
# GET AVAILABLE VOICES
# ==============================

def get_voices():

    try:

        url = "https://api.elevenlabs.io/v1/voices"

        headers = {
            "xi-api-key": API_KEY
        }

        r = requests.get(url, headers=headers, timeout=20)

        if r.status_code == 200:

            data = r.json()

            voices = []

            for v in data.get("voices", []):

                voices.append({
                    "id": v.get("voice_id"),
                    "name": v.get("name")
                })

            if voices:
                return voices

    except Exception as e:

        print("Voice Fetch Error:", str(e))

    # ==============================
    # FALLBACK VOICES
    # ==============================

    return [
        {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Rachel"},
        {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Bella"},
        {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi"},
        {"id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh"},
        {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni"},
        {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold"},
        {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam"},
        {"id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam"}
    ]