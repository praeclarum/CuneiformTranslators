import io
import requests
import re
import pandas as pd

import languages

class Publication():
    def __init__(self, id, language=None, text_areas=None, genre=None, period=None, object_type=None, translation_source=None, src_url=None, src_link=None):
        self.id = id
        self.text_areas = list() if text_areas is None else text_areas
        self.language = language
        self.genre = genre
        self.period = period
        self.object_type = object_type
        self.translation_source = translation_source
        self.src_url = src_url
    def __repr__(self):
        return f"Publication({repr(self.id)}, {repr(self.language)}, {repr(self.text_areas)})"
    def has_translations(self):
        return any(x.has_translations() for x in self.text_areas)
    
class TextArea():
    def __init__(self, name, lines=None, paragraphs=None):
        self.name = name
        self.lines = list() if lines is None else lines
        self.paragraphs = list() if paragraphs is None else paragraphs
    def __repr__(self):
        return f"TextArea({repr(self.name)}, {repr(self.lines)}, {repr(self.paragraphs)})"
    def has_translations(self):
        return len(self.lines) > 0 and (any(x.has_translations() for x in self.lines) or any(x.has_translations() for x in self.paragraphs))
    def lines_to_paragraphs(self, src_lang, tgt_lang, max_length=128):
        self.paragraphs = list()
        plen = 0
        for iline, line in enumerate(self.lines):
            line_len = len(line.text)
            if languages.looks_like_li(line.text, src_lang):
                self.paragraphs.append(TextParagraph(iline, iline+1, "li"))
                plen = line_len
            else:
                if len(self.paragraphs) > 0 and self.paragraphs[-1].tag == "p" and plen + line_len < max_length:
                    p = self.paragraphs[-1]
                    p.end_line_index += 1
                    plen += line_len
                else:
                    self.paragraphs.append(TextParagraph(iline, iline+1))
                    plen = line_len
        if any(l for l in self.lines if tgt_lang in l.languages):
            for p in self.paragraphs:
                lines = self.lines[p.start_line_index:p.end_line_index]
                tlines = [(x.languages[tgt_lang] if tgt_lang in x.languages else "") for x in lines]
                p.languages[tgt_lang] = languages.remove_extraneous_space(" ".join(tlines))
        return self.paragraphs
    def paragraphs_to_lines(a, max_line_length=512):
        psrcs = list()
        for p in a.paragraphs:
            srcs = list()
            psrcs.append(srcs)
            end_line_index = p.end_line_index
            start_line_index = p.start_line_index
            src_lines = [x.text for x in a.lines[start_line_index:end_line_index]]
            src = " ".join(src_lines)
            while end_line_index > start_line_index + 1 and len(src) > max_line_length:
                end_line_index -= 1
                src_lines = [x.text for x in a.lines[start_line_index:end_line_index]]
                src = " ".join(src_lines)
            src = languages.remove_blanks(src)
            src = languages.underline_sign_names(src)
            src = languages.dashes_to_dots(src)                        
            src = languages.remove_extraneous_space(src)
            if len(src) > 0 and src not in srcs:
                src_len = len(src)
                if src_len > max_line_length:
                    max_line_length = src_len
                srcs.append((start_line_index, end_line_index, src))
        return psrcs

class TextLine():
    def __init__(self, number, text, languages=None):
        self.number = number
        self.text = text
        self.languages = dict() if languages is None else languages
    def __repr__(self):
        return f"TextLine({repr(self.number)}, {repr(self.text)}, {repr(self.languages)})"
    def has_translations(self):
        for k in self.languages:
            v = self.languages[k]
            if len(v) > 0:
                return True
        return False

class TextParagraph():
    def __init__(self, start_line_index, end_line_index, tag="p", languages=None):
        self.start_line_index = start_line_index
        self.end_line_index = end_line_index
        self.tag = tag
        self.languages = dict() if languages is None else languages
    def __repr__(self):
        return f"TextParagraph({repr(self.start_line_index)}, {repr(self.end_line_index)}, {repr(self.languages)})"
    def has_translations(self):
        for k in self.languages:
            v = self.languages[k]
            if len(v) > 0:
                return True
        return False
    
def text_area_to_json(a):
    return {
        "name": a.name,
        "lines": [text_line_to_json(a) for a in a.lines],
        "paragraphs": [text_paragraph_to_json(a) for a in a.paragraphs],
    }
def text_line_to_json(line):
    return {
        "number": line.number,
        "text": line.text,
        "languages": line.languages,
    }
def text_paragraph_to_json(para):
    return {
        "start_line_index": para.start_line_index,
        "end_line_index": para.end_line_index,
        "tag": para.tag,
        "languages": para.languages,
    }
def pub_to_json(pub):
    return {
        "id": pub.id,
        "language": pub.language,
        "text_areas": [text_area_to_json(a) for a in pub.text_areas],
        "genre": pub.genre,
        "period": pub.period,
        "object_type": pub.object_type,
        "src_url": pub.src_url,
    }

def json_to_pub(json):
    return Publication(
        json["id"],
        json["language"],
        [json_to_text_area(a) for a in json["text_areas"]],
        json["genre"] if "genre" in json else None,
        json["period"] if "period" in json else None,
        json["object_type"] if "object_type" in json else None,
        json["src_url"] if "src_url" in json else None,
    )
def json_to_text_area(json):
    return TextArea(
        json["name"],
        [json_to_text_line(a) for a in json["lines"]],
        [json_to_text_paragraph(a) for a in json["paragraphs"]],
    )
def json_to_text_line(json):
    return TextLine(
        json["number"],
        json["text"],
        json["languages"],
    )
def json_to_text_paragraph(json):
    return TextParagraph(
        json["start_line_index"],
        json["end_line_index"],
        json["tag"],
        json["languages"],
    )
    
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
        id_text = int(pid[1:])
        meta = cat[cat["id_text"]==id_text]
        if len(meta) != 1:
            continue
        pub.id = pid
        pub.genre = str(meta["genre"].values[0])    
        pub.object_type = str(meta["object_type"].values[0])
        pub.material = str(meta["material"].values[0])
        pub.period = str(meta["period"].values[0])
        pub.provenience = str(meta["provenience"].values[0])
        pub.collection = str(meta["collection"].values[0])
        pub.translation_source = str(meta["translation_source"].values[0])
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
    if x is None:
        return "other-object"
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
    if x is None:
        return "other-genre"
    g = str(x).lower().replace("?","").replace("(see subgenre)","").replace("(modern)", "").replace("(seal)", "").replace("/", "-").strip()
    if g == "other":
        return "other-genre"
    if g in genres:
        return g
    return "other-genre"

def get_genres(gs):
    if gs is None:
        return set()
    return {get_genre(y) for x in gs.split(";") for y in x.split(",")}



def get_years(raw_periods):
    if raw_periods is None:
        return []
    years = []
    matches = re.findall(r"(\d+)\s*(BC|AD)?\s*([-–]\s*(\d+)\s*(BC|AD))?", raw_periods)
    for syear, sera, end, eyear, eera in matches:
        if len(sera) == 0:
            sera = eera
        if len(sera) > 0:
            year = (int(syear), sera, int(eyear) if len(eyear)>0 else 0, eera)
            if year == (1200, 'BC', 700, 'BC'):
                year = (1150, 'BC', 730, 'BC')
            years.append(year)
    return years

# print(get_years("Uruk III (ca. 3200- 3000 BC) - Early Dynastic I-II (ca. 2900-2700 BC)"))
# print(get_years("Parthian (247 BC- 224 AD)"))
# print(get_years("Achaemenid (547–331 BC)"))
# print(get_years("Linear Elamite (ca. 2200 BC)"))

periods = [
    ((8500, 'BC', 3500, 'BC'), 'Pre-Uruk V', 'pre-uruk-v'),
    ((3500, 'BC', 3350, 'BC'), 'Uruk V', 'uruk-v'),
    ((3350, 'BC', 3200, 'BC'), 'Uruk IV', 'uruk-iv'),
    ((3300, 'BC', 3000, 'BC'), 'Egyptian 0', 'egyptian-0'),
    ((3200, 'BC', 3000, 'BC'), 'Uruk III', 'uruk-iii'),
    ((3100, 'BC', 2900, 'BC'), 'Proto-Elamite', 'proto-elamite'),
    ((2900, 'BC', 2700, 'BC'), 'ED I-II', 'ed-i-ii'),
    ((2700, 'BC', 2500, 'BC'), 'Early Dynastic IIIA', 'early-dynastic-iiia'),
    ((2600, 'BC', 2500, 'BC'), 'ED IIIa', 'ed-iiia'),
    ((2500, 'BC', 2340, 'BC'), 'ED IIIb', 'ed-iiib'),
    ((2350, 'BC', 2250, 'BC'), 'Ebla', 'ebla'),
    ((2340, 'BC', 2200, 'BC'), 'Old Akkadian', 'old-akkadian'),
    ((2200, 'BC', 0, ''), 'Linear Elamite', 'linear-elamite'),
    ((2200, 'BC', 2100, 'BC'), 'Lagash II', 'lagash-ii'),
    ((2700, 'BC', 1500, 'BC'), 'Old Elamite', 'old-elamite'),
    ((2200, 'BC', 1900, 'BC'), 'Harappan', 'harappan'),
    ((2100, 'BC', 2000, 'BC'), 'Ur III', 'ur-iii'),
    ((2000, 'BC', 1900, 'BC'), 'Early Old Babylonian', 'early-old-babylonian'),
    ((1950, 'BC', 1850, 'BC'), 'Old Assyrian', 'old-assyrian'),
    ((1900, 'BC', 1600, 'BC'), 'Old Babylonian', 'old-babylonian'),
    ((1500, 'BC', 1100, 'BC'), 'Middle Hittite', 'middle-hittite'),
    ((1400, 'BC', 1100, 'BC'), 'Middle Babylonian', 'middle-babylonian'),
    ((1400, 'BC', 1000, 'BC'), 'Middle Assyrian', 'middle-assyrian'),
    ((1300, 'BC', 1000, 'BC'), 'Middle Elamite', 'middle-elamite'),
    ((1150, 'BC', 730, 'BC'), 'Early Neo-Babylonian', 'early-neo-babylonian'),
    ((911, 'BC', 612, 'BC'), 'Neo-Assyrian', 'neo-assyrian'),
    ((770, 'BC', 539, 'BC'), 'Neo-Elamite', 'neo-elamite'),
    ((626, 'BC', 539, 'BC'), 'Neo-Babylonian', 'neo-babylonian'),
    ((547, 'BC', 331, 'BC'), 'Achaemenid', 'achaemenid'),
    ((323, 'BC', 63, 'BC'), 'Hellenistic', 'hellenistic'),
    ((247, 'BC', 224, 'AD'), 'Parthian', 'parthian'),
    ((224, 'AD', 641, 'AD'), 'Sassanian', 'sassanian'),
    ((3000, 'AD', 0, ''), 'Other', 'other-period'),
    ((9999, 'AD', 0, ''), 'Fake', 'fake'),
]
def get_period_sort_value(period):
    x, _, _ = period
    s = (-x[0] if x[1]=="BC" else x[0])
    if x[2] == 0:
        return s
    e = (-x[2] if x[3]=="BC" else x[2])
    return (s+e)/2

periods = sorted(periods, key=get_period_sort_value)
# for p in periods:
#     print(f"    ({repr(p)},")
#     print(f"    ({repr(p[0])}, {repr(p[1])}, {repr(slugify(p[1]))}),")

period_from_year = {x[0]: x[1] for x in periods}
year_from_period = {x[1]: x[0] for x in periods}
period_slug_from_period = {x[1]: x[2] for x in periods}
period_from_period_slug = {x[2]: x[1] for x in periods}

def get_period_from_year(year):
    if year in period_from_year:
        return period_from_year[year]
    return "Other"

def sanitize_period(y):
    p = y.replace("?", "").replace("(modern)","").replace("fake (ancient)", "Fake").strip()
    if p == "modern" or p == "fake" or p == "copy":
        p = "Fake"
    elif p == "uncertain" or p == "nan":
        p = "Other"
    return p

def get_periods(raw_periods):
    if raw_periods is None:
        return ["Other"]
    years = get_years(raw_periods)
    if len(years) == 0:
        periods = [sanitize_period(y) for z in raw_periods.split(" or ") for y in z.split(";")]
        periods = [p for p in periods if p in year_from_period]
        if len(periods) == 0:
            print("No periods for:", raw_periods)
        return periods
    else:
        return [get_period_from_year(x) for x in years]


def wrap_paragraph(paragraph, lines, src_lang, wmax_num_tokens, tgt_lang, avg_src_chars_per_token = 1.8713256996006793, avg_tgt_chars_per_token = 2.577806274115267):
    ptag, pline_start_index, pline_end_index = paragraph
    wline_ranges = []
    wline_tok_len = 0.0
    
    def start_new_line(pline_index):
#         print("start", pline_index)
        wline_ranges.append((pline_index, pline_index + 1))
        
    def append_line(pline_index):
#         print("append", pline_index)
        r = wline_ranges[-1]
        if r[1] == pline_index:
            wline_ranges[-1] = (r[0], r[1] + 1)
        else:
            print(f"Missing line: got {pline_index}, expected {r[1]}: {wline_ranges}")

    for pline_index in range(pline_start_index, pline_end_index):
        pline_num_toks = len(lines[pline_index].text) / avg_src_chars_per_token + 1.0
        if len(wline_ranges) == 0 or (wline_tok_len + pline_num_toks > wmax_num_tokens):
            start_new_line(pline_index)
            wline_tok_len = 0.0
        else:
            append_line(pline_index)
        wline_tok_len += pline_num_toks
    return wline_ranges

def print_pub_paragraphs(pub, tgt_len="en"):
    for a in pub.text_areas:
        print(pub.id, a.name)
        for p in a.paragraphs:
            lines = a.lines[p.start_line_index:p.end_line_index]
            cuneiform = " ".join(x.text for x in lines)
            tgt = p.languages[tgt_len]
            print("   >>>>", cuneiform)
            print("   <<<<", tgt)
        print("")
        
def print_pub_lines(pub, tgt_len="en"):
    for a in pub.text_areas:
        print(pub.id, a.name)
        for line in a.lines:
            print(line.text)
        print("")
        
def text_area_is_translated(pub, text_area, tgt_lang):
    for line in text_area.lines:
        if tgt_lang in line.languages:
            return True
    return False

def pub_is_translated(pub, tgt_lang):
    return any(x for x in pub.text_areas if text_area_is_translated(pub, x, tgt_lang))
