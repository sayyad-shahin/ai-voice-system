from deep_translator import GoogleTranslator


def translate(text, source_lang, target_lang):
    try:
        #  Clean input
        text = text.strip()

        if not text:
            return ""

        #  If same language, skip translation
        if source_lang == target_lang:
            return text

        #  Translate
        translated = GoogleTranslator(
            source=source_lang,
            target=target_lang
        ).translate(text)

        #  Fallback safety
        if not translated or translated.strip() == "":
            return text

        return translated.strip()

    except Exception as e:
        print("Translate Error:", e)
        return text