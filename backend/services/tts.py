import os
import uuid
import glob
import time
import requests

API_KEY      = os.getenv("ELEVENLABS_API_KEY", "")
BACKEND_URL  = os.getenv("BACKEND_URL", "https://ai-voice-system-j313.onrender.com")

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR    = os.path.abspath(os.path.join(BASE_DIR, "..", "audio"))
os.makedirs(AUDIO_DIR, exist_ok=True)

FALLBACK_ID  = "EXAVITQu4vr4xnSDxMaL"   # Rachel — most reliable multilingual
MODEL        = "eleven_multilingual_v2"
TIMEOUT      = 60  # seconds

DEFAULT_VOICES = [
    {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Rachel"},
    {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Bella"},
    {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi"},
    {"id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh"},
    {"id": "ErXwobaYiN019PkySvjV",  "name": "Antoni"},
    {"id": "VR6AewLTigWG4xSOukaG",  "name": "Arnold"},
    {"id": "pNInz6obpgDQGcFmaJgB",  "name": "Adam"},
    {"id": "yoZ06aMxZJJ28mfd3POQ",  "name": "Sam"},
]


def _purge_old_audio(max_age_h: int = 2):
    cutoff = time.time() - max_age_h * 3600
    for fp in glob.glob(os.path.join(AUDIO_DIR, "*.mp3")):
        try:
            if os.path.getmtime(fp) < cutoff:
                os.remove(fp)
        except OSError:
            pass


def _call_elevenlabs(text: str, voice_id: str) -> bytes | None:
    if not API_KEY:
        print("[TTS] ERROR: ELEVENLABS_API_KEY is not set.")
        return None

    url     = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {
        "text":     text,
        "model_id": MODEL,
        "voice_settings": {
            "stability":         0.45,
            "similarity_boost":  0.80,
            "style":             0.00,
            "use_speaker_boost": True
        }
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.content
        print(f"[TTS] API returned {resp.status_code}: {resp.text[:300]}")
    except requests.exceptions.Timeout:
        print("[TTS] Request timed out.")
    except Exception as exc:
        print(f"[TTS] Request error: {exc}")
    return None


def speak(text: str, voice_id: str) -> str:
    """
    Convert text to speech. Returns public URL of the mp3, or '' on failure.
    Tries requested voice first, then falls back to Rachel.
    """
    if not text or not text.strip():
        return ""

    _purge_old_audio()

    voices = [voice_id]
    if voice_id != FALLBACK_ID:
        voices.append(FALLBACK_ID)

    audio = None
    for vid in voices:
        audio = _call_elevenlabs(text, vid)
        if audio:
            break
        if vid != voices[-1]:
            print(f"[TTS] Voice {vid} failed, trying fallback …")

    if not audio:
        print("[TTS] All voices failed.")
        return ""

    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    try:
        with open(filepath, "wb") as f:
            f.write(audio)
    except Exception as exc:
        print(f"[TTS] Failed to write audio file: {exc}")
        return ""

    url = f"{BACKEND_URL}/audio/{filename}"
    print(f"[TTS] Audio ready: {url}")
    return url


def get_voices() -> list[dict]:
    """Return list of available ElevenLabs voices, or built-in defaults."""
    if not API_KEY:
        return DEFAULT_VOICES
    try:
        resp = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": API_KEY},
            timeout=15
        )
        if resp.status_code == 200:
            raw = resp.json().get("voices", [])
            voices = [{"id": v["voice_id"], "name": v["name"]}
                      for v in raw if v.get("voice_id")]
            if voices:
                return voices
    except Exception as exc:
        print(f"[TTS] get_voices error: {exc}")
    return DEFAULT_VOICES