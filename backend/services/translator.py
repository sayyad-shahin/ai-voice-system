from deep_translator import GoogleTranslator

def translate(text, source_lang, target_lang):
    try:
        translated = GoogleTranslator(
            source=source_lang,
            target=target_lang
        ).translate(text)

        return translated if translated else text

    except Exception as e:
        print("Translate Error:", e)
        return text