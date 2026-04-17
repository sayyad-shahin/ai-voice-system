from deep_translator import GoogleTranslator
from langdetect import detect

def translate(text, target_lang):
    try:
        source_lang = detect(text)

        translated = GoogleTranslator(
            source=source_lang,
            target=target_lang
        ).translate(text)

        return translated if translated else text

    except Exception as e:
        print("Translate Error:", e)
        return text