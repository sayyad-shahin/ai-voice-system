def improve(text):

    replacements = {
        "i want": "I would like",
        "give me": "Please provide",
        "tell me": "Could you tell me",
        "what is": "Can you explain"
    }

    text = text.lower()

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text.capitalize()