import csv


class FieldsGroup:
    def expand_fields(self, prefix):
        raise NotImplementedError()


class TrEvent(FieldsGroup):
    def __init__(self, row_id=-1):
        self.row_id = row_id

    def set_row_id(self, row_id):
        self.row_id = row_id

    def expand_fields(self, prefix):
        info = tr_info_db.get_tr_info_by_row_id(self.row_id)
        return {
            f'{prefix}_iso_date': info['iso_date'],
            f'{prefix}_stamp': info['stamp'],
            f'{prefix}_hash': info['hash'],
            f'{prefix}_row_id': info['row_id'],
        }


class FloatSet(FieldsGroup):
    def __init__(self, values=None):
        self.zero_count = 0
        self.values = values or []

    def add(self, v):
        if v == 0:
            self.zero_count += 1
        else:
            self.values.append(v)

    def expand_fields(self, prefix):
        prefix1 = '_'.join(prefix.split('_')[:-1])
        prefix2 = prefix
        if len(self.values) == 0:
            return {
                f'{prefix1}_count': 0,
                f'{prefix1}_zero_count': self.zero_count,
                f'{prefix2}_min': 0,
                f'{prefix2}_max': 0,
                f'{prefix2}_sum': 0,
                f'{prefix2}_avg': 0,
            }
        else:
            return {
                f'{prefix1}_count': len(self.values),
                f'{prefix1}_zero_count': self.zero_count,
                f'{prefix2}_min': min(self.values),
                f'{prefix2}_max': max(self.values),
                f'{prefix2}_sum': sum(self.values),
                f'{prefix2}_avg': sum(self.values) / len(self.values),
            }


def make_dataset(db, fpath):
    expanded_db = {}
    for row_id, row in db.items():
        new_row = {}
        for field, val in row.items():
            if isinstance(val, FieldsGroup):
                for exp_field, exp_val in val.expand_fields(field).items():
                    new_row[exp_field] = exp_val
            else:
                assert type(val) in [int, float, str]
                new_row[field] = val
        expanded_db[row_id] = new_row

    rows = list(expanded_db.values())
    cols_order = list(rows[0].keys())
    for row in rows:
        row_keys_order = list(row.keys())
        assert row_keys_order == cols_order, (row_keys_order, cols_order)

    with fpath.with_suffix('.csv').open('w', encoding='utf-8', newline='') as csv_file:
        csv_writer = csv.writer(
            csv_file,
            delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL,
        )
        csv_writer.writerow([col for col in cols_order])
        for row in rows:
            csv_writer.writerow([row[col] for col in cols_order])

    src.utils.write_json(expanded_db, fpath.with_suffix('.json'))
