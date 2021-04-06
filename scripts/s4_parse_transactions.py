import sys
from pathlib import Path
repo_dir = Path(__file__).resolve().parent.parent
if str(repo_dir) not in sys.path:
    sys.path.append(str(repo_dir))


import src.utils
import config
import src.tr.iter
import src.contracts.nft_parser
import src.contracts.art_house_parser
import src.contracts.money_parser
import src.contracts.addrs_state


max_time = sys.argv[1] if len(sys.argv) >= 2 else '2100-01-01T00:00:00Z'


nft_ops = []
art_house_ops = []
money_trs = []
trs_info = []

addrs_state = src.contracts.addrs_state.AddrsState()
addrs_state = src.contracts.state_utils.StateRecorder(addrs_state)

print('Filtering NFT, ArtHouse and money ops...')

for tr in src.tr.iter.iter_tr():
    if tr['time'] >= max_time:
        continue

    for op in tr['ops']:
        op_type = '__' + op['type'] + '__'
        call = op.get('parameters', {}).get('call', op_type)
        addrs_state.apply_op(
            row_id=op['row_id'],
            sender=op['sender'],
            receiver=op.get('receiver'),
            volume=op['volume'],
            call=call,
        )

    tr_volume = 0
    for op in tr['ops']:
        op_hash = op['hash']

        if op['sender'] == config.name2addr['nft_contract']:
            raise Exception(f'Not expecting nft_contract to send messages: {op_hash}')

        if op.get('receiver') == config.name2addr['nft_contract']:
            nft_ops.append(op)

        if op.get('receiver') == config.name2addr['art_house_contract']:
            art_house_ops.append(op)

        if op['status'] != 'applied':
            continue

        assert op['volume'] >= 0
        tr_volume += op['volume']

    trs_info.append([
        tr['hash_c'],
        src.utils.iso_date_to_stamp(tr['time']),
        tr['ops'][0]['row_id'],
        tr['ops'][-1]['row_id'],
        tr['fpath'].name,
        tr_volume,
    ])

    if tr_volume > 0:
        money_trs.append(tr)


print('Writing addrs log...')

src.utils.write_json(addrs_state.log, config.addrs_state_log_file)

print('Writing transactions info...')

src.utils.write_json(trs_info, config.trs_info_file)


print('Parsing NFT ops...')

nft_log = src.contracts.nft_parser.parse_ops(nft_ops)

src.utils.write_json(
    nft_log,
    config.nft_state_log_file,
)

print('Parsing ArtHouse ops...')

ah_log = src.contracts.art_house_parser.parse_ops(art_house_ops)

src.utils.write_json(
    ah_log,
    config.ah_state_log_file,
)

print('Parsing money ops...')

money_log = src.contracts.money_parser.parse_trs(money_trs)

src.utils.write_json(
    money_log,
    config.money_state_log_file,
)
