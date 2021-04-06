import bisect

import config
import src.utils


class TrInfoDB:
    def __init__(self):
        self.db = src.utils.read_json(config.trs_info_file)
        self.tr_by_hashc_cache = {}
        self.last_tr_chunk_read_cache = ('', None)
        self.make_index()

    def make_index(self):
        self.stamps_list = []
        self.min_row_ids_list = []
        self.hashc_to_db_idx = {}

        prev_max_row_id = 0
        for db_idx, (tr_hashc, stamp, min_row_id, max_row_id, fname, tr_volume) in enumerate(self.db):
            assert min_row_id <= max_row_id
            assert prev_max_row_id < min_row_id
            prev_max_row_id = max_row_id
            self.stamps_list.append(stamp)
            self.min_row_ids_list.append(min_row_id)
            self.hashc_to_db_idx[tr_hashc] = db_idx

    def _read_trs_chunk_file(self, fname):
        cache_fname, cache_data = self.last_tr_chunk_read_cache
        if cache_fname != fname:
            fpath = config.transactions_dir / fname
            assert fpath.is_file()
            self.last_tr_chunk_read_cache = (
                fname,
                src.utils.read_json(fpath),
            )
        cache_fname, cache_data = self.last_tr_chunk_read_cache
        assert cache_fname == fname
        return cache_data

    def _get_info_by_db_idx(self, db_idx):
        tr_hashc, stamp, min_row_id, max_row_id, fname, tr_volume = self.db[db_idx]
        return {
            'hash': tr_hashc.split('_')[0],
            'hashc': tr_hashc,
            'stamp': stamp,
            'iso_date': src.utils.stamp_to_iso_date(stamp),
            'min_row_id': min_row_id,
            'max_row_id': max_row_id,
            'db_idx': db_idx,
            'volume': tr_volume,
        }

    def get_tr_info_by_row_id(self, row_id):
        idx = bisect.bisect_left(self.min_row_ids_list, row_id)

        candidates = []
        try:
            candidates.append(self._get_info_by_db_idx(idx))
        except:
            pass
        try:
            candidates.append(self._get_info_by_db_idx(idx - 1))
        except:
            pass

        for cand in candidates:
            if cand['min_row_id'] <= row_id <= cand['max_row_id']:
                tr_info = cand
                break
        else:
            raise Exception(f'Transaction row_id={row_id} not found')

        return {
            **tr_info,
            'row_id': row_id,
        }

    def _get_full_tr_by_db_idx(self, db_idx):
        db_entry = self.db[db_idx]
        fname = db_entry[4]
        tr_hashc = db_entry[0]
        if tr_hashc not in self.tr_by_hashc_cache:
            chunk_data = self._read_trs_chunk_file(fname)
            tr_hash = tr_hashc.split('_')[0]
            tr_op_no = int(tr_hashc.split('_')[1])
            assert tr_hash in chunk_data
            self.tr_by_hashc_cache[tr_hashc] = [
                op
                for op in chunk_data[tr_hash]
                if op['op_c'] == tr_op_no
            ]
        return self.tr_by_hashc_cache[tr_hashc]

    def get_full_tr_by_hashc(self, tr_hashc):
        if tr_hashc not in self.tr_by_hashc_cache:
            db_idx = self.hashc_to_db_idx[tr_hashc]
            self.tr_by_hashc_cache[tr_hashc] = self._get_full_tr_by_db_idx(db_idx)
        return self.tr_by_hashc_cache[tr_hashc]

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

    def get_full_tr_by_row_id(self, row_id, return_op=False):
        tr_info = self.get_tr_info_by_row_id(row_id)
        full_tr = self._get_full_tr_by_db_idx(tr_info['db_idx'])

        for op in full_tr:
            if op['row_id'] == row_id:
                if return_op:
                    return op
                else:
                    return full_tr
        raise Exception(f'Transaction with row_id={row_id} not in local database')
