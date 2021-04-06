import sys
import shutil
from pathlib import Path
import src.utils


repo_dir = Path(__file__).parent.resolve()
assert repo_dir.name == 'hicetnunc-dataset'

cache_dir = repo_dir / 'cache'
export_cache_dir = repo_dir / 'export_cache'
export_cache_archive_file = repo_dir / 'cache.zip'
export_dataset_archive_file = repo_dir / 'dataset.zip'

if not (cache_dir / 'ipfs0').exists():
    if export_cache_archive_file.exists():
        print('Extracting cache.zip...', end=' ')
        sys.stdout.flush()
        shutil.unpack_archive(export_cache_archive_file, cache_dir, 'zip')
        print('done\n')
    else:
        print('You should download cache.zip and put into repository root')
        sys.exit()

ipfs0_dir = cache_dir / 'ipfs0'
ipfs0_dir.mkdir(exist_ok=True)
ipfs1_dir = cache_dir / 'ipfs1'
ipfs1_dir.mkdir(exist_ok=True)
previews_dir = cache_dir / 'previews'
previews_dir.mkdir(exist_ok=True)
previews_dimensions_cache_file = previews_dir / 'dimensions.json'

parsed_transactions_dir = cache_dir / 'parsed_transactions'
parsed_transactions_dir.mkdir(exist_ok=True)
nft_state_log_file = parsed_transactions_dir / 'nft_state_log.json'
ah_state_log_file = parsed_transactions_dir / 'ah_state_log.json'
money_state_log_file = parsed_transactions_dir / 'money_state_log.json'
trs_info_file = parsed_transactions_dir / 'trs_info.json'
addrs_state_log_file = parsed_transactions_dir / 'addrs_state_log.json'
tokens_db_json_file = parsed_transactions_dir / 'tokens_db.json'
swaps_db_json_file = parsed_transactions_dir / 'swaps_db.json'
addrs_db_json_file = parsed_transactions_dir / 'addrs_db.json'

accounts_metadata_dir = cache_dir / 'accounts_metadata'
accounts_metadata_dir.mkdir(exist_ok=True)
tzktio_accounts_metadata_file = accounts_metadata_dir / 'tzktio_accounts_metadata.json'
tzktio_accounts_logos_dir = accounts_metadata_dir / 'logos'
tzktio_accounts_logos_dir.mkdir(exist_ok=True)

dataset_dir = repo_dir / 'dataset'
dataset_dir.mkdir(exist_ok=True)
datasets_fields_file = dataset_dir / 'fields_list.json'
datasets_fields_file.parent.mkdir(exist_ok=True)

name2addr = {
    'art_house_contract': 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9',
    'nft_contract': 'KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton',
    'comission_wallet': 'tz1UBZUkXpKGhYsP5KtzDNqLLchwF4uHrGjw',
    'curate_contract': 'KT1TybhR7XraG75JFYKSrh7KnxukMBT5dor6',
    'hdao_contract': 'KT1AFA2mwNUMNd4SsujE1YYp29vd8BZejyKW',
    'baking_benjamins': 'tz1S5WxdZR5f9NzsPXhr7L9L1vrEb5spZFur',
    'burn': 'tz1burnburnburnburnburnburnburjAYjjX',
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

fetch_transactions_addrs_set = {
    item['addr']
    for item in fetch_transactions_config['addrs']
}

fetch_transactions_config_hash = src.utils.get_fetch_transactions_config_hash(fetch_transactions_config)

transactions_dir = repo_dir / 'cache' / 'transactions' / fetch_transactions_config_hash

previews_config = {
    'ps_1024x1024': {
        'type': 'render',
        'extension': '.jpeg',
        'resolution': [1024, 1024],
        'service': 'preview-service',
    },
    'thumbs_256x256': {
        'type': 'thumb',
        'extension': '.jpeg',
        'resolution': [256, 256],
        'sources': ['ps_1024x1024'],
        'service': 'preview-service',
    },
}


# this directory is optional
website_repo_dir = repo_dir.parent.resolve() / 'hashquine.github.io'
