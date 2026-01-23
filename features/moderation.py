import re

BAD_WORDS = {"shit", "fuck"}

def bad_word(text: str) -> bool:
    text = text.lower()
    return any(
        re.search(rf"\b{word}\b", text)
        for word in BAD_WORDS
    )