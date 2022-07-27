import os, sys, math
import requests
import json
import shutil
from requests.packages.urllib3.exceptions import InsecureRequestWarning

session = requests.Session()

def get_project_ids():
    return session.get("http://oracc.museum.upenn.edu/projects.json").json()["public"]

CHUNK_SIZE = 16 * 1024

ignore_project_ids = {'contrib/amarna', 'rinap/rinap5p1', 'cdli', 'cams/tlab', 'cams', 'arrim', 'cams/akno', 'cams/etana', 'cams/barutu', 'amgg', 'lovelyrics', 'ctij', 'lacost', 'contrib', 'cams/selbi', 'cams/ludlul', 'contrib/lambert', 'akklove', 'cams/anzu', 'pnao', 'rimanum'}

def download_project_zip(project_id, out_dir, verbose=True):
    
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    project_zip_name = project_id.replace('/', '-') + ".zip"
    url = "http://build-oracc.museum.upenn.edu/json/" + project_zip_name
    if verbose:
        print(url)
    tmp_dir = f"{out_dir}/tmp"
    ofile = f"{out_dir}/{project_zip_name}"
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

def get_all_project_zips(out_dir, verbose=False, tqdm=lambda x: x):
    project_ids = get_project_ids()
    paths = []
    new_ignores = set()
    for p in tqdm(project_ids):
        if p in ignore_project_ids:
            continue
        path = download_project_zip(p, out_dir, verbose=verbose)
        if path is not None:
            paths.append(path)
        else:
            new_ignores.add(p)
    tmp_dir = f"{out_dir}/tmp"
    if os.path.exists(tmp_dir):
        os.rmdir(tmp_dir)
    if len(new_ignores) > 0:
        print("ignore_project_ids =", repr(new_ignores))
    return paths