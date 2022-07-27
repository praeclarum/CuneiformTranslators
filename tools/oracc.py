import os, sys, math
import requests
import json
import shutil
from requests.packages.urllib3.exceptions import InsecureRequestWarning

session = requests.Session()

def get_project_ids():
    return session.get("http://oracc.museum.upenn.edu/projects.json").json()["public"]

CHUNK_SIZE = 16 * 1024

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
