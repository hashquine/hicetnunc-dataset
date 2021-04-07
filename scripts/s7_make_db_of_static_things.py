import sys
from pathlib import Path
repo_dir = Path(__file__).resolve().parent.parent
if str(repo_dir) not in sys.path:
    sys.path.append(str(repo_dir))


from tqdm import tqdm
from collections import Counter

from PIL import Image

import src.utils
import config
import src.ipfs
import src.tr.info_db
import src.contracts.state_utils
import src.contracts.nft_state
import src.contracts.art_house_state
import src.contracts.addrs_state
import src.contracts.money_state


if __name__ == '__main__':

    print('Reading parsed logs...')

    nft_state_log = src.utils.read_json(config.nft_state_log_file)
    nft_state = src.contracts.nft_state.NFTState()
    nft_state_replayer = src.contracts.state_utils.StateReplayer(nft_state_log, nft_state)

    ah_state_log = src.utils.read_json(config.ah_state_log_file)
    ah_state = src.contracts.art_house_state.ArtHouseState()
    ah_state_replayer = src.contracts.state_utils.StateReplayer(ah_state_log, ah_state)

    money_state_log = src.utils.read_json(config.money_state_log_file)
    money_state = src.contracts.money_state.MoneyState()
    money_state_replayer = src.contracts.state_utils.StateReplayer(money_state_log, money_state)

    addrs_state_log = src.utils.read_json(config.addrs_state_log_file)
    addrs_state = src.contracts.addrs_state.AddrsState()
    addrs_state_replayer = src.contracts.state_utils.StateReplayer(addrs_state_log, addrs_state)

    tr_info_db = src.tr.info_db.TrInfoDB()

    nft_state_replayer.replay_to_end()
    ah_state_replayer.replay_to_end()
    money_state_replayer.replay_to_end()
    addrs_state_replayer.replay_to_end()


    print('Making tokens db...')

    tokens_db = {}
    swaps_db = {}

    assert set(nft_state.tokens.keys()) == set(ah_state.tokens.keys())

    for token_id, nft_token_info in nft_state.tokens.items():
        tokens_db[str(token_id)] = {
            'token_id': token_id,
            'mint_tokens_receiver': nft_token_info['tokens_receiver'],
            'info_ipfs': nft_token_info['info_ipfs'],
            'mint_count': nft_token_info['mint_count'],
            'mint_row_id': nft_token_info['mint_row_id'],
        }

    for token_id, ah_token_info in tqdm(ah_state.tokens.items()):
        db_entry = tokens_db[str(token_id)]
        db_entry['royalties'] = ah_token_info['royalties']
        db_entry['mint_ah_row_id'] = ah_token_info['mint_ah_row_id']
        db_entry['mint_sender'] = ah_token_info['mint_sender']

        assert db_entry['mint_tokens_receiver'] == ah_token_info['tokens_receiver']
        assert db_entry['mint_count'] == ah_token_info['mint_count']
        assert db_entry['info_ipfs'] == ah_token_info['info_ipfs']

        nft_mint_tr = tr_info_db.get_full_tr_by_row_id(db_entry['mint_row_id'])
        ah_mint_tr = tr_info_db.get_full_tr_by_row_id(ah_token_info['mint_ah_row_id'])
        assert nft_mint_tr == ah_mint_tr


    print('Making swaps db...')

    for swap_id, ah_swap_info in tqdm(list(ah_state.swaps.items())):
        assert str(ah_swap_info['token_id']) in tokens_db
        ah_swap_op = tr_info_db.get_full_tr_by_row_id(ah_swap_info['created_row_id'], return_op=True)
        swaps_db[str(swap_id)] = {
            'swap_id': swap_id,
            'swap_sender': ah_swap_info['swap_sender'],
            'created_row_id': ah_swap_info['created_row_id'],
            'token_id': ah_swap_info['token_id'],
            'price': ah_swap_info['price'],
            'initial_count': ah_swap_info['initial_count'],
        }


    print('Populating tokens with info...')

    token_info_fields_cnt = Counter()

    for token_id, token_db_entry in tqdm(tokens_db.items()):
        info_ipfs_fpath = src.ipfs.get_ipfs_fpath(token_db_entry['info_ipfs'], 'ipfs0')
        token_info = src.utils.read_json(info_ipfs_fpath)

        for field in token_info:
            token_info_fields_cnt[field] += 1
        token_info_keys = set(token_info.keys())
        assert token_info_keys.issubset({
            'artifactUri', 'creators', 'decimals', 'description', 'displayUri', 'formats',
            'isBooleanAmount', 'name', 'shouldPreferSymbol', 'symbol', 'tags', 'thumbnailUri',
        })

        if int(token_id) == 152:
            assert 'isBooleanAmount' not in token_info
        elif int(token_id) <= 352:
            assert token_info['isBooleanAmount'] == (token_db_entry['mint_count'] == 1)
        else:
            assert token_info['isBooleanAmount'] is False

        if int(token_id) <= 154:
            assert 'shouldPreferSymbol' not in token_info
        else:
            assert token_info['shouldPreferSymbol'] is False

        if 'displayUri' in token_info:
            assert int(token_id) >= 11000
            if token_info['displayUri']:
                assert src.ipfs.validate_ipfs_uri(token_info['displayUri'])

        assert token_info['decimals'] == 0
        assert token_info['symbol'] == 'OBJKT'

        assert len(token_info['formats']) == 1
        assert token_info['formats'][0]['uri'] == token_info['artifactUri']
        assert src.ipfs.validate_ipfs_uri(token_info['formats'][0]['uri'])
        assert len(token_info['creators']) == 1

        for tag in token_info['tags']:
            for ch in [' ', '\n', '\t']:
                assert ch not in tag, (ch, tag)

        if token_info['creators'][0] != token_db_entry['mint_sender']:
            assert token_id == '5571' or token_info['creators'][0] in ['', None]

        if token_info['thumbnailUri'] != 'ipfs://QmNrhZHUaEqxhyLfqoq1mtHSipkWHeT31LNHb1QEbDHgnc':
            token_db_entry['thumbnail_ipfs'] = src.ipfs.validate_ipfs_uri(token_info['thumbnailUri'])

        token_db_entry['artifact_mime'] = token_info['formats'][0]['mimeType']
        token_db_entry['artifact_ipfs'] = token_info['formats'][0]['uri']
        token_db_entry['meta_creator'] = str(token_info['creators'][0])
        token_db_entry['display_uri_ipfs'] = token_info.get('displayUri', '') or ''
        token_db_entry['tags'] = '\t'.join(token_info['tags'])
        token_db_entry['name'] = token_info['name']
        token_db_entry['description'] = token_info['description']


    print('Adding artifact file size and preview dimensions data...')

    previews_dimensions_cache = src.utils.read_json(config.previews_dimensions_cache_file) or {}

    not_in_cache_count = 0
    for token_id, token_db_entry in tqdm(tokens_db.items()):
        try:
            artifact_fpath = src.ipfs.get_ipfs_fpath(token_db_entry['artifact_ipfs'], 'ipfs1')
            token_db_entry['artifact_file_size'] = artifact_fpath.stat().st_size
        except src.ipfs.IpfsNotCachedException:
            not_in_cache_count += 1

        ipfs_id = src.ipfs.validate_ipfs_uri(token_db_entry['artifact_ipfs'])
        preview_fpath = config.previews_dir / 'ps_1024x1024' / (ipfs_id + '.jpeg')
        if preview_fpath.exists() and preview_fpath.stat().st_size > 0:
            if ipfs_id not in previews_dimensions_cache:
                try:
                    im = Image.open(preview_fpath)
                    width, height = im.size
                    previews_dimensions_cache[ipfs_id] = {
                        'preview_width': width,
                        'preview_height': height,
                    }
                except Exception:
                    print(f'Cannot read image {preview_fpath}')
                    previews_dimensions_cache[ipfs_id] = {
                        'preview_width': -1,
                        'preview_height': -1,
                    }

            dimensions_cache_entry = previews_dimensions_cache[ipfs_id]
            token_db_entry['artifact_preview_width'] = dimensions_cache_entry['preview_width']
            token_db_entry['artifact_preview_height'] = dimensions_cache_entry['preview_height']

        if token_db_entry['display_uri_ipfs'] != '':
            try:
                display_uri_fpath = src.ipfs.get_ipfs_fpath(token_db_entry['display_uri_ipfs'], 'ipfs1')
                token_db_entry['display_uri_file_size'] = display_uri_fpath.stat().st_size
            except src.ipfs.IpfsNotCachedException:
                not_in_cache_count += 1
        else:
            token_db_entry['display_uri_file_size'] = -1

    print('Number of tokens without downloaded artifacts:', not_in_cache_count)

    src.utils.write_json(previews_dimensions_cache, config.previews_dimensions_cache_file)

    print('Making address db...')

    addrs_db = {}
    for addr, addr_entry in addrs_state.addrs.items():
        addrs_db[addr] = {
            'address': addr,
            'first_op_row_id': addr_entry['first_op_row_id'],
            'first_op_has_reveal': addr_entry['first_op_has_reveal'],
            'in_op_count': addr_entry['in_op_count'],
            'out_op_count': addr_entry['out_op_count'],
            'money_received': addr_entry['money_received'],
            'money_sent': addr_entry['money_sent'],
        }

    accounts_metadata = src.utils.read_json(config.tzktio_accounts_metadata_file)

    url_prefixes = {
        'https://www.facebook.com/',
        'www.facebook.com/',
        'https://facebook.com/',
        'https://www.instagram.com/',
        'https://instagram.com/',
        'https://web.facebook.com/',
    }

    unknown_prefixes = set()
    for addr, addr_meta in accounts_metadata.items():
        if addr_meta is None:
            continue
        if addr not in addrs_db:
            continue
        db_entry = addrs_db[addr]
        for field, field_val in addr_meta.items():
            if field in {
                'twitter', 'site', 'email', 'instagram', 'github', 'telegram',
                'reddit', 'facebook', 'logo', 'description'
            }:
                orig_field_val = field_val
                field_val = field_val.strip()
                if field_val.endswith('/'):
                    field_val = field_val[:-1]
                if field not in {'site', 'email', 'reddit', 'logo', 'description'} and '/' in field_val:
                    prefix = '/'.join(field_val.lower().split('/')[:-1]) + '/'
                    if prefix in url_prefixes:
                        field_val = field_val[len(prefix):]
                    else:
                        unknown_prefixes.add(prefix)
                db_entry[f'tzkt_info_{field}'] = field_val
            elif field == 'alias':
                db_entry['tzkt_info_name'] = field_val

    if unknown_prefixes:
        print(f'Unknown prefixes: {unknown_prefixes}')

    print('Writing result data...')

    src.utils.write_json(tokens_db, config.tokens_db_json_file)
    src.utils.write_json(swaps_db, config.swaps_db_json_file)
    src.utils.write_json(addrs_db, config.addrs_db_json_file)
