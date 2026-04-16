from deep_translator import GoogleTranslator

def translate(text, target_lang):
    try:
        # Always auto-detect (more reliable than langdetect)
        translated = GoogleTranslator(
            source='auto',
            target=target_lang
        ).translate(text)

        print("Translated:", translated)

        return translated

    except Exception as e:
        print("Translation Error:", str(e))
        return text