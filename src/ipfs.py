class IpfsNotCachedException(Exception):
    pass


def validate_ipfs_uri(uri):
    assert type(uri) is str
    assert uri.startswith('ipfs://')
    assert uri.count('ipfs://') == 1
    ipfs_hash = uri.replace('ipfs://', '')
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
        raise IpfsNotCachedException()
    return fpath
