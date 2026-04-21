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

FALLBACK_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"
MODEL             = "eleven_multilingual_v2"
TIMEOUT           = 60

GTTS_LANG_MAP = {
    "en": "en", "hi": "hi", "mr": "mr",
    "ta": "ta", "te": "te", "gu": "gu",
    "bn": "bn", "kn": "kn",
}

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


def _save_audio(audio_bytes: bytes) -> str:
    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    try:
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        url = f"{BACKEND_URL}/audio/{filename}"
        print(f"[TTS] ✅ Saved: {url}")
        return url
    except Exception as e:
        print(f"[TTS] ❌ Save error: {e}")
        return ""


def _elevenlabs(text: str, voice_id: str) -> bytes | None:
    if not API_KEY or len(API_KEY) < 20:
        print("[TTS] ElevenLabs skipped — no valid API key")
        return None

    print(f"[TTS] Trying ElevenLabs key={API_KEY[:8]}... voice={voice_id}")
    url     = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {
        "text":     text,
        "model_id": MODEL,
        "voice_settings": {
            "stability": 0.45, "similarity_boost": 0.80,
            "style": 0.00, "use_speaker_boost": True
        }
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 200:
            print(f"[TTS] ✅ ElevenLabs OK ({len(resp.content)} bytes)")
            return resp.content
        print(f"[TTS] ElevenLabs {resp.status_code}: {resp.text[:200]}")
        if resp.status_code == 422 and voice_id != FALLBACK_VOICE_ID:
            return _elevenlabs(text, FALLBACK_VOICE_ID)
    except requests.exceptions.Timeout:
        print("[TTS] ElevenLabs timeout")
    except Exception as e:
        print(f"[TTS] ElevenLabs error: {e}")
    return None


def _gtts_fallback(text: str, lang: str = "en") -> bytes | None:
    try:
        from gtts import gTTS
        import io
        gtts_lang = GTTS_LANG_MAP.get(lang, "en")
        print(f"[TTS] Using Google TTS fallback lang={gtts_lang}")
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        audio = buf.getvalue()
        if audio:
            print(f"[TTS] ✅ Google TTS OK ({len(audio)} bytes)")
            return audio
    except ImportError:
        print("[TTS] gTTS not installed — add gtts to requirements.txt")
    except Exception as e:
        print(f"[TTS] Google TTS error: {e}")
    return None


def speak(text: str, voice_id: str, target_lang: str = "en") -> str:
    if not text or not text.strip():
        return ""

    _purge_old_audio()

    # Try ElevenLabs first
    audio = _elevenlabs(text, voice_id)
    if not audio and voice_id != FALLBACK_VOICE_ID:
        audio = _elevenlabs(text, FALLBACK_VOICE_ID)

    # Fall back to Google TTS
    if not audio:
        print("[TTS] ElevenLabs failed — switching to Google TTS")
        audio = _gtts_fallback(text, target_lang)

    if not audio:
        print("[TTS] ❌ All TTS methods failed")
        return ""

    return _save_audio(audio)


def get_voices() -> list[dict]:
    if not API_KEY:
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
                return voices
    except Exception as e:
        print(f"[TTS] get_voices error: {e}")
    return DEFAULT_VOICES