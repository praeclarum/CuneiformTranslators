import io
import requests
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

    for line in atf_lines:
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
    print(f"Downloading {atf_url}")
    atf = str(requests.get(atf_url).content, "utf8")
    print("Parsing atf")
    return parse_atf(atf)

def get_catalog():
    cat_url = "https://github.com/cdli-gh/data/raw/master/cdli_cat.csv"
    print(f"Downloading {cat_url}")
    cat_csv = str(requests.get(cat_url).content, "utf8")
    cat = pd.read_csv(io.StringIO(cat_csv))
    return cat

def merge_atf_with_catalog(atf, cat, tqdm=lambda x: x):
    output_pubs = []
    for pub in tqdm(atf):
        pid = pub.id
        if len(pid) < 3 or pid[0] != "P":
            continue
        if pid[-1] == "=":
            pid = pid[:-1]
        pid = int(pid[1:])
        meta = cat[cat["id_text"]==pid]
        if len(meta) != 1:
            continue
        pub.id = pid
        pub.genre = str(meta["genre"].values[0])    
        pub.object_type = str(meta["object_type"].values[0])
        pub.material = str(meta["material"].values[0])
        pub.period = str(meta["period"].values[0])
        pub.provenience = str(meta["provenience"].values[0])
        pub.collection = str(meta["collection"].values[0])
        output_pubs.append(pub)
    output_pubs.sort(key=lambda a: a.id)
    return output_pubs

object_types = {
    'brick',
    'barrel',
    'cylinder',
    'cone',
    'tablet',
    'seal',
    'bulla',
    'vessel',
    'lentil',
    'envelope',
    'block',
    'prism',
    'vase',
    'docket',
    'sealing',
    'tag'
}

def sanitize_object_type(x):
    return str(x).lower().replace(" (see object remarks)","").replace(" (not impression)", "").replace(" & envelope", "").replace(" in envelope", "").replace("prismatic cylinder", "prism").strip()

def get_object_type(x):
    x = sanitize_object_type(x)
    if x == "other":
        return "other-object"
    if x in object_types:
        return x
    return "other-object"
    
genres = {
    'administrative',
    'ritual',
    'omens',
    'astronomical',
    'school',
    'prayer-incantation',
    'administative',
    'lexical',
    'pottery',
    'letter',
    'royal-votive',
    'uncertain',
    'mathematical',
    'scientific',
    'literary',
    'legal',
    'astronomical, omen',
    'votive',
    'medical',
    'historical',
    'fake',
    'royal-monumental',
    'administrative record',
    'omen',
    'private-votive'
}

def get_genre(x):
    g = str(x).lower().replace("?","").replace("(see subgenre)","").replace("(modern)", "").replace("(seal)", "").replace("/", "-").strip()
    if g == "other":
        return "other-genre"
    if g in genres:
        return g
    return "other-genre"

def get_genres(gs):
    return {get_genre(y) for x in gs.split(";") for y in x.split(",")}




