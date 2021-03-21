import json
import hashlib
import datetime
import dateutil.parser


def read_json(fpath):
    fpath.parent.mkdir(exist_ok=True, parents=True)

    if not fpath.exists():
        return None

    with fpath.open('r', encoding='utf-8') as f:
        return json.load(f)


def write_json(data, fpath):
    fpath.parent.mkdir(exist_ok=True, parents=True)

    # We want to ensure, that if there is an error during overwriting
    # (for example, not enough memory), there will be some backup file,
    # so that previous data will not be lost.
    backup_file = None
    if fpath.exists():
        backup_file = fpath.with_name(f'{fpath.stem}.backup.json')
        fpath.rename(backup_file)

    fpath.write_text('', 'utf-8') # we want to make file invalid JSON at this point
    with fpath.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=None, separators=(',', ':'))

    if backup_file:
        backup_file.unlink()
    print('written', fpath.stat().st_size, 'bytes', len(data), 'entries')


def iso_date_to_stamp(iso_date):
    assert iso_date.endswith('Z'), iso_date
    assert '.' not in iso_date, iso_date
    res = int(dateutil.parser.isoparse(iso_date).timestamp())
    assert stamp_to_iso_date(res) == iso_date
    return res


def stamp_to_utc_datetime(stamp):
    return datetime.datetime.fromtimestamp(
        stamp,
        tz=datetime.timezone.utc,
    )


def stamp_to_iso_date(stamp):
    assert type(stamp) is int, stamp
    res = stamp_to_utc_datetime(stamp).isoformat()
    assert res.endswith('+00:00') and res.count('+00:00') == 1, res
    res = res.replace('+00:00', 'Z')
    assert res.count('-') == 2 and res.count('T') == 1 and res.count(':') == 2, res
    assert '.' not in res
    return res


def get_md5_hash(obj):
    m = hashlib.md5()
    m.update(json.dumps(obj, ensure_ascii=False).encode('utf-8'))
    return m.hexdigest()


def is_in_jupyter(globals):
    return 'In' in globals


def get_cur_jupyter_cell_source(globals):
    res = globals['In'][-1] + '\n'
    repo_dir_substr = "repo_dir = Path('..').resolve()\n"
    assert repo_dir_substr in res
    repo_dir_subst = "repo_dir = Path('.').resolve()\n"
    res = res.replace(repo_dir_substr, repo_dir_subst)
    return res
