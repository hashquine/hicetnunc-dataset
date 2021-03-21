import sys
import time
from pathlib import Path
from tqdm import tqdm
import requests

repo_dir = Path('.').resolve()
assert repo_dir.name == 'hicetnunc-dataset', repo_dir
if str(repo_dir) not in sys.path:
    sys.path.append(str(repo_dir))

import lib.utils


def check_first_transaction_stamp(min_stamp, sender=None, receiver=None):
    assert type(min_stamp) is int
    req = requests.get('https://api.tzstats.com/tables/op', params={
        'sender': sender,
        'receiver': receiver,
        'limit': 100,
        'columns': ','.join(['time', 'hash']),
        'time.lt': min_stamp,
    })
    if req.status_code != 200:
        print('!!!', req.text)
        raise Exception(f'Server response is not 200 (tzstats/tables/op)')

    req_res = req.json()
    if len(req_res) != 0:
        print('Try using min_stamp=', req_res[0][0])
        raise Exception(f'Invalid min_stamp={min_stamp} for sender={sender}, receiver={receiver}')


def get_transactions_hashes(min_stamp, max_stamp, sender=None, receiver=None):
    limit = 50000
    cursor = None
    page_no = 1

    res = set()
    print(f'sender={repr(sender)}, receiver={repr(receiver)}', end=' ')
    sys.stdout.flush()

    while True:
        print(page_no, end=' ')
        sys.stdout.flush()
        req = requests.get('https://api.tzstats.com/tables/op', params={
            'sender': sender,
            'receiver': receiver,
            'limit': limit,
            'columns': ','.join(['row_id', 'hash']),
            'cursor': cursor,
            'time.gte': min_stamp,
            'time.lt': max_stamp,
        })
        if req.status_code != 200:
            print('!!!', req.text)
            raise Exception(f'Server response is not 200 (tzstats/tables/op)')

        req_res = req.json()
        print(f'({len(req_res)})', end=' ')
        sys.stdout.flush()
        if len(req_res) == 0:
            break

        for op_row_id, op_hash in req_res:
            res.add(op_hash)

        cursor = req_res[-1][0]
        page_no += 1

    print(f'total {len(res)}')
    sys.stdout.flush()

    return res


def get_full_transaction(transaction_hash):
    req = requests.get(f'https://api.tzstats.com/explorer/op/{transaction_hash}')
    if req.status_code != 200:
        print('!!!', req.text)
        raise Exception(f'Server response is not 200 (tzstats/explorer/op)')

    req_res = req.json()
    return req_res


def update_transactions_cache_file(config_hash, min_stamp, stamp_step, addrs):
    assert type(min_stamp) is int and type(stamp_step) is int
    assert min_stamp % stamp_step == 0
    max_stamp = min_stamp + stamp_step

    transactions_file = transactions_cache_dir / config_hash / f'{min_stamp}.json'

    if transactions_file.exists():
        transactions_file_mtime = transactions_file.stat().st_mtime
        if transactions_file_mtime > max_stamp + stamp_step * 3:
            return

    print(f'min_stamp={min_stamp} ({lib.utils.stamp_to_iso_date(min_stamp)}),', end=' ')
    sys.stdout.flush()

    data = lib.utils.read_json(transactions_file)
    if data is None:
        data = {}

    print(f'{len(data)} existing entries')

    transactions_hashes = set()
    for addr in addrs:
        transactions_hashes.update(get_transactions_hashes(min_stamp, max_stamp, sender=addr))
        transactions_hashes.update(get_transactions_hashes(min_stamp, max_stamp, receiver=addr))

    hashes_to_fetch = transactions_hashes - set(data.keys())
    unexpected_hashes = set(data.keys()) - transactions_hashes
    if unexpected_hashes:
        print(unexpected_hashes)
        raise Exception(f'Found {len(unexpected_hashes)} unexpected hashes')

    for tr_no, tr_hash in tqdm(enumerate(hashes_to_fetch), total=len(hashes_to_fetch)):
        # print(f'{tr_no:-5d}/{len(hashes_to_fetch)} Fetching {tr_hash}...', end=' ')
        # sys.stdout.flush()

        data[tr_hash] = get_full_transaction(tr_hash)

        # print(len(data[tr_hash]))

    lib.utils.write_json(data, transactions_file)


def check_min_stamps(config):
    print('Checking min_stamp validity...', end=' ')
    sys.stdout.flush()
    min_stamp = config['min_stamp']
    for addr_entry in config['addrs']:
        if not addr_entry['assert_min_stamp']:
            continue
        addr = addr_entry['addr']
        check_first_transaction_stamp(min_stamp, sender=addr, receiver=None)
        check_first_transaction_stamp(min_stamp, sender=None, receiver=addr)
    print('ok')


def update_transactions_cache(config):
    config_hash = get_config_hash(config)
    cur_stamp = int(time.time())
    stamp_step = config['stamp_step']
    addrs = [item['addr'] for item in config['addrs']]
    
    print(f'config_hash={config_hash}')

    for min_stamp in range(config['min_stamp'], cur_stamp, stamp_step):
        update_transactions_cache_file(config_hash, min_stamp, stamp_step, addrs)


def get_config_hash(config):
    return lib.utils.get_md5_hash({
        'min_stamp': config['stamp_step'],
        'stamp_step': config['stamp_step'],
        'addrs': [item['addr'] for item in config['addrs']],
    })[:10]


transactions_cache_dir = repo_dir / 'cache' / 'transactions'


config = {
    'min_stamp':  1614500000, # Sun Feb 28 2021 08:13:20 GMT+0000
    'stamp_step':     100000, # 1.15 days
    'addrs': [{
        'addr': 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9',
        'name': 'art_house_contract',
        'assert_min_stamp': True,
    }, {
        'addr': 'KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton',
        'name': 'nft_contract',
        'assert_min_stamp': True,
    }, {
        'addr': 'tz1UBZUkXpKGhYsP5KtzDNqLLchwF4uHrGjw',
        'name': 'comission_wallet',
        'assert_min_stamp': False,
    }, {
        'addr': 'KT1TybhR7XraG75JFYKSrh7KnxukMBT5dor6',
        'name': 'curate_contract',
        'assert_min_stamp': True,
    }, {
        'addr': 'KT1AFA2mwNUMNd4SsujE1YYp29vd8BZejyKW',
        'name': 'hdao_contract',
        'assert_min_stamp': True,
    }],
}


if lib.utils.is_in_jupyter(globals()):
    # If running in Jupyter, write script source to file
    (repo_dir / 'scripts' / 'update_blockchain_data.py').write_text(
        lib.utils.get_cur_jupyter_cell_source(globals()),
        'utf-8',
    )

elif __name__ == '__main__':
    check_min_stamps(config)
    update_transactions_cache(config)
