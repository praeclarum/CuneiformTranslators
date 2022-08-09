import os, sys, math
import requests
import json
import shutil
import zipfile
from glob import glob
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from collections import defaultdict

import languages

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

def get_all_object_html_paths(oracc_dir):
    object_htmls = {os.path.basename(x).replace(".html",""): x for x in glob(f"{oracc_dir}/html/**/*.html", recursive=True)}
    return object_htmls

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
    def guess_corpus_file_lang(file):
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
            c, c_lang = guess_corpus_file_lang(cf)
            if c_lang is not None:
                corpi[c_id] = {"corpus": c, "lang": c_lang}
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
