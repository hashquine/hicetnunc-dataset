import bisect

import src.config
import src.utils


class TrInfoDB:
    def __init__(self):
        self.db = src.utils.read_json(src.config.trs_info_file)
        self.last_tr_chunk_read_cache = ('', None)
        self.make_index()

    def make_index(self):
        self.stamps_list = []
        self.min_row_ids_list = []
        self.hash_to_db_idx = {}

        prev_max_row_id = 0
        for db_idx, (tr_hash, stamp, min_row_id, max_row_id, fname) in enumerate(self.db):
            assert min_row_id <= max_row_id
            assert prev_max_row_id < min_row_id
            prev_max_row_id = max_row_id
            self.stamps_list.append(stamp)
            self.min_row_ids_list.append(min_row_id)
            self.hash_to_db_idx[tr_hash] = db_idx

    def _read_trs_chunk_file(self, fname):
        cache_fname, cache_data = self.last_tr_chunk_read_cache
        if cache_fname != fname:
            fpath = src.config.transactions_dir / fname
            assert fpath.is_file()
            self.last_tr_chunk_read_cache = (
                fname,
                src.utils.read_json(fpath),
            )
        cache_fname, cache_data = self.last_tr_chunk_read_cache
        assert cache_fname == fname
        return cache_data

    def _get_info_by_db_idx(self, db_idx):
        tr_hash, stamp, min_row_id, max_row_id, fname = self.db[db_idx]
        return {
            'hash': tr_hash,
            'stamp': stamp,
            'iso_date': src.utils.stamp_to_iso_date(stamp),
            'min_row_id': min_row_id,
            'max_row_id': max_row_id,
        }

    def get_tr_info_by_row_id(self, row_id, prefix=''):
        full_op = self.get_full_transaction_by_row_id(row_id, return_op=True)
        stamp = src.utils.iso_date_to_stamp(full_op['time'])
        return {
            f'{prefix}hash': full_op['hash'],
            f'{prefix}stamp': stamp,
            f'{prefix}iso_date': src.utils.stamp_to_iso_date(stamp),
        }

    def _get_full_transaction_by_db_idx(self, db_idx):
        db_entry = self.db[db_idx]
        fname = db_entry[4]
        chunk_data = self._read_trs_chunk_file(fname)
        tr_hash = db_entry[0]
        assert tr_hash in chunk_data
        return chunk_data[tr_hash]

    def get_last_row_id_before_stamp(self, stamp):
        idx = bisect.bisect_left(self.stamps_list, stamp)
        if idx == 0:
            raise Exception(f'No transactions before stamp {stamp}')
        db_idx = idx - 1
        return self.db[db_idx][3]

    def get_first_row_id_after_stamp(self, stamp):
        db_idx = bisect.bisect_left(self.stamps_list, stamp)
        if db_idx == len(self.db) - 1:
            raise Exception(f'No transactions after stamp {stamp}')
        return self.db[db_idx][3]

    def get_full_transaction_by_row_id(self, row_id, return_op=False):
        idx = bisect.bisect_left(self.min_row_ids_list, row_id)
        cand0 = self._get_full_transaction_by_db_idx(
            max(0, min(len(self.db) - 1, idx))
        )
        cand1 = self._get_full_transaction_by_db_idx(
            max(0, min(len(self.db) - 1, idx - 1))
        )
        for tr in [cand0, cand1]:
            for op in tr:
                if op['row_id'] == row_id:
                    if return_op:
                        return op
                    else:
                        return tr
        raise Exception(f'Transaction with row_id={row_id} not in local database')
