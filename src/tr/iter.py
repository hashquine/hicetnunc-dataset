import sys
from tqdm import tqdm

import src.utils
import src.tr.utils
import config


def get_tr_files(transactions_dir, stamp_step):
    res = [fpath for fpath in transactions_dir.iterdir() if 'invalid' not in fpath.name]
    res.sort(key=lambda f: int(f.stem))

    stamps = [int(fpath.stem) for fpath in res]
    expected_stamps = list(range(stamps[0], stamps[-1] + stamp_step, stamp_step))
    if stamps != expected_stamps:
        print(set(stamps) ^ set(expected_stamps))
        raise Exception(f'Not all transactions files are present')

    return res


def iter_tr_inner(transactions_dir, stamp_step):
    assert transactions_dir.is_dir()
    last_tr_time = '-'

    for tr_file in tqdm(get_tr_files(transactions_dir, stamp_step)):
        transactions = list(src.utils.read_json(tr_file).values())

        if None in transactions:
            print(f'Breaking on transaction not in cache, last time is {last_tr_time}')
            break

        transactions.sort(key=lambda it: it[0]['row_id'])

        for tr in transactions:
            by_internal_index = []
            for op in tr:
                op_c = op['op_c']
                if op_c == len(by_internal_index):
                    by_internal_index.append([op])
                elif op_c == len(by_internal_index) - 1:
                    by_internal_index[-1].append(op)
                else:
                    raise Exception(f'Unexpected internal index: {op_c} / {len(by_internal_index) - 1}')

            for op_c, ops in enumerate(by_internal_index):
                if len(src.tr.utils.get_ops_addrs(ops).intersection(config.fetch_transactions_addrs_set)) == 0:
                    continue

                yield {
                    'hash': ops[0]['hash'],
                    'hash_c': ops[0]['hash'] + '_' + str(op_c),
                    'op_c': op_c,
                    'fpath': tr_file,
                    'time': ops[0]['time'],
                    'stamp': src.utils.iso_date_to_stamp(ops[0]['time']),
                    'ops': ops,
                }
            last_tr_time = ops[0]['time']
    sys.stdout.flush()
    print()


def iter_tr(
    transactions_dir=config.transactions_dir,
    stamp_step=config.fetch_transactions_stamp_step,
):
    prev_stamp = 0
    prev_row_id = 0
    prev_tr = '-'
    for tr in iter_tr_inner(transactions_dir, stamp_step):
        for op in tr['ops']:
            assert op['hash'] == tr['hash']
            assert op['time'] == tr['time']
            assert prev_row_id < op['row_id'], (prev_row_id, op['row_id'], prev_tr['hash'], prev_tr['fpath'], op['hash'], tr['fpath'])
            prev_row_id = op['row_id']

        file_min_stamp = int(tr['fpath'].stem)
        file_max_stamp = file_min_stamp + stamp_step
        assert file_min_stamp % stamp_step == 0, (tr['fpath'], stamp_step)
        assert file_min_stamp <= tr['stamp'] < file_max_stamp, (tr['fpath'], tr['stamp'], stamp_step)

        assert prev_stamp <= tr['stamp'], tr['hash']

        yield tr

        prev_stamp = tr['stamp']
        prev_tr = tr
