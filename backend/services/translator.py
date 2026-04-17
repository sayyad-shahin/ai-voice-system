from deep_translator import GoogleTranslator

VALID_LANGS = {
    "en", "hi", "mr", "ta", "te", "gu", "bn", "kn"
}


def translate(text, target_lang):
    try:

        #  Skip detection (BIG latency reduction)
        source_lang = "auto"

        if target_lang not in VALID_LANGS:
            target_lang = "en"

        translated = GoogleTranslator(
            source=source_lang,
            target=target_lang
        ).translate(text)

        return translated if translated else text

    except Exception as e:
        print("Translate Error:", e)
        return text