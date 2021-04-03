import src.config


class IpfsNotCachedException(Exception):
    pass


def validate_ipfs_uri(uri):
    assert type(uri) is str
    if uri.startswith('ipfs://'):
        assert uri.count('ipfs://') == 1
        ipfs_hash = uri.replace('ipfs://', '')
    else:
        ipfs_hash = uri
    assert len(ipfs_hash) == 46, len(ipfs_hash)
    assert ipfs_hash.startswith('Qm'), ipfs_hash
    return ipfs_hash


def get_ipfs_fpath(ipfs_uri, dir_name):
    ipfs_hash = validate_ipfs_uri(ipfs_uri)
    assert dir_name in ['ipfs0', 'ipfs1']
    dir_path = src.config.cache_dir / dir_name
    assert dir_path.is_dir()
    fpath = dir_path / ipfs_hash
    if not fpath.is_file():
        raise IpfsNotCachedException(ipfs_uri)
    return fpath


def get_previews(ipfs):
    ipfs = src.ipfs.validate_ipfs_uri(ipfs)
    res = {}
    original_fpath = src.config.ipfs1_dir / ipfs
    if original_fpath.exists():
        res['original'] = original_fpath
    for preview_config_id, preview_config in src.config.previews_config.items():
        dir_path = src.config.previews_dir / preview_config_id
        fpath = dir_path / (ipfs + preview_config['extension'])
        if fpath.exists():
            file_size = fpath.stat().st_size
            res[preview_config_id] = fpath if file_size > 0 else None
    return res


def make_media_db():
    from tqdm import tqdm
    import src.contracts.nft_state
    import src.contracts.state_utils

    nft_state_log = src.utils.read_json(src.config.nft_state_log_file)
    nft_state = src.contracts.nft_state.NFTState()
    nft_state_replayer = src.contracts.state_utils.StateReplayer(nft_state_log, nft_state)

    nft_state_replayer.replay_to_end()

    print('Making media db...')
    media_db = {}
    for token_id, token_db_entry in tqdm(list(nft_state.tokens.items())):
        try:
            info_fpath = src.ipfs.get_ipfs_fpath(token_db_entry['info_ipfs'], 'ipfs0')
        except Exception as e:
            print(token_id, token_db_entry)
            raise e

        token_info = src.utils.read_json(info_fpath)

        assert len(token_info['formats']) == 1
        assert token_info['formats'][0]['uri'] == token_info['artifactUri']

        ipfs_uri = src.ipfs.validate_ipfs_uri(token_info['artifactUri'])
        mime_type = token_info['formats'][0]['mimeType']

        db_entry = src.ipfs.get_previews(ipfs_uri)
        db_entry['ipfs'] = ipfs_uri
        db_entry['mime'] = mime_type

        if ipfs_uri in media_db:
            prev_mime_type = media_db[ipfs_uri]['mime']
            if prev_mime_type != mime_type:
                pass
                # print('duplicate', ipfs_uri, repr(prev_mime_type), repr(mime_type))

        media_db[ipfs_uri] = db_entry

    return media_db
