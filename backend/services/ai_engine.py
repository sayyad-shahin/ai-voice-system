def improve(text):

    if not text:
        return text

    replacements = {
        "i want": "I would like",
        "give me": "Please provide",
        "tell me": "Could you tell me",
        "what is": "Can you explain"
    }

    text_lower = text.lower()

    for k, v in replacements.items():
        if k in text_lower:
            text = text.replace(k, v)

    return text.strip().capitalize()