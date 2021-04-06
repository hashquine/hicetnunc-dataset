import sys
from pathlib import Path
repo_dir = Path(__file__).resolve().parent.parent
if str(repo_dir) not in sys.path:
    sys.path.append(str(repo_dir))


import requests
from tqdm import tqdm

import src.utils
import config
import src.ipfs


preview_server_urls = [
    'http://127.0.0.1:8000',
    'http://host.docker.internal:8000',
]


def make_ps_preview(read_fpath, write_fpath, mime, resolution):
    width, height = resolution

    try:
        req = requests.post(f'{preview_server_url}/preview/{width}x{height}', files={
            'file': ('file', read_fpath.read_bytes(), mime)
        })
    except requests.exceptions.ConnectionError:
        raise Exception(
            'Ensure that there is a fpurchess/preview-service docker service running on http://127.0.0.1:8000'
        )

    if req.status_code != 200:
        print('Cannot convert ', read_fpath, mime)
        print(req.text)
        write_fpath.write_bytes(b'')
    else:
        write_fpath.write_bytes(req.content)



if __name__ == '__main__':

    for preview_server_url in preview_server_urls:
        try:
            print(f'Trying to connect to {preview_server_url}...', end=' ')
            sys.stdout.flush()
            req = requests.get(preview_server_url)
            print('ok')
            break
        except requests.exceptions.ConnectionError:
            print('fail')
    else:
        raise Exception(
            'Ensure that there is a fpurchess/preview-service docker service running on http://127.0.0.1:8000'
        )

    for preview_config_id, preview_config in config.previews_config.items():
        media_db = src.ipfs.make_media_db()

        print(preview_config_id, '...')
        dir_path = config.previews_dir / preview_config_id
        dir_path.mkdir(exist_ok=True)

        for media_db_entry in tqdm(list(media_db.values())):
            ipfs = media_db_entry['ipfs']
            out_fpath = dir_path / (ipfs + preview_config['extension'])
            if out_fpath.exists():
                continue

            if preview_config['type'] == 'render':
                in_fpath = media_db_entry.get('original')
                if not in_fpath:
                    continue

                make_ps_preview(
                    in_fpath,
                    out_fpath,
                    media_db_entry['mime'],
                    preview_config['resolution'],
                )

            elif preview_config['type'] == 'thumb':
                in_fpath = None
                for other_preview_config_id in preview_config['sources']:
                    in_fpath_candidate = media_db_entry.get(other_preview_config_id)
                    if in_fpath_candidate:
                        in_fpath = in_fpath_candidate

                if in_fpath is None:
                    continue

                make_ps_preview(
                    in_fpath,
                    out_fpath,
                    'image/jpeg',
                    preview_config['resolution'],
                )
