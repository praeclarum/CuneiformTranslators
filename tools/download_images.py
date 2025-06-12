"""Download images from cdli.earth"""

import os
import requests
import sys
import tqdm
import time

downloads_dir = os.environ.get("DOWNLOADS_DIR", "/Volumes/FrankDisk/cdli_images")
reverse_download_order = "--rev" in sys.argv

src_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(os.path.join(src_dir, "..", "data"))
atf_path = os.path.join(data_dir, "cdliatf_unblocked.atf")

def get_pub_ids():
    """Get publication IDs from the ATF file."""
    pub_ids = []
    with open(atf_path, "r") as f:
        for line in tqdm.tqdm(f):
            if line.startswith("&"):
                parts = line.split()
                if len(parts) > 1:
                    pub_id = parts[0][1:]
                    if len(pub_id) == 7:
                        pub_ids.append(pub_id)
    return sorted(pub_ids)


pub_ids = get_pub_ids()

print(f"Found {len(pub_ids):,} publications.")

session = requests.Session()

def download_pub_images(pub_id, timeout=10):
    """Download images for a given publication ID."""
    global session
    urls = [
        f"https://cdli.earth/dl/photo/{pub_id}.jpg",
        f"https://cdli.earth/dl/lineart/{pub_id}_l.jpg"
    ]
    download_dir = os.path.join(downloads_dir, pub_id[:4])
    got_response = False
    for url in urls:
        filename = os.path.join(download_dir, os.path.basename(url))
        if os.path.exists(filename):
            continue
        try:
            response = session.get(url, timeout=timeout)
            got_response = True
            if response.status_code == 200:
                os.makedirs(download_dir, exist_ok=True)
                with open(filename, "wb") as f:
                    f.write(response.content)                    
            elif response.status_code == 404:
                # print(f"Image not found for {url}, skipping.")
                pass
            else:
                print(f"Failed to download {url}: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error downloading {url}: {e}")
            print(f"Retrying after 61 secs...")
            del session
            time.sleep(61)
            session = requests.Session()

if reverse_download_order:
    pub_ids.reverse()

for pub_id in tqdm.tqdm(pub_ids):
    # print(f"Downloading: {pub_id}")
    download_pub_images(pub_id)
