import json
import requests

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

replacements = [
    ("ā", "a"),
    ("Ā", "a"),
    ("ḫ", "h"),
    ("Ḫ", "H"),
    ("ī", "i"),
    ("Ī", "I"),
#     ("î", "i"),
#     ("Î", "I"),
    ("ř", "r"),
    ("Ř", "R"),
    ("šš", "sh"),
    ("š", "sh"),
    ("Š", "Sh"),
    ("ṣ", "sh"),
    ("Ṣ", "Sh"),
    ("ṭ", "t"),
    ("Ṭ", "T"),
    ("ū", "u"),
    ("Ū", "U"),
]

def replace_unsupported(text):
    r = text
    for s, t in replacements:
        r = r.replace(s, t)
    return r

cuneiform_unicode = json.loads(requests.get("https://github.com/darth-cheney/cuneiform-signs-unicode/raw/master/cuneiform-unicode.json").text)["signs"]

cuneiform_unicode_replacements = { x["value"].lower(): x["character"] for x in cuneiform_unicode }

def split_cuneiform_word(word):
    parts = [""]
    for c in word:
        if c == "{" or c == "}":
            parts.append(c)
            parts.append("")
        elif c == "-" or c == "#" or c == "_":
            parts.append("")
        else:
            parts[-1] = parts[-1] + c
    return [p for p in parts if len(p) > 0]

def cuneiform_text_to_unicode(atf_text, language):
    words = atf_text.split(" ")
    for i, word in enumerate(words):
        lemmas = split_cuneiform_word(word)
        for j, lemma in enumerate(lemmas):
            lemma = lemma.lower()
            if lemma in cuneiform_unicode_replacements:
                lemmas[j] = cuneiform_unicode_replacements[lemma]
        words[i] = "".join(lemmas)
    return " ".join(words)
