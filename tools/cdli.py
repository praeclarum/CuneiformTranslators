import io
import requests
from tqdm import tqdm
import pandas as pd

class Publication():
    def __init__(self, id):
        self.id = id
        self.text_areas = list()
        self.language = None
    def __repr__(self):
        return f"Publication({repr(self.id)}, {repr(self.language)}, {repr(self.text_areas)})"
    def has_translations(self):
        return any(x.has_translations() for x in self.text_areas)
    
class TextArea():
    def __init__(self, name):
        self.name = name
        self.lines = list()
    def __repr__(self):
        return f"TextArea({repr(self.name)}, {repr(self.lines)})"
    def has_translations(self):
        return len(self.lines) > 0 and any(x.has_translations() for x in self.lines)
    
class TextLine():
    def __init__(self, number, text):
        self.number = number
        self.text = text
        self.languages = dict()
    def __repr__(self):
        return f"TextLine({repr(self.number)}, {repr(self.text)}, {repr(self.languages)})"
    def has_translations(self):
        for k in self.languages:
            v = self.languages[k]
            if len(v) > 0:
                return True
        return False
    
def parse_atf(atf):
    publications = []
    pub = None
    text = None
    tline = None
    all_langs = set()
    
    atf_lines = atf.split("\n")
#     for l in atf_lines[:50]:
#         print(l)

    for line in tqdm(atf_lines):
        line = line.replace("\t", " ").strip()
        if len(line) < 1:
            continue

        if line[0] == "&":
            pub = Publication(line[1:].split(" ", 1)[0])
            publications.append(pub)
        elif line[0] == "@":
            text = TextArea(line[1:])
            pub.text_areas.append(text)
        elif line[0].isdigit():
    #         print(line)
            parts = line.split(" ", 1)
            number, t = parts if len(parts) == 2 else (line, "")
            t = " ".join(t.strip().split(" "))
            tline = TextLine(number, t)
            text.lines.append(tline)
        elif len(line) > 4 and line.startswith("#atf: lang "):
            lang = line.split(" ")[-1].strip()
            all_langs.add(lang)
            pub.language = lang
        elif len(line) > 4 and line.startswith("#tr."):
            parts = line.split(":", 1)
            lang, t = parts if len(parts) == 2 else (line, "")
            lang = lang[4:].strip()
            if lang == "ts" and pub.language is not None:
                lang = pub.language + "ts"
            all_langs.add(lang)
            t = " ".join(t.strip().split(" "))
            tline.languages[lang] = t
        else:
    #         print("Unknown start:", line[0])
            pass

    return publications

def get_atf():
    atf_url = "https://github.com/cdli-gh/data/raw/master/cdliatf_unblocked.atf"
    atf = str(requests.get(atf_url).content, "utf8")
    return parse_atf(atf)

def get_catalog():
    cat_url = "https://github.com/cdli-gh/data/raw/master/cdli_cat.csv"
    cat_csv = str(requests.get(cat_url).content, "utf8")
    cat = pd.read_csv(io.StringIO(cat_csv))
    return cat
    

