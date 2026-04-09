import requests
import uuid
import os

API_KEY = "sk_777f15c4383559da769d79dd43377c2cb14bbfcc9c47cff0"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_FOLDER = os.path.join(BASE_DIR, "..", "audio")

# =============================
#  TEXT TO SPEECH
# =============================
def speak(text, voice_id):

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2"
    }

    try:
        r = requests.post(url, json=payload, headers=headers)

        # ❌ If selected voice fails → fallback
        if r.status_code != 200:
            print("Voice failed, using fallback")

            fallback_voice = "EXAVITQu4vr4xnSDxMaL"

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{fallback_voice}"
            r = requests.post(url, json=payload, headers=headers)

        # ❌ If still fail → return empty
        if r.status_code != 200:
            print("TTS completely failed")
            return ""

        os.makedirs(AUDIO_FOLDER, exist_ok=True)

        filename = str(uuid.uuid4()) + ".mp3"
        filepath = os.path.join(AUDIO_FOLDER, filename)

        with open(filepath, "wb") as f:
            f.write(r.content)

        return f"http://localhost:5000/audio/{filename}"

    except Exception as e:
        print("TTS Error:", e)
        return ""


# =============================
#  GET VOICES (DYNAMIC + FALLBACK)
# =============================
def get_voices():

    url = "https://api.elevenlabs.io/v1/voices"

    headers = {
        "xi-api-key": API_KEY
    }

    try:
        r = requests.get(url, headers=headers)

        if r.status_code == 200:
            data = r.json()

            voices = []

            for v in data.get("voices", []):
                voices.append({
                    "id": v.get("voice_id"),
                    "name": v.get("name")
                })

            # ✅ If API returns voices
            if voices:
                return voices

    except Exception as e:
        print("Voice Fetch Error:", e)

    #  FALLBACK (ALWAYS WORKING)
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