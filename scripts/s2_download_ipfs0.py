import sys
from pathlib import Path
repo_dir = Path(__file__).resolve().parent.parent
if str(repo_dir) not in sys.path:
    sys.path.append(str(repo_dir))

import time
import datetime
from tqdm import tqdm
import requests

import src.utils
import config
import src.ipfs
import src.tr.iter


def extract_ipfs_links(obj, res_set):
    if type(obj) == dict:
        for val in obj.values():
            extract_ipfs_links(val, res_set)
    elif type(obj) == list:
        for val in obj:
            extract_ipfs_links(val, res_set)
    elif type(obj) == str:
        if 'ipfs' in obj.lower():
            res_set.add(obj)


def fetch_ipfs_ref(ref, ipfs_dir):
    assert ref.startswith('ipfs://')
    ref = ref.replace('ipfs://', '')

    if 1:
        req = requests.get(f'https://cloudflare-ipfs.com/ipfs/{ref}')
    else:
        req = requests.get(f'https://ipfs.io/ipfs/{ref}')

    if req.status_code != 200:
        if req.status_code == 403 and req.text == 'ipfs: video streaming is not allowed\n':
            req = requests.get(f'https://ipfs.io/ipfs/{ref}')
            if req.status_code == 200:
                pass
            elif req.status_code == 429:
                print('Too many requests to ipfs.io')
                time.sleep(60)
                return

            else:
                print(req.text)
                raise Exception(f'Error during fetch {ref} from ipfs.io and cloudflare')

        elif req.status_code in [524, 504, 404]:
            # timeout
            return

        else:
            print(req.status_code, repr(req.text))
            raise Exception(f'Error during fetch {ref} from cloudflare')

    temp_fpath = ipfs_dir / ('tmp.' + ref)
    temp_fpath.write_bytes(req.content)

    fpath = ipfs_dir / ref
    temp_fpath.rename(fpath)


def get_refs0_to_fetch():
    ref_set = set()
    for tr in src.tr.iter.iter_tr():
        extract_ipfs_links(tr, ref_set)

    print(f'{len(ref_set)} ipfs0 references found')

    invalid_refs = set()
    for ref in ref_set:
        if not ref.startswith('ipfs://') or '[' in ref:
            invalid_refs.add(ref)
    ref_set = ref_set - invalid_refs
    print('Invalid refs0: ', invalid_refs)

    existing_refs = set(['ipfs://' + fpath.name for fpath in config.ipfs0_dir.iterdir()])

    unexpected_refs = existing_refs - ref_set
    if unexpected_refs:
        print(unexpected_refs)
        print(f'{len(unexpected_refs)} unexpected refs0')

    refs_to_fetch = ref_set - existing_refs
    print(f'{len(refs_to_fetch)} refs0 to fetch')

    return refs_to_fetch


def get_refs1_to_fetch():
    ref_set = set()
    for meta0_file in tqdm(list(config.ipfs0_dir.iterdir())):
        meta0_data = src.utils.read_json(meta0_file)
        extract_ipfs_links(meta0_data, ref_set)

    print(f'{len(ref_set)} ipfs1 references found')

    invalid_refs = set()
    for ref in ref_set:
        if not ref.startswith('ipfs://'):
            invalid_refs.add(ref)
    ref_set = ref_set - invalid_refs
    print('Invalid refs1: ', invalid_refs)

    existing_refs = set()
    for ref in tqdm(list(ref_set)):
        if src.ipfs.get_previews(ref):
            existing_refs.add(ref)

    unexpected_refs = existing_refs - ref_set
    if unexpected_refs:
        print(unexpected_refs)
        raise Exception(f'{len(unexpected_refs)} unexpected refs1')

    refs_to_fetch = ref_set - existing_refs
    print(f'{len(refs_to_fetch)} refs1 to fetch')

    return list(refs_to_fetch)


if __name__ == '__main__':

    for ref in tqdm(get_refs0_to_fetch()):
        fetch_ipfs_ref(ref, config.ipfs0_dir)
