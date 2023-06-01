import sys, os, datetime
import json
from tqdm import tqdm
from collections import defaultdict

import cdli
import oracc

class Corpus:
    def __init__(self, id):
        self.id = id
    def get_pubs_with_lang(self, src_lang):
        raise NotImplementedError

class CDLI(Corpus):
    def __init__(self):
        super().__init__("cdli")
        self.cdli_pubs = cdli.get_atf()
        self.cdli_index = {x.id: x for x in self.cdli_pubs}
        # cdli_pub_ids = set(self.cdli_index.keys())
    def get_pubs_with_lang(self, src_lang):
        transliterated_cdli_index = {x.id: x for x in self.cdli_pubs if x.language == src_lang}
        return transliterated_cdli_index

class ORACC(Corpus):
    def __init__(self, oracc_dir, download=False, tqdm=tqdm):
        super().__init__("oracc")
        json_path = "../data/oracc_pubs.json"
        if os.path.exists(json_path):
            pubs_json = json.load(open(json_path, "r"))
            self.oracc_transliterated_pubs = {p["id"]: cdli.json_to_pub(p) for p in pubs_json.values()}
            return
        # oracc_dir = os.path.abspath(f"/Volumes/FrankDisk/oracc_zips")
        # oracc_dir = os.path.abspath(f"/home/fak/nn/Data/oracc_zips")
        # project_zips = oracc.get_all_project_zips(oracc_dir, verbose=False, tqdm=tqdm)
        # all_corpus_object_ids = oracc.get_all_corpus_object_ids(project_zips[:], tqdm=tqdm)
        oracc_pub_ids_and_langs, transliterated_oracc_corpi = oracc.load_all_project_pub_ids(oracc_dir, tqdm=tqdm)
        transliterated_oracc_pub_ids = set(transliterated_oracc_corpi.keys())
        transliterated_oracc_pids_and_oids = \
            [(x["corpus"]["project"], x["corpus"]["textid"]) for x in transliterated_oracc_corpi.values()]
        if download:
            for pid, oid in tqdm(transliterated_oracc_pids_and_oids[:]):
                tpath = oracc.download_object_translation(oracc_dir, pid, oid)
        self.oracc_transliterated_pubs = dict()
        for pid in tqdm(transliterated_oracc_pub_ids):
            p = oracc.get_object_id_pub(pid, oracc_dir)
            self.oracc_transliterated_pubs[pid] = p
    def get_pubs_with_lang(self, src_lang):
        transliterated_oracc_index = {x.id: x for x in self.oracc_transliterated_pubs.values() if x.language == src_lang}
        return transliterated_oracc_index
