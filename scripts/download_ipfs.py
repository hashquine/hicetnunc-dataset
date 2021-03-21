import sys
import time
import datetime
from pathlib import Path
from tqdm import tqdm
import requests

repo_dir = Path('.').resolve()
assert repo_dir.name == 'hicetnunc-dataset', repo_dir
if str(repo_dir) not in sys.path:
    sys.path.append(str(repo_dir))

import lib.utils
import lib.iter_tr


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


stamp_step = 100000
config_hash = 'cd9acbdf4c'
transactions_dir = repo_dir / 'cache' / 'transactions' / config_hash
assert transactions_dir.is_dir()

ipfs0_dir = repo_dir / 'cache' / 'ipfs0'
ipfs0_dir.mkdir(exist_ok=True)
ipfs1_dir = repo_dir / 'cache' / 'ipfs1'
ipfs1_dir.mkdir(exist_ok=True)


def fetch_ipfs_ref(ref, ipfs_dir):
    assert ref.startswith('ipfs://')
    ref = ref.replace('ipfs://', '')

    req = requests.get(f'https://cloudflare-ipfs.com/ipfs/{ref}')
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
    for tr in lib.iter_tr.iter_tr(transactions_dir, stamp_step):
        extract_ipfs_links(tr, ref_set)

    print(f'{len(ref_set)} ipfs0 references found')

    invalid_refs = set()
    for ref in ref_set:
        if not ref.startswith('ipfs://'):
            invalid_refs.add(ref)
    ref_set = ref_set - invalid_refs
    print('Invalid refs0: ', invalid_refs)

    existing_refs = set(['ipfs://' + fpath.name for fpath in ipfs0_dir.iterdir()])

    unexpected_refs = existing_refs - ref_set
    if unexpected_refs:
        print(unexpected_refs)
        raise Exception(f'{len(unexpected_refs)} unexpected refs0')

    refs_to_fetch = ref_set - existing_refs
    print(f'{len(refs_to_fetch)} refs0 to fetch')

    return refs_to_fetch


def get_refs1_to_fetch():
    ref_set = set()
    for meta0_file in tqdm(list(ipfs0_dir.iterdir())):
        meta0_data = lib.utils.read_json(meta0_file)
        extract_ipfs_links(meta0_data, ref_set)

    print(f'{len(ref_set)} ipfs1 references found')

    invalid_refs = set()
    for ref in ref_set:
        if not ref.startswith('ipfs://'):
            invalid_refs.add(ref)
    ref_set = ref_set - invalid_refs
    print('Invalid refs1: ', invalid_refs)

    existing_refs = set(['ipfs://' + fpath.name for fpath in ipfs1_dir.iterdir()])

    unexpected_refs = existing_refs - ref_set
    if unexpected_refs:
        print(unexpected_refs)
        raise Exception(f'{len(unexpected_refs)} unexpected refs1')

    refs_to_fetch = ref_set - existing_refs
    print(f'{len(refs_to_fetch)} refs1 to fetch')

    return list(refs_to_fetch)


if lib.utils.is_in_jupyter(globals()):
    # If running in Jupyter, write script source to file
    (repo_dir / 'scripts' / 'download_ipfs.py').write_text(
        lib.utils.get_cur_jupyter_cell_source(globals()),
        'utf-8',
    )

elif __name__ == '__main__':

    for ref in tqdm(get_refs0_to_fetch()):
        fetch_ipfs_ref(ref)

    for ref in tqdm(get_refs1_to_fetch()):
        fetch_ipfs_ref(ref, ipfs1_dir)
