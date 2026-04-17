from deep_translator import GoogleTranslator

def translate(text, target_lang):
    try:
        translated = GoogleTranslator(
            source="auto",   #  VERY IMPORTANT
            target=target_lang
        ).translate(text)

        if translated and translated.strip().lower() != text.strip().lower():
            return translated

        print("Translation same as input → forcing fallback")

        # fallback via English
        temp = GoogleTranslator(source="auto", target="en").translate(text)
        final = GoogleTranslator(source="en", target=target_lang).translate(temp)

        return final if final else text

    except Exception as e:
        print("Translate Error:", e)
        return text