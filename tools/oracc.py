import os, sys, math
import requests
import json
import shutil
import zipfile
from glob import glob
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from collections import defaultdict
from bs4 import BeautifulSoup

import languages
import cdli

session = requests.Session()

def get_project_ids():
    return session.get("http://oracc.museum.upenn.edu/projects.json").json()["public"]

CHUNK_SIZE = 16 * 1024

ignore_project_ids = {'contrib/amarna', 'rinap/rinap5p1', 'cdli', 'cams/tlab', 'cams', 'arrim', 'cams/akno', 'cams/etana', 'cams/barutu', 'amgg', 'lovelyrics', 'ctij', 'lacost', 'contrib', 'cams/selbi', 'cams/ludlul', 'contrib/lambert', 'akklove', 'cams/anzu', 'pnao', 'rimanum'}

def get_project_zip_path(project_id, oracc_dir):
    project_zip_name = project_id.replace('/', '-') + ".zip"
    ofile = f"{oracc_dir}/{project_zip_name}"
    return ofile

def download_project_zip(project_id, oracc_dir, verbose=True):
    
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    project_zip_name = project_id.replace('/', '-') + ".zip"
    url = "http://build-oracc.museum.upenn.edu/json/" + project_zip_name
    if verbose:
        print(url)
    tmp_dir = f"{oracc_dir}/tmp"
    ofile = get_project_zip_path(project_id, oracc_dir)
    if os.path.exists(ofile):
        return ofile
    os.makedirs(tmp_dir, exist_ok=True)
    tfile = f"{tmp_dir}/{project_zip_name}"
    response = session.get(url, verify=False)
    new_ignores = set()
    if response.status_code == 200:
        if verbose:
            print("Downloading " + url)
        with open(tfile, 'wb') as f:
            for c in response.iter_content(chunk_size=CHUNK_SIZE):
                f.write(c)
        shutil.move(tfile, ofile)
        return ofile
    else:
        print(url + " does not exist.")
        return None
    
def get_all_project_zips(oracc_dir, verbose=False, tqdm=lambda x: x):
    project_ids = get_project_ids()
    paths = []
    new_ignores = set()
    for p in tqdm(project_ids):
        if p in ignore_project_ids:
            continue
        path = download_project_zip(p, oracc_dir, verbose=verbose)
        if path is not None:
            paths.append(path)
        else:
            new_ignores.add(p)
    tmp_dir = f"{oracc_dir}/tmp"
    if os.path.exists(tmp_dir):
        os.rmdir(tmp_dir)
    if len(new_ignores) > 0:
        print("ignore_project_ids =", repr(new_ignores))
    return paths

def get_project_translated_object_ids(project_zip_path):
    project_id = os.path.basename(project_zip_path).replace(".zip", "").replace("-", "/")
    result = []
    project_zip = zipfile.ZipFile(project_zip_path, "r")
#     for f in project_zip.filelist:
#         print(f)
    metas = [x for x in project_zip.filelist if x.filename.endswith("metadata.json")]
    if len(metas) != 1:
        return result
    with project_zip.open(metas[0], "r") as f:
        meta = json.load(f)
    formats = meta["formats"]
    if "tr-en" not in formats:
        return result
    result = [(project_id, x) for x in formats["tr-en"]]
    return result

def get_all_translated_object_ids(project_zips, tqdm=lambda x: x):
    all_translated_ids = []
    for p in tqdm(project_zips):
        all_translated_ids.extend(get_project_translated_object_ids(p))
    return sorted(list(set(all_translated_ids)))

def get_project_corpus_object_ids(project_zip_path):
#     print(project_zip_path)
    project_id = os.path.basename(project_zip_path).replace(".zip", "").replace("-", "/")
    project_zip = zipfile.ZipFile(project_zip_path, "r")
    result = [(project_id, x.filename.split("/")[-1].replace(".json", "")) for x in project_zip.filelist if "/corpusjson/" in x.filename and x.filename.endswith(".json")]
#     print(result)
    return result

def get_all_corpus_object_ids(project_zips, tqdm=lambda x: x):
    all_corpus_ids = []
    for p in tqdm(project_zips):
        all_corpus_ids.extend(get_project_corpus_object_ids(p))
    return sorted(list(set(all_corpus_ids)))

def load_project_corpus(project_id, oracc_dir):
    project_zip_path = get_project_zip_path(project_id, oracc_dir)
    result = dict()
    project_zip = zipfile.ZipFile(project_zip_path, "r")
#     for f in project_zip.filelist:
#         print(f)
    corpi = [x for x in project_zip.filelist if "/corpusjson/" in x.filename and x.filename.endswith(".json")]
    if len(corpi) == 0:
        return result
    for corpus_file_info in corpi:
#         print(corpus_file_info)
        with project_zip.open(corpus_file_info, "r") as f:
            corpus = json.load(f)
#         print(corpus.keys())
        result[corpus_file_info.filename] = corpus
    return result

def download_object_translation(oracc_dir, project_id, object_id):
    url = f"http://oracc.iaas.upenn.edu/{project_id}/{object_id}/html"
    odir = f"{oracc_dir}/html/{object_id[:2]}"
    out_path = f"{odir}/{object_id}.html"
    if os.path.exists(out_path):
        return out_path
    os.makedirs(odir, exist_ok=True)
    html_text = session.get(url).text
    with open(out_path, "wt") as f:
        f.write(html_text)
    return out_path

all_object_html_paths = dict()

def get_all_object_html_paths(oracc_dir):
    global all_object_html_paths
    if len(all_object_html_paths) == 0:
        all_object_html_paths = {os.path.basename(x).replace(".html",""): x for x in glob(f"{oracc_dir}/html/**/*.html", recursive=True)}
    return all_object_html_paths

old_langs = {languages.all_languages[k]: k for k in languages.old_languages}
    
def load_project_pub_ids(project_id, oracc_dir):
    project_zip_path = get_project_zip_path(project_id, oracc_dir)
    result = set()
    corpi = dict()
    if not os.path.exists(project_zip_path):
        return result, corpi
    project_zip = zipfile.ZipFile(project_zip_path, "r")
    
    catalogs = [x for x in project_zip.filelist if x.filename.endswith("catalogue.json")]
    if len(catalogs) != 1:
        return result, corpi
    with project_zip.open(catalogs[0], "r") as f:
        catalog = json.load(f)
    if "members" not in catalog:
        return result, corpi
    members = catalog["members"]
    result = set((x, old_langs[members[x]["language"]]) for x in members.keys() if "language" in members[x] and members[x]["language"] in old_langs)
    
    corpus_files = [x for x in project_zip.filelist if "/corpusjson/" in x.filename and x.filename.endswith(".json")]
    def find_corpus_langs(o, langs):
        if isinstance(o, dict):
            if "lang" in o:
                lang = o["lang"].split("-")[0]
                langs[lang] += 1
            elif "exolng" in o:
                lang = o["exolng"].split("-")[0]
                langs[lang] += 1
            else:
                for v in o.values():
                    find_corpus_langs(v, langs)
        elif isinstance(o, list):
            for v in o:
                find_corpus_langs(v, langs)
    def read_corpus(file):
        langs = defaultdict(lambda: 0)
        with project_zip.open(file, "r") as f:
            corpus = json.load(f)
            find_corpus_langs(corpus, langs)
#         langs = sorted([(x, langs[x]) for x in langs.keys()], key=lambda y:-y[1])
#         print(langs)
        lang = "akk" if "akk" in langs else ("sux" if "sux" in langs else None)
        if lang is None:
            if len(langs) > 0:
#                 print(langs)
                pass
            else:
#                 print("No langs", project_zip_path, file.filename)
                pass
        return corpus, lang
      
    for cf in corpus_files:
        try:
            c_id = cf.filename.split("/")[-1].replace(".json", "")
            if c_id not in members:
                # print(f"Corpus {c_id} not in members")
                # print("catalogs", catalogs)
                # print("members", members)
                catalog_info = {}
            else:
                catalog_info = members[c_id]
            cat_lang = old_langs[catalog_info["language"]] if "language" in catalog_info and catalog_info["language"] in old_langs else None
            # print(c_id, cat_lang)
            c, guess_lang = read_corpus(cf)
            c_lang = cat_lang if cat_lang is None else guess_lang
            if c_lang is not None:
                corpi[c_id] = {"corpus": c, "lang": c_lang, "catalog_info": catalog_info}
                result.add((c_id, c_lang))
        except json.decoder.JSONDecodeError:
            print("Error:", sys.exc_info())
    return result, corpi

def load_all_project_pub_ids(oracc_dir, tqdm=lambda x: x):
    project_ids = get_project_ids()
    pub_ids = set()
    corpi = dict()
    for pid in tqdm(project_ids):
        ppub_ids, pcorpi = load_project_pub_ids(pid, oracc_dir)
        pub_ids = pub_ids.union(ppub_ids)
        for k in pcorpi.keys():
            corpi[k] = pcorpi[k]
    pub_ids = sorted(list(set(pub_ids)))
    return pub_ids, corpi

def load_html(path):
    with open(path, "rt") as f:
        return BeautifulSoup(f.read(), features="html.parser")
    
def load_html_for_object_id(object_id, oracc_dir):
    return load_html(get_all_object_html_paths(oracc_dir)[object_id])

def get_object_id_pub(object_id, corpus, catalog_info, lang, oracc_dir):
    pub = cdli.Publication(object_id)
    pub.language = lang

    project_id = corpus["project"]
    pub.src_url = f"http://oracc.museum.upenn.edu/{project_id}/{object_id}"

    # print("CAT", repr(catalog_info))
    pub.genre = catalog_info["genre"] if "genre" in catalog_info else None
    pub.period = catalog_info["period"] if "period" in catalog_info else None
    pub.object_type = catalog_info["object_type"] if "object_type" in catalog_info else None
    pub.translation_source = catalog_info["author"] if "author" in catalog_info else None

    # print(cdli.pub_to_json(pub))
    
    surface = ""
    column = ""
    text_area = None
    def add_line(number, cuneiform):
        nonlocal surface, column, text_area, pub
        if text_area is None:
            name = surface
            if len(column) > 0:
                if len(name) > 0:
                    name += " " + column
                else:
                    name = column
            text_area = cdli.TextArea(name=name)
            pub.text_areas.append(text_area)
        line = cdli.TextLine(number=number, text=cuneiform)
        text_area.lines.append(line)

    html = load_html_for_object_id(object_id, oracc_dir)
    texts = html.find_all("div", class_="text")

    for text in texts:
        surface = ""
        column = ""
        text_area = None
        line_index = 0
        table = text.find("table", class_="transliteration")
        if table is None:
            continue
        text_title = text.find("h1").text
        rows = table.find_all("tr")
        for r in rows:
            cols = r.find_all("td")
            rclasses = r["class"] if r.has_attr("class") else []
            if "h" in rclasses:
                htext = cols[0].text.strip()
                if "surface" in rclasses:
                    surface = htext
                    column = ""
                elif "column" in rclasses:
                    column = htext
                text_area = None
                line_index = 0
#                 print("")
#                 print(object_id, text_title, surface, column)
            else:
                lnums = [x for x in cols if x.has_attr("class") and "lnum" in x["class"]]
                if len(lnums) != 1:
                    continue
                lnum = lnums[0].text.strip() if len(lnums) > 0 else ""                
                tlits = [x for x in cols if x.has_attr("class") and "tlit" in x["class"]]
                ntlits = len(tlits)
                cs = [x for x in cols if x.has_attr("class") and "c" in x["class"]]
                xtrs = [x for x in cols if x.has_attr("class") and "xtr" in x["class"]]
                if ntlits == 1:
                    tlit = tlit_to_normalized_ascii(tlits[0])
                    add_line(lnum, tlit)
                    xtr = ""
                    rowspan = 1
                    if len(xtrs) > 0:
                        if xtrs[0].has_attr("rowspan"):
                            rowspan = int(xtrs[0]["rowspan"])
                        xtr = xtr_to_en(xtrs[0])
                        para = cdli.TextParagraph(line_index, line_index + rowspan)
                        para.languages["en"] = xtr
                        text_area.paragraphs.append(para)
                    line_index += 1
                elif len(cs) > 0 and len(cs) == len(xtrs):
                    for i, c in enumerate(cs):
                        tlit = tlit_to_normalized_ascii(c)
                        add_line(lnum + f".{i}", tlit)
                        xtr = xtr_to_en(xtrs[i])
                        para = cdli.TextParagraph(line_index, line_index + 1)
                        para.languages["en"] = xtr
                        text_area.paragraphs.append(para)
                        line_index += 1
                elif ntlits == 0:
                    pass
                else:
                    raise ValueError("Unsupported format: ntlits=", len(tlits))
#                 print(line_index, lnum, "\t", tlit, "\t", rowspan, "\t", xtr)
                
#                 print("row", r["class"], "with", len(cols), "cols", [(x["class"] if x.has_attr("class") else []) for x in cols])
#         print("")
    return pub

def xtr_to_en(xtr):
    ptr = xtr.find("p", class_="tr")
    if ptr is None:
        return ""
    cell = ptr.find("span", class_="cell")
    if cell is not None:
        ptr = cell
    return ptr.text.strip()
            
tlit_ignore_classes = set(["marker"])

def is_node_sign(node):
    if isinstance(node, str):
        return node == "."
    return node.name=="sup" or (node.has_attr("class") and "sign" in node["class"])

def tlit_to_normalized_ascii(tlit):
    def node_to_str(node, in_sign):
        if isinstance(node, str):
            return [node]
        children_in_sign = False
        ignore = False
        classes = node["class"] if node.has_attr("class") else []
        for c in classes:
            ignore = ignore or (c in tlit_ignore_classes)
        if ignore:
            return []
        parts = []
        is_sup = node.name == "sup"
        is_sign = all(is_node_sign(x) for x in node)
        if is_sup:
            parts.append("{")
            if "sux" in node["class"] and node.text == "m":
                parts.append("disz")
                parts.append("}")
                return parts
        if is_sign and not in_sign:
#             parts.append("_")
            children_in_sign = True
        for c in node:
            parts.extend(node_to_str(c, in_sign=in_sign or children_in_sign))
#         if is_sign and not in_sign:
#             parts.append("_")
        if is_sup:
            parts.append("}")
        return parts
    tokens = node_to_str(tlit, in_sign=False)
    return languages.unicode_words_to_normalized_ascii(tokens)

