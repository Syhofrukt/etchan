from langdetect import detect

LANG_MAP = {
    "en": "english",
    "ru": "russian",
    "de": "german",
    "fr": "french",
    "es": "spanish",
    "pt": "portuguese"
}

def lang_detect(text: str):
    try:
        lang = detect(text)
    except Exception:
        return "simple"

    return LANG_MAP.get(lang, "simple")
