import random

def improve(text):

    responses = [
        "Here is the information you requested:",
        "Let me help you with that.",
        "Here is the answer:",
        "Sure, I can help."
    ]

    prefix = random.choice(responses)

    return prefix + " " + text.capitalize()