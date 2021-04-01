import sys
from pathlib import Path
repo_dir = Path(__file__).parent.parent.resolve()
if str(repo_dir) not in sys.path:
    sys.path.append(str(repo_dir))


import src.utils
import src.config
import src.contracts.addrs_state
import src.contracts.state_utils

from tqdm import tqdm
import requests


addrs_state_log = src.utils.read_json(src.config.addrs_state_log_file)
addrs_state = src.contracts.addrs_state.AddrsState()
addrs_state_replayer = src.contracts.state_utils.StateReplayer(addrs_state_log, addrs_state)

addrs_state_replayer.replay_to_end()

accounts_metadata = {}

for addr, addr_db_entry in tqdm(list(addrs_state.addrs.items())):
    req = requests.get(f'https://api.tzkt.io/v1/accounts/{addr}/metadata')
    if req.status_code == 200:
        accounts_metadata[addr] = req.json()
    elif req.status_code == 204:
        accounts_metadata[addr] = None
    else:
        print('!!!', addr, req.status_code, req.text)
        accounts_metadata[addr] = None

src.utils.write_json(accounts_metadata, src.config.tzktio_accounts_metadata_file)
