import json
import requests
import re

old_languages = {
    "akk": "Akkadian",
    "sux": "Sumerian",
    "qpn": "Proper Nouns",
    "arc": "Aramaic",
    "elx": "Elamite",
    "grc": "Greek",
    "peo": "Old Persian",
    "ug": "Ugaritic",
    "xur": "Urartian",
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

unicode_en_to_ascii_en_replacements = [
    ("ā", "a"),
    ("Ā", "a"),
    ("ŋ", "g"),
    ("Ŋ", "G"),
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

unicode_atf_to_ascii_atf_replacements = [
    ("⸢", ""),
    ("⸣", "#"),
    ("ʾ", "'"),
    ("ŋ", "g"),
    ("Ŋ", "G"),
    ("ḫ", "h"),
    ("Ḫ", "H"),
    ("š", "sz"),
    ("Š", "SZ"),
    ("ṣ", "s,"),
    ("Ṣ", "S,"),
    ("ś" ,"s'"),
    ("Ś", "S'"),
    ("ṭ", "t,"),
    ("Ṭ", "T,"),
    ("ₓ", "x2"),
    ("ₓ", "X2"),
    ("₀", "0"),
    ("₁", "1"),
    ("₂", "2"),
    ("₃", "3"),
    ("₄", "4"),
    ("₅", "5"),
    ("₆", "6"),
    ("₇", "7"),
    ("₈", "8"),
    ("₉", "9"),
]

unicode_atf_to_ascii_atf_token_replacements = {
    "bán": "ban2",
    "buru": "bur'u",
    "èše": "esze3",
    "géš": "gesz2",
    "šár": "szar2",
    "bùr": "bur3",
    "GÁN": "GAN2",
    "sá": "sa2",
    "sìla": "sila3",
    "lú": "lu2",
    "gur₇": "guru7",
    "taka₄": "tak4",
    "líd": "lid2",
    "zíd": "zi3",
    "teŋ₄": "ti",
    "šaru": "szar'u",
    "úš": "us2",
    "kùš": "kusz3",
    "kug": "ku3",
    "sig₁₀": "si3",
    "zid₂": "zi3",
    "gud": "gu4",
    "bí": "bi2",
    "dug₄": "du11",
    "diŋir": "dingir",
    "àm": "am3",
    "íb": "ib2",
    "íl": "il2",
    "su₁₃": "su3",
    "GIR₃": "GIRI3",
    "ŋiri₂": "gir2",
    "IR₃": "ARAD2",
    "ti₇": "te",
    "giggi": "kukku5",
    "sag₁₀": "saga",
    "gurum": "gur2",
    "aḫ₃": "had2",
    "tu₄": "tum",
    "gab₂": "kab",
    "zid": "zi",
    "tum₁₂": "tu",
    "GEME₂": "dam",
    "šag₄": "sza3",
    "kud": "ku5",
#     "bu": "pu",
#     "pu": "bu",
}

cdli_inconsistencies = {
    "sumun2": "sun2",
}

blank_string = [
    "(blank)",
    "($ blank $)",
    "($ blank space $)",
    "( space )",
]

li_start_re = re.compile(r"^\[?_?\d+(/\d+)?\((asz|ban2|barig|disz|gesz2|iku|u)\)\]?")

underline_sign_names_re = re.compile(r"\b([A-Z][A-Z0-9#\. &]*[A-Z0-9#])")

def replace_unsupported_en(text):
    r = text
    for s, t in unicode_en_to_ascii_en_replacements:
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

def underline_sign_names_repl(match):
    return '_' + match.group(1).lower() + '_'
    
def underline_sign_names(text):
#     return text
    return underline_sign_names_re.sub(underline_sign_names_repl, text).replace(".", "-")

def remove_extraneous_space(s):
    return " ".join(x for x in s.split(" ") if len(x) > 0)

def remove_blanks(s):
    for b in blank_string:
        s = s.replace(b, "")
    return s

def dashes_to_dots(s):
    return s.replace("[---]", "[...]").replace("[---", "[...").replace("---]", "...]").replace("---", "...")

def target_ok(target_text):
    if len(target_text) == 0:
        return False
    if len(set(target_text.replace(" ", ""))) < 2:
        return False
    return True

def looks_like_li(line, lang):
    return li_start_re.match(line)

def unicode_words_to_normalized_ascii(tokens):
    def proc_token(token):
        if token in unicode_atf_to_ascii_atf_token_replacements:
            return unicode_atf_to_ascii_atf_token_replacements[token]
        for s, t in unicode_atf_to_ascii_atf_replacements:
            token = token.replace(s, t)
        return token
    retokenized = "".join(proc_token(x) for x in tokens)
    underlined = underline_sign_names(retokenized).strip()
    return underlined
