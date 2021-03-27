from pathlib import Path
import src.utils


repo_dir = Path(__file__).parent.parent.resolve()
assert repo_dir.name == 'hicetnunc-dataset'

cache_dir = repo_dir / 'cache'
cache_dir.mkdir(exist_ok=True)

ipfs0_dir = cache_dir / 'ipfs0'
ipfs0_dir.mkdir(exist_ok=True)
ipfs1_dir = cache_dir / 'ipfs1'
ipfs1_dir.mkdir(exist_ok=True)
previews_dir = cache_dir / 'previews'
previews_dir.mkdir(exist_ok=True)
previews_thumbs_dir = cache_dir / 'previews_thumbs'
previews_thumbs_dir.mkdir(exist_ok=True)

parsed_transactions_dir = cache_dir / 'parsed_transactions'
parsed_transactions_dir.mkdir(exist_ok=True)
nft_state_log_file = parsed_transactions_dir / 'nft_state_log.json'
ah_state_log_file = parsed_transactions_dir / 'ah_state_log.json'
money_state_log_file = parsed_transactions_dir / 'money_state_log.json'
trs_info_file = parsed_transactions_dir / 'trs_info.json'
tzktio_accounts_metadata_file = cache_dir / 'accounts_metadata' / 'tzktio_accounts_metadata.json'
tzktio_accounts_metadata_file.parent.mkdir(exist_ok=True)

dataset_dir = repo_dir / 'dataset'
dataset_dir.mkdir(exist_ok=True)
tokens_db_json_file = dataset_dir / 'tokens_db.json'
swaps_db_json_file = dataset_dir / 'swaps_db.json'


name2addr = {
    'art_house_contract': 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9',
    'nft_contract': 'KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton',
    'comission_wallet': 'tz1UBZUkXpKGhYsP5KtzDNqLLchwF4uHrGjw',
    'curate_contract': 'KT1TybhR7XraG75JFYKSrh7KnxukMBT5dor6',
    'hdao_contract': 'KT1AFA2mwNUMNd4SsujE1YYp29vd8BZejyKW',
    'baking_benjamins': 'tz1S5WxdZR5f9NzsPXhr7L9L1vrEb5spZFur',
}

addr2name = { addr: name for name, addr in name2addr.items() }


fetch_transactions_stamp_step = 100000     # 1.15 days
fetch_transactions_min_stamp = 1614500000  # Sun Feb 28 2021 08:13:20 GMT+0000

fetch_transactions_config = {
    'min_stamp': fetch_transactions_min_stamp,
    'stamp_step': fetch_transactions_stamp_step,
    'addrs': [{
        'addr': name2addr['art_house_contract'],
        'assert_min_stamp': True,
    }, {
        'addr': name2addr['nft_contract'],
        'assert_min_stamp': True,
    }, {
        'addr': name2addr['comission_wallet'],
        'assert_min_stamp': False,
    }, {
        'addr': name2addr['curate_contract'],
        'assert_min_stamp': True,
    }, {
        'addr': name2addr['hdao_contract'],
        'assert_min_stamp': True,
    }],
}

fetch_transactions_config_hash = src.utils.get_fetch_transactions_config_hash(fetch_transactions_config)

transactions_dir = repo_dir / 'cache' / 'transactions' / fetch_transactions_config_hash
