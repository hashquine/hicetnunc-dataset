import sys
from pathlib import Path
repo_dir = Path(__file__).parent.parent.resolve()
if str(repo_dir) not in sys.path:
    sys.path.append(str(repo_dir))

import src.utils
import src.config
import src.tr.iter
import src.contracts.nft_parser
import src.contracts.art_house_parser
import src.contracts.money_parser


nft_ops = []
art_house_ops = []
money_trs = []
trs_info = []

print('Filtering NFT, ArtHouse and money ops...')

for tr in src.tr.iter.iter_tr():
    trs_info.append([
        tr['hash'],
        src.utils.iso_date_to_stamp(tr['time']),
        tr['ops'][0]['row_id'],
        tr['ops'][-1]['row_id'],
        tr['fpath'].name,
    ])

    tr_volume = 0
    for op in tr['ops']:
        op_hash = op['hash']

        if op['sender'] == src.config.name2addr['nft_contract']:
            raise Exception(f'Not expecting nft_contract to send messages: {op_hash}')

        if op.get('receiver') == src.config.name2addr['nft_contract']:
            nft_ops.append(op)

        if op.get('receiver') == src.config.name2addr['art_house_contract']:
            art_house_ops.append(op)

        if op['status'] != 'applied':
            continue

        assert op['volume'] >= 0
        tr_volume += op['volume']

    if tr_volume > 0:
        money_trs.append(tr)


print('Writing transactions info...')

src.utils.write_json(trs_info, src.config.trs_info_file)


print('Parsing NFT ops...')

nft_log = src.contracts.nft_parser.parse_ops(nft_ops)

src.utils.write_json(
    nft_log,
    src.config.nft_state_log_file,
)

print('Parsing ArtHouse ops...')

ah_log = src.contracts.art_house_parser.parse_ops(art_house_ops)

src.utils.write_json(
    ah_log,
    src.config.ah_state_log_file,
)

print('Parsing money ops...')

money_log = src.contracts.money_parser.parse_trs(money_trs)

src.utils.write_json(
    money_log,
    src.config.money_state_log_file,
)
