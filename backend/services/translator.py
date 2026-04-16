from deep_translator import GoogleTranslator
from langdetect import detect

VALID_LANGS = {
    "en", "hi", "mr", "ta", "te", "gu", "bn", "kn"
}


def translate(text, target_lang):
    try:

        source_lang = detect(text)

        if source_lang not in VALID_LANGS:
            source_lang = "auto"

        if target_lang.startswith("en"):
            target_lang = "en"

        translated = GoogleTranslator(
            source=source_lang,
            target=target_lang
        ).translate(text)

        return translated

    except Exception:
        return text