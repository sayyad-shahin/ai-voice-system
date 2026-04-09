from deep_translator import GoogleTranslator
from langdetect import detect

#  Supported language codes (IMPORTANT)
VALID_LANGS = {
    "en", "hi", "mr", "ta", "te", "gu", "bn", "kn"
}

def translate(text, target_lang):

    try:
        #  Detect input language
        source_lang = detect(text)

        #  Fix unsupported detection
        if source_lang not in VALID_LANGS:
            source_lang = "auto"

        #  Force correct English code
        if target_lang.startswith("en"):
            target_lang = "en"

        print(f"Detected: {source_lang} → Target: {target_lang}")

        translated = GoogleTranslator(
            source=source_lang,
            target=target_lang
        ).translate(text)

        return translated

    except Exception as e:
        print("Translation Error:", e)
        return text