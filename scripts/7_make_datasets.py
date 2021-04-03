import sys
from pathlib import Path
repo_dir = Path(__file__).resolve().parent.parent
if str(repo_dir) not in sys.path:
    sys.path.append(str(repo_dir))


from collections import defaultdict
from tqdm import tqdm

import src.utils
import src.config
import src.datasets
import src.tr.info_db


print('Reading state logs...')

tokens_db = src.utils.read_json(src.config.tokens_db_json_file)
swaps_db = src.utils.read_json(src.config.swaps_db_json_file)
addrs_db = src.utils.read_json(src.config.addrs_db_json_file)

nft_state_log = src.utils.read_json(src.config.nft_state_log_file)
ah_state_log = src.utils.read_json(src.config.ah_state_log_file)
money_state_log = src.utils.read_json(src.config.money_state_log_file)

tr_info_db = src.tr.info_db.TrInfoDB()


print('Join contracts logs with transactions...')

transactions_index = defaultdict(lambda: {
    'nft_log_entry': None,
    'ah_log_entry': None,
    'money_log_entry': None,
    'created_swap': None,
    'created_token': None,
})


for entries, row_id_field, entry_field in [
    (nft_state_log, 'row_id', 'nft_log_entry'),
    (ah_state_log, 'row_id', 'ah_log_entry'),
    (money_state_log, 'row_id', 'money_log_entry'),
    (swaps_db.values(), 'created_row_id', 'created_swap'),
    (tokens_db.values(), 'mint_ah_row_id', 'created_token'),
]:
    for entry in entries:
        tr_hash = tr_info_db.get_tr_info_by_row_id(entry[row_id_field])['hashc']
        assert transactions_index[tr_hash][entry_field] is None
        transactions_index[tr_hash][entry_field] = entry
        entry['tr_index_entry'] = transactions_index[tr_hash]


print('Checking, that every art house log entry has corresponding nft log entry...')

for ah_log_entry in ah_state_log:
    entry_method = ah_log_entry['method']
    nft_log_entry = ah_log_entry['tr_index_entry']['nft_log_entry']
    if entry_method in ['apply_collect', 'apply_swap', 'apply_cancel_swap']:
        assert nft_log_entry['method'] == 'apply_transfer'
    elif entry_method == 'apply_mint':
        assert nft_log_entry['method'] == 'apply_mint'
    else:
        assert False, entry_method

