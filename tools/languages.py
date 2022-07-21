old_languages = {
    "akk": "Akkadian",
    "sux": "Sumerian",
    "qpn": "Proper Nouns",
    "arc": "Aramaic",
    "elx": "Elamite",
    "grc": "Greek",
    "peo": "Old Persian",
    "ug": "Ugaritic",
}
transliterated_languages = {
    "akkts": "Akkadian",
    "suxts": "Sumerian",
    "qpnts": "Proper Nouns",
    "arcts": "Aramaic",
    "elxts": "Elamite",
    "grcts": "Greek",
    "peots": "Old Persian",
    "ugts": "Ugaritic",
}
modern_languages = {
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian"
}
ml_languages = {
    "ml_de": "German",
    "ml_en": "English",
    "ml_es": "Spanish",
    "ml_fr": "French",
    "ml_it": "Italian"
}

all_languages = {**old_languages, **transliterated_languages, **modern_languages, **ml_languages}

language_codes = set(list(all_languages.keys()))
