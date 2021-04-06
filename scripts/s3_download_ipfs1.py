import sys
from pathlib import Path
repo_dir = Path(__file__).resolve().parent.parent
if str(repo_dir) not in sys.path:
    sys.path.append(str(repo_dir))


import config
from tqdm import tqdm

import scripts.s2_download_ipfs0


if __name__ == '__main__':

    for ref in tqdm(scripts.s2_download_ipfs0.get_refs1_to_fetch()):
        scripts.s2_download_ipfs0.fetch_ipfs_ref(ref, config.ipfs1_dir)
