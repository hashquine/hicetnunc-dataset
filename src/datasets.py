import csv
from collections import defaultdict

import src.utils
import config


class FieldsGroup:
    def expand_fields(self, prefix, tr_info_db):
        raise NotImplementedError()


class TrEvent(FieldsGroup):
    def __init__(self, row_id=-1):
        self.row_id = row_id

    def __repr__(self):
        return f'TrEvent({self.row_id})'

    def set_row_id(self, row_id):
        self.row_id = row_id

    def expand_fields(self, prefix, tr_info_db):
        if self.row_id == -1:
            return {
                f'{prefix}_iso_date': '',
                f'{prefix}_stamp': -1,
                f'{prefix}_hash': '',
                f'{prefix}_row_id': -1,
            }
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

    def __repr__(self):
        return f'FloatSet(0x{self.zero_count} + {len(self.values)})'

    def add(self, v, count=1):
        for i in range(count):
            if v == 0:
                self.zero_count += 1
            else:
                self.values.append(v)

    def count(self, mode='all'):
        if mode == 'all':
            return len(self.values) + self.zero_count
        elif mode == 'zero':
            return self.zero_count
        elif mode == 'non_zero':
            return len(self.values)

    def expand_fields(self, prefix, tr_info_db):
        prefix1 = '_'.join(prefix.split('_')[:-1])
        prefix2 = prefix
        if len(self.values) == 0:
            return {
                f'{prefix1}_count': 0,
                f'{prefix1}_nonzero_count': self.zero_count,
                f'{prefix1}_zero_count': self.zero_count,
                f'{prefix2}_min': 0,
                f'{prefix2}_max': 0,
                f'{prefix2}_sum': 0,
                f'{prefix2}_avg': 0,
            }
        else:
            return {
                f'{prefix1}_count': len(self.values) + self.zero_count,
                f'{prefix1}_nonzero_count': len(self.values),
                f'{prefix1}_zero_count': self.zero_count,
                f'{prefix2}_min': min(self.values),
                f'{prefix2}_max': max(self.values),
                f'{prefix2}_sum': sum(self.values),
                f'{prefix2}_avg': sum(self.values) / len(self.values),
            }


def make_dataset(db, fpath, tr_info_db):
    expanded_db = {}
    for row_id, row in db.items():
        new_row = {}
        for field, val in row.items():
            if isinstance(val, FieldsGroup):
                for exp_field, exp_val in val.expand_fields(field, tr_info_db).items():
                    new_row[exp_field] = exp_val
            else:
                assert type(val) in [int, float, str], type(val)
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
            csv_writer.writerow([
                str(row[col]).replace('\0', '')
                for col in cols_order
            ])

    src.utils.write_json(expanded_db, fpath.with_suffix('.json'))


def validate_type(row, field_id, field_type, checked_fields, is_csv=False):
    field_val = row[field_id]
    checked_fields.add(field_id)

    if is_csv:
        assert type(field_val) is str

    if field_type == 'string':
        assert type(field_val) is str

    elif field_type == 'unsigned_string':
        assert type(field_val) is str, field_id
        if field_val != '':
            assert int(field_val) >= 0

    elif field_type == 'boolean':
        if not csv:
            assert type(field_val) is int
        assert int(field_val) in [0, 1]

    elif field_type == 'unsigned_integer':
        if not csv:
            assert type(field_val) is int
        assert float(field_val) % 1 == 0, field_id
        assert float(field_val) >= 0 or float(field_val) == -1, field_id

    elif field_type == 'unsigned_float':
        if not csv:
            assert type(field_val) in [int, float], field_id
        assert float(field_val) >= 0 or float(field_val) == -1, field_id

    elif field_type == 'iso_date':
        assert type(field_val) is str
        if field_val != '':
            assert field_val.endswith('Z')
            assert 'T' in field_val
            assert len(field_val) == 20, len(field_val)

    elif field_type == 'tr_hash':
        assert type(field_val) is str
        if field_val != '':
            assert len(field_val) == 51, len(field_val)

    elif field_type == 'address':
        assert type(field_val) is str
        if field_val != '':
            assert field_val[:2].lower() in ['kt', 'tz'], (field_id, field_val)
            assert len(field_val) == 36

    elif field_type == 'ipfs':
        assert type(field_val) is str
        if field_val != '':
            assert field_val[:2] in ['Qm'], (field_id, field_val)
            assert len(field_val) == 46

    else:
        raise Exception(f'Unkown field type "{field_type}"')


def validate_field(row, field_schema, checked_fields, is_csv=False):
    field_type = field_schema['type']
    field_id = field_schema['field']

    if field_type == 'event':
        validate_type(
            row,
            field_id + '_iso_date',
            'iso_date',
            checked_fields,
            is_csv,
        )
        validate_type(
            row,
            field_id + '_stamp',
            'unsigned_integer',
            checked_fields,
            is_csv,
        )
        validate_type(
            row,
            field_id + '_hash',
            'tr_hash',
            checked_fields,
            is_csv,
        )
        validate_type(
            row,
            field_id + '_row_id',
            'unsigned_integer',
            checked_fields,
            is_csv,
        )

    elif field_type == 'float_set':
        prefix1 = '_'.join(field_id.split('_')[:-1])
        validate_type(
            row,
            prefix1 + '_count',
            'unsigned_integer',
            checked_fields,
            is_csv,
        )
        validate_type(
            row,
            prefix1 + '_nonzero_count',
            'unsigned_integer',
            checked_fields,
            is_csv,
        )
        validate_type(
            row,
            prefix1 + '_zero_count',
            'unsigned_integer',
            checked_fields,
            is_csv,
        )
        validate_type(
            row,
            field_id + '_min',
            'unsigned_float',
            checked_fields,
            is_csv,
        )
        validate_type(
            row,
            field_id + '_max',
            'unsigned_float',
            checked_fields,
            is_csv,
        )
        validate_type(
            row,
            field_id + '_sum',
            'unsigned_float',
            checked_fields,
            is_csv,
        )
        validate_type(
            row,
            field_id + '_avg',
            'unsigned_float',
            checked_fields,
            is_csv,
        )

    else:
        validate_type(
            row,
            field_id,
            field_type,
            checked_fields,
            is_csv,
        )


def validate_row(row, fields_by_id, is_csv=False):
    checked_fields = set()
    for field_id, field_schema in fields_by_id.items():
        validate_field(row, fields_by_id[field_id], checked_fields, is_csv)
    extra_fields = set(row.keys()) - checked_fields
    if extra_fields:
        raise Exception(f'There are extra fields: {extra_fields}')


def validate_rows(rows, dataset_fields, is_csv=False):
    fields_by_id = {}
    for field_group, fields in dataset_fields.items():
        for field_entry in fields:
            fields_by_id[field_entry['field']] = field_entry

    unique_values = defaultdict(set)

    for row in rows:
        validate_row(row, fields_by_id, is_csv)
        for field_id, field_val in row.items():
            unique_values[field_id].add(field_val)

    for field_id, field_vals in unique_values.items():
        assert len(field_vals) >= 1, field_id
        if len(field_vals) == 1:
            field_val = list(field_vals)[0]
            print(f'Field "{field_id}" has single value {repr(field_val)}')


def validate_datasets():
    datasets_fields = src.utils.read_json(config.datasets_fields_file)

    for dataset_id, dataset_fields in datasets_fields.items():
        print('Validating', dataset_id, '...')
        dataset_csv_file = config.dataset_dir / (dataset_id + '.csv')
        with dataset_csv_file.open('r', newline='', encoding='utf-8') as f:
            validate_rows([
                row
                for row in csv.DictReader(f)
            ], dataset_fields)

        dataset_json = src.utils.read_json(config.dataset_dir / (dataset_id + '.json'))
        validate_rows([
            row
            for row in dataset_json.values()
        ], dataset_fields)
        print()
