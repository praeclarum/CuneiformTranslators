import sys, os, datetime
import json
import zipfile
from tqdm import tqdm
from collections import defaultdict

import cdli
import oracc

class Corpus:
    def __init__(self, id):
        self.id = id
    def get_pubs(self):
        raise NotImplementedError
    def init_pubs(self):
        for pub in self.get_pubs():
            pub.corpus = self.id
    def get_pubs_with_lang(self, src_lang):
        transliterated_cdli_index = {x.id: x for x in self.get_pubs() if x.language == src_lang}
        return transliterated_cdli_index

class CDLI(Corpus):
    def __init__(self, tqdm=tqdm):
        super().__init__("cdli")
        zip_path = "../data/cdli_pubs.zip"
        if os.path.exists(zip_path):
            with open(zip_path, "rb") as f:
                with zipfile.ZipFile(f) as zf:
                    json_name = [x for x in zf.namelist() if x.endswith(".json")][0]
                    pubs_json = json.load(zf.open(json_name, "r"))
                    self.cdli_pubs = {p["id"]: cdli.json_to_pub(p) for p in pubs_json.values()}
                    self.init_pubs()
                    return
        cat = cdli.get_catalog()
        atf_pubs = cdli.get_atf()
        self.cdli_pubs = {p.id: p for p in cdli.merge_atf_with_catalog(atf_pubs, cat, tqdm)}
        with open(zip_path, "wb") as f:
            with zipfile.ZipFile(f, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                json_str = json.dumps({p.id: cdli.pub_to_json(p) for p in self.cdli_pubs.values()})
                zf.writestr("oracc_pubs.json", bytes(json_str, "utf-8"))
        self.init_pubs()
    def get_pubs(self):
        return self.cdli_pubs.values()
    
class ORACC(Corpus):
    def __init__(self, oracc_dir, tqdm=tqdm):
        super().__init__("oracc")
        zip_path = "../data/oracc_pubs.zip"
        if os.path.exists(zip_path):
            with open(zip_path, "rb") as f:
                with zipfile.ZipFile(f) as zf:
                    json_name = [x for x in zf.namelist() if x.endswith(".json")][0]
                    pubs_json = json.load(zf.open(json_name, "r"))
                    self.oracc_pubs = {p["id"]: cdli.json_to_pub(p) for p in pubs_json.values()}
                    self.init_pubs()
                    return
        oracc_pub_ids_and_langs, transliterated_oracc_corpi = oracc.load_all_project_pub_ids(oracc_dir, tqdm=tqdm)
        transliterated_oracc_pub_ids = set(transliterated_oracc_corpi.keys())
        transliterated_oracc_pids_and_oids = \
            [(x["corpus"]["project"], x["corpus"]["textid"]) for x in transliterated_oracc_corpi.values()]
        for pid, oid in tqdm(transliterated_oracc_pids_and_oids[:]):
            tpath = oracc.download_object_translation(oracc_dir, pid, oid)
        self.oracc_pubs = dict()
        for pid in tqdm(transliterated_oracc_pub_ids):
            corpus = transliterated_oracc_corpi[pid]["corpus"]
            catalog_info = transliterated_oracc_corpi[pid]["catalog_info"]
            lang = transliterated_oracc_corpi[pid]["lang"]
            p = oracc.get_object_id_pub(pid, corpus, catalog_info, lang, oracc_dir)
            self.oracc_pubs[pid] = p
        with open(zip_path, "wb") as f:
            with zipfile.ZipFile(f, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                json_str = json.dumps({p.id: cdli.pub_to_json(p) for p in self.oracc_pubs.values()})
                zf.writestr("oracc_pubs.json", bytes(json_str, "utf-8"))
        self.init_pubs()
    def get_pubs(self):
        return self.oracc_pubs.values()

def merge_corpus_pubs(pubss, supported_langs):
    all_pubs = dict()
    for corpus, pubs in pubss:
        for p in pubs:
            if p.language in supported_langs:
                p.corpus = corpus
                if any(len(a.lines) > 0 for a in p.text_areas):
                    all_pubs[p.id] = p
    return all_pubs
