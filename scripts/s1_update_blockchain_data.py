import sys
from pathlib import Path
repo_dir = Path(__file__).resolve().parent.parent
if str(repo_dir) not in sys.path:
    sys.path.append(str(repo_dir))

import time
from tqdm import tqdm
import requests

import src.utils
import config


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


class RetryableException(Exception):
    pass


def get_full_transaction(transaction_hash):
    try:
        req = requests.get(f'https://api.tzstats.com/explorer/op/{transaction_hash}', timeout=5)
    except Exception as e:
        raise RetryableException(str(e))

    if req.status_code != 200:
        print('!!!', req.text)
        raise Exception(f'Server response is not 200 (tzstats/explorer/op)')

    req_res = req.json()
    return req_res


def update_transactions_cache_file(config_hash, min_stamp, stamp_step, addrs, force_check=False):
    assert type(min_stamp) is int and type(stamp_step) is int
    assert min_stamp % stamp_step == 0
    max_stamp = min_stamp + stamp_step

    transactions_file = config.transactions_dir / f'{min_stamp}.json'

    if not force_check and transactions_file.exists():
        transactions_file_mtime = transactions_file.stat().st_mtime
        if transactions_file_mtime > max_stamp + stamp_step:
            for tr_hash, tr_val in src.utils.read_json(transactions_file).items():
                if tr_val is None:
                    break
            else:
                # If there are no empty entries, do not perform check
                return

    print(f'min_stamp={min_stamp} ({src.utils.stamp_to_iso_date(min_stamp)}),', end=' ')
    sys.stdout.flush()

    data = src.utils.read_json(transactions_file)
    if data is None:
        data = {}

    existing_hashes = set()
    for tr_hash, tr_val in data.items():
        if tr_val is not None:
            existing_hashes.add(tr_hash)

    print(f'{len(data)} existing entries, {len(existing_hashes)} non-empty')

    transactions_hashes = set()
    for addr in addrs:
        transactions_hashes.update(get_transactions_hashes(min_stamp, max_stamp, sender=addr))
        transactions_hashes.update(get_transactions_hashes(min_stamp, max_stamp, receiver=addr))

    hashes_to_fetch = transactions_hashes - existing_hashes
    unexpected_hashes = existing_hashes - transactions_hashes
    if unexpected_hashes:
        print(unexpected_hashes)
        raise Exception(f'Found {len(unexpected_hashes)} unexpected hashes')

    for tr_hash in hashes_to_fetch:
        data[tr_hash] = None

    last_save_stamp = 0

    for tr_no, tr_hash in tqdm(enumerate(hashes_to_fetch), total=len(hashes_to_fetch)):
        for trial_no in range(10):
            if time.time() - last_save_stamp > 10 * 60:
                src.utils.write_json(data, transactions_file)
                last_save_stamp = time.time()
            time.sleep(0.3)  # just slow down a little bit
            try:
                res_val = get_full_transaction(tr_hash)
                break
            except RetryableException:
                print('retry', trial_no)
                time.sleep(2 ** trial_no)  # exponential cooldown

        data[tr_hash] = res_val

    src.utils.write_json(data, transactions_file)


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


def update_transactions_cache(config, force_check=False):
    config_hash = src.utils.get_fetch_transactions_config_hash(config)
    cur_stamp = int(time.time())
    stamp_step = config['stamp_step']
    addrs = [item['addr'] for item in config['addrs']]

    print(f'config_hash={config_hash}')

    for min_stamp in range(config['min_stamp'], cur_stamp, stamp_step):
        update_transactions_cache_file(config_hash, min_stamp, stamp_step, addrs, force_check)


if __name__ == '__main__':

    script_config = config.fetch_transactions_config
    check_min_stamps(script_config)
    update_transactions_cache(script_config, force_check=False)
