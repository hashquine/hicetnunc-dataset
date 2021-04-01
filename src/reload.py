import sys
from pathlib import Path
repo_dir = Path(__file__).parent.parent.resolve()
if str(repo_dir) not in sys.path:
    sys.path.append(str(repo_dir))


def reload():
    import importlib
    import src.reload
    src.reload._reload()


def _reload():
    "Helper function for developing with Jupyter notebook"

    import importlib

    import src
    import src.utils
    import src.config
    import src.ipfs
    import src.datasets
    import src.formatters.md_fields_schema
    import src.tr.iter
    import src.tr.utils
    import src.tr.info_db
    import src.contracts.state_utils
    import src.contracts.nft_state
    import src.contracts.nft_parser
    import src.contracts.art_house_state
    import src.contracts.art_house_parser
    import src.contracts.money_state
    import src.contracts.money_parser
    import src.contracts.addrs_state

    importlib.reload(src.utils)
    importlib.reload(src.config)
    importlib.reload(src.ipfs)
    importlib.reload(src.datasets)
    importlib.reload(src.formatters.md_fields_schema)
    importlib.reload(src.tr.utils)
    importlib.reload(src.tr.info_db)
    importlib.reload(src.tr.iter)
    importlib.reload(src.contracts.state_utils)
    importlib.reload(src.contracts.nft_state)
    importlib.reload(src.contracts.nft_parser)
    importlib.reload(src.contracts.art_house_state)
    importlib.reload(src.contracts.art_house_parser)
    importlib.reload(src.contracts.money_state)
    importlib.reload(src.contracts.money_parser)
    importlib.reload(src.contracts.addrs_state)


if __name__ == '__main__':
    reload()
