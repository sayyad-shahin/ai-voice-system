import requests
import uuid
import os

#  USE ENV VARIABLE (IMPORTANT)
API_KEY = os.environ.get("sk_65c15e2725440cec4c696fac58285fc6509ef118a10390f7")

#  RENDER BASE URL (CHANGE IF NEEDED)
BASE_URL = os.environ.get(
    "BASE_URL",
    "https://ai-voice-system-j313.onrender.com"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_FOLDER = os.path.join(BASE_DIR, "..", "audio")

# =============================
# TEXT TO SPEECH
# =============================
def speak(text, voice_id):

    if not API_KEY:
        print(" Missing ELEVENLABS_API_KEY")
        return ""

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

        #  ADD TIMEOUT (IMPORTANT)
        r = requests.post(url, json=payload, headers=headers, timeout=15)

        #  FALLBACK VOICE
        if r.status_code != 200:
            print(" Voice failed, using fallback")

            fallback_voice = "EXAVITQu4vr4xnSDxMaL"

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{fallback_voice}"
            r = requests.post(url, json=payload, headers=headers, timeout=15)

        #  TOTAL FAILURE
        if r.status_code != 200:
            print(" TTS completely failed:", r.text)
            return ""

        #  SAVE AUDIO
        os.makedirs(AUDIO_FOLDER, exist_ok=True)

        filename = str(uuid.uuid4()) + ".mp3"
        filepath = os.path.join(AUDIO_FOLDER, filename)

        with open(filepath, "wb") as f:
            f.write(r.content)

        #  RETURN PRODUCTION URL (FIXED)
        return f"{BASE_URL}/audio/{filename}"

    except Exception as e:
        print(" TTS Error:", e)
        return ""


# =============================
# GET VOICES
# =============================
def get_voices():

    if not API_KEY:
        print(" Missing ELEVENLABS_API_KEY")
        return fallback_voices()

    url = "https://api.elevenlabs.io/v1/voices"

    headers = {
        "xi-api-key": API_KEY
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code == 200:
            data = r.json()

            voices = [
                {
                    "id": v.get("voice_id"),
                    "name": v.get("name")
                }
                for v in data.get("voices", [])
                if v.get("voice_id") and v.get("name")
            ]

            if voices:
                return voices

        print(" Voice API failed:", r.text)

    except Exception as e:
        print(" Voice Fetch Error:", e)

    return fallback_voices()


# =============================
# FALLBACK VOICES
# =============================
def fallback_voices():
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