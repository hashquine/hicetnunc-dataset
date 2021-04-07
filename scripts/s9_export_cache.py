import sys
from pathlib import Path
repo_dir = Path(__file__).resolve().parent.parent
if str(repo_dir) not in sys.path:
    sys.path.append(str(repo_dir))


import shutil
from tqdm import tqdm

import config
import src.utils


addrs_ds = src.utils.read_json(config.dataset_dir / 'addrs.json')
tokens_ds = src.utils.read_json(config.dataset_dir / 'tokens.json')

ecd = config.export_cache_dir

# if ecd.exists():
#     print(f'Removing {ecd} directory...')
#     shutil.rmtree(ecd)

ecd.mkdir(exist_ok=True)

(ecd / 'accounts_metadata').mkdir(exist_ok=True)
(ecd / 'accounts_metadata' / 'logos').mkdir(exist_ok=True)
(ecd / 'ipfs0').mkdir(exist_ok=True)
(ecd / 'previews').mkdir(exist_ok=True)
(ecd / 'previews' / 'thumbs_256x256').mkdir(exist_ok=True)
(ecd / 'transactions' / config.transactions_dir.name).mkdir(exist_ok=True, parents=True)

print('Copying logos...')

for addr_ds_entry in tqdm(addrs_ds.values()):
    if addr_ds_entry['ban_status'] != '':
        continue
    logo_file = config.tzktio_accounts_logos_dir / (addr_ds_entry['address'] + '.png')
    target_logo_file = ecd / 'accounts_metadata' / 'logos' / logo_file.name
    if logo_file.exists() and not target_logo_file.exists():
        shutil.copy(logo_file, target_logo_file)

print('Copying tokens 256x256 thumbs...')

for token_ds_entry in tqdm(tokens_ds.values()):
    if token_ds_entry['ban_status'] != '':
        continue
    token_preview_file = config.previews_dir / 'thumbs_256x256' / (token_ds_entry['artifact_ipfs'] + '.jpeg')
    target_token_preview_file = ecd / 'previews' / 'thumbs_256x256' / token_preview_file.name
    if token_preview_file.exists() and not target_token_preview_file.exists():
        shutil.copy(token_preview_file, target_token_preview_file)

print('Copying tokens metadata...')

for token_ds_entry in tqdm(tokens_ds.values()):
    token_ipfs0_file = config.ipfs0_dir / token_ds_entry['info_ipfs']
    if token_preview_file.exists():
        shutil.copy(token_ipfs0_file, ecd / 'ipfs0' / token_ipfs0_file.name)

print('Copying single files...')

shutil.copy(
    config.tzktio_accounts_metadata_file,
    ecd / 'accounts_metadata' / config.tzktio_accounts_metadata_file.name,
)

shutil.copy(
    config.previews_dimensions_cache_file,
    ecd / 'previews' / config.previews_dimensions_cache_file.name,
)

print('Copying transactions...')

for tr_file in tqdm(list(config.transactions_dir.iterdir())):
    if 'invalid' in tr_file.name:
        continue
    shutil.copy(tr_file, ecd / 'transactions' / tr_file.parent.name / tr_file.name)


print('Making dataset.zip archive...')

shutil.make_archive(config.export_dataset_archive_file.with_suffix(''), 'zip', config.dataset_dir)


ewd = config.website_repo_dir / 'hicetnunc'

if ewd.is_dir():
    print('WEBSITE: Copying logos...')
    (ewd / 'user_logos').mkdir(exist_ok=True)

    for addr_ds_entry in tqdm(addrs_ds.values()):
        if addr_ds_entry['ban_status'] != '':
            continue
        logo_file = config.tzktio_accounts_logos_dir / (addr_ds_entry['address'] + '.png')
        target_logo_file = ewd / 'user_logos' / logo_file.name
        if logo_file.exists() and not target_logo_file.exists():
            shutil.copy(logo_file, target_logo_file)

if ewd.is_dir():
    print('WEBSITE: Copying tokens 256x256 thumbs...')
    (ewd / 'token_thumbs').mkdir(exist_ok=True)
    for token_ds_entry in tqdm(tokens_ds.values()):
        if token_ds_entry['ban_status'] != '':
            continue
        token_preview_file = config.previews_dir / 'thumbs_256x256' / (token_ds_entry['artifact_ipfs'] + '.jpeg')
        target_token_preview_file = ewd / 'token_thumbs' / (token_ds_entry['token_id'] + '.jpeg')
        if token_preview_file.exists() and not target_token_preview_file.exists():
            shutil.copy(token_preview_file, target_token_preview_file)


print('Making cache.zip archive...')

shutil.make_archive(config.export_cache_archive_file.stem, 'zip', ecd)
