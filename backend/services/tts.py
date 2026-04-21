import os
import uuid
import glob
import time
import requests

API_KEY     = os.getenv("ELEVENLABS_API_KEY", "").strip()
BACKEND_URL = os.getenv("BACKEND_URL", "https://ai-voice-system-j313.onrender.com").strip()

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "audio"))
os.makedirs(AUDIO_DIR, exist_ok=True)

FALLBACK_ID = "EXAVITQu4vr4xnSDxMaL"   # Rachel
MODEL       = "eleven_multilingual_v2"
TIMEOUT     = 60

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
    # ── Key check ───────────────────────────────────────────
    if not API_KEY:
        print("[TTS]  ELEVENLABS_API_KEY is NOT set in environment variables!")
        print("[TTS]    Go to Render → your service → Environment → Add ELEVENLABS_API_KEY")
        return None

    if len(API_KEY) < 20:
        print(f"[TTS]  ELEVENLABS_API_KEY looks invalid (too short): '{API_KEY[:8]}...'")
        return None

    print(f"[TTS] Using API key: {API_KEY[:8]}...{API_KEY[-4:]} (voice={voice_id})")

    url     = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key":   API_KEY,
        "Content-Type": "application/json"
    }
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

    for attempt in range(2):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)

            if resp.status_code == 200:
                print(f"[TTS]  Audio generated successfully ({len(resp.content)} bytes)")
                return resp.content

            # Log the exact error from ElevenLabs
            print(f"[TTS]  API error {resp.status_code}: {resp.text[:500]}")

            if resp.status_code == 401:
                print("[TTS]    → Invalid API key. Get a new one from elevenlabs.io")
                return None
            if resp.status_code == 429:
                print("[TTS]    → Rate limit / quota exceeded. Create a new ElevenLabs account.")
                return None
            if resp.status_code == 422:
                print("[TTS]    → Invalid voice_id. Using fallback.")
                return None

        except requests.exceptions.Timeout:
            print(f"[TTS] ⏱ Timeout on attempt {attempt+1}")
            if attempt == 0:
                time.sleep(1)
        except Exception as e:
            print(f"[TTS]  Request error: {e}")
            return None

    return None


def speak(text: str, voice_id: str) -> str:
    """Convert text to speech. Returns public URL of mp3 or '' on failure."""
    if not text or not text.strip():
        return ""

    _purge_old_audio()

    # Try requested voice first, then fallback
    voices_to_try = [voice_id]
    if voice_id != FALLBACK_ID:
        voices_to_try.append(FALLBACK_ID)

    audio_bytes = None
    for vid in voices_to_try:
        audio_bytes = _call_elevenlabs(text, vid)
        if audio_bytes:
            break
        if vid != voices_to_try[-1]:
            print(f"[TTS] Trying fallback voice: {FALLBACK_ID}")

    if not audio_bytes:
        print("[TTS]  All voice attempts failed.")
        return ""

    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    try:
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
    except Exception as e:
        print(f"[TTS]  Failed to save audio file: {e}")
        return ""

    audio_url = f"{BACKEND_URL}/audio/{filename}"
    print(f"[TTS]  Audio URL: {audio_url}")
    return audio_url


def get_voices() -> list[dict]:
    """Return available ElevenLabs voices, or built-in defaults."""
    if not API_KEY:
        print("[TTS] No API key — returning default voices list")
        return DEFAULT_VOICES
    try:
        resp = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": API_KEY},
            timeout=15
        )
        if resp.status_code == 200:
            raw    = resp.json().get("voices", [])
            voices = [{"id": v["voice_id"], "name": v["name"]}
                      for v in raw if v.get("voice_id")]
            if voices:
                print(f"[TTS] Loaded {len(voices)} voices from ElevenLabs")
                return voices
        print(f"[TTS] Could not load voices ({resp.status_code}), using defaults")
    except Exception as e:
        print(f"[TTS] get_voices error: {e}")
    return DEFAULT_VOICES