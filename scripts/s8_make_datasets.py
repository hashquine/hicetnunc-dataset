import sys
from pathlib import Path
repo_dir = Path(__file__).resolve().parent.parent
if str(repo_dir) not in sys.path:
    sys.path.append(str(repo_dir))


from collections import defaultdict
from tqdm import tqdm
import requests

import src.utils
import config
import src.ipfs
import src.datasets
import src.tr.info_db



from collections import Counter, defaultdict


def make_transactions_index():
    transactions_index = defaultdict(lambda: {
        'nft_log_entry': None,
        'ah_log_entry': None,
        'money_log_entry': None,
        'created_swap': None,
        'created_token': None,
        'tr_info': None,
    })

    for entries, row_id_field, entry_field in [
        (nft_state_log, 'row_id', 'nft_log_entry'),
        (ah_state_log, 'row_id', 'ah_log_entry'),
        (money_state_log, 'row_id', 'money_log_entry'),
        (swaps_db.values(), 'created_row_id', 'created_swap'),
        (tokens_db.values(), 'mint_ah_row_id', 'created_token'),
    ]:
        for entry in entries:
            tr_info = tr_info_db.get_tr_info_by_row_id(entry[row_id_field])
            tr_hashc = tr_info['hashc']
            assert transactions_index[tr_hashc][entry_field] is None
            transactions_index[tr_hashc][entry_field] = entry
            transactions_index[tr_hashc]['tr_info'] = tr_info
            entry['tr_index_entry'] = transactions_index[tr_hashc]

    return transactions_index


def check_ah_logs():
    for ah_log_entry in ah_state_log:
        entry_method = ah_log_entry['method']
        nft_log_entry = ah_log_entry['tr_index_entry']['nft_log_entry']
        if entry_method in ['apply_collect', 'apply_swap', 'apply_cancel_swap']:
            assert nft_log_entry['method'] == 'apply_transfer'
        elif entry_method == 'apply_mint':
            assert nft_log_entry['method'] == 'apply_mint'
        else:
            assert False, entry_method


print('Reading state logs...')

tokens_db = src.utils.read_json(config.tokens_db_json_file)
swaps_db = src.utils.read_json(config.swaps_db_json_file)
addrs_db = src.utils.read_json(config.addrs_db_json_file)

nft_state_log = src.utils.read_json(config.nft_state_log_file)
ah_state_log = src.utils.read_json(config.ah_state_log_file)
money_state_log = src.utils.read_json(config.money_state_log_file)

tr_info_db = src.tr.info_db.TrInfoDB()


print('Join contracts logs with transactions...')

transactions_index = make_transactions_index()

print('Checking, that every art house log entry has corresponding nft log entry...')

check_ah_logs()

print('Getting banned addrs and objkts...')

banned_objkts = requests.get('https://raw.githubusercontent.com/hicetnunc2000/hicetnunc/main/filters/o.json').json()
banned_addrs = requests.get('https://raw.githubusercontent.com/hicetnunc2000/hicetnunc/main/filters/w.json').json()


def init_tokens_ds():
    tokens_ds = {}
    for token_db_entry in tokens_db.values():
        if 'artifact_file_size' not in token_db_entry:
            token_id = token_db_entry['token_id']
            print(f'No artifact file size for {token_id}')
        token_db_entry['state'] = 'NOT_EXISTS'
        token_db_entry['own_counts_by_address'] = None
        token_db_entry['own_counts_by_category'] = None
        token_db_entry['author_swap_balance'] = 0
        token_db_entry['author_other_balance'] = 0
        tokens_ds[str(token_db_entry['token_id'])] = {
            'token_id': str(token_db_entry['token_id']),
            'issuer': token_db_entry['mint_sender'],
            'mint_count': token_db_entry['mint_count'],
            'mint': src.datasets.TrEvent(token_db_entry['mint_row_id']),
            'artifact_ipfs': src.ipfs.validate_ipfs_uri(token_db_entry['artifact_ipfs']) if token_db_entry['artifact_ipfs'] else '',
            'artifact_mime': token_db_entry['artifact_mime'],
            'artifact_file_size': token_db_entry.get('artifact_file_size', -1),
            'artifact_preview_width': token_db_entry.get('artifact_preview_width', -1),
            'artifact_preview_height': token_db_entry.get('artifact_preview_height', -1),
            'info_title': token_db_entry['name'],
            'info_description': token_db_entry['description'],
            'info_tags': ' '.join(token_db_entry['tags'].split('\t')),
            'ban_status': 'banned' if token_db_entry['token_id'] in banned_objkts else '',
            'author_sold_prices': src.datasets.FloatSet(),
            'secondary_sold_prices': src.datasets.FloatSet(),
            'author_sold_prices': src.datasets.FloatSet(),
            'available_prices': src.datasets.FloatSet(),
            'burn_count': 0,
            'author_owns_count': 0,
            'other_own_count': 0,
            'author_sent_count': 0,
            'info_ipfs': src.ipfs.validate_ipfs_uri(token_db_entry['info_ipfs']),
            'display_uri_ipfs': (
                src.ipfs.validate_ipfs_uri(token_db_entry['display_uri_ipfs'])
                if token_db_entry['display_uri_ipfs'] else ''
            ),
            'royalties': token_db_entry['royalties'] / 10,
            'mint_tokens_receiver': token_db_entry['mint_tokens_receiver'],
            'info_creator': '' if token_db_entry['meta_creator'] in ['None', '', None] else token_db_entry['meta_creator'],
            'mint_ah_row_id': token_db_entry['mint_ah_row_id'],
        }
    return tokens_ds


def init_addrs_ds():
    addrs_ds = {}
    for addr_db_entry in addrs_db.values():
        addrs_ds[addr_db_entry['address']] = {
            'address': addr_db_entry['address'],
            'first_action': src.datasets.TrEvent(addr_db_entry['first_op_row_id']),
            'tzkt_info_name': addr_db_entry.get('tzkt_info_name', ''),
            'tzkt_info_twitter': addr_db_entry.get('tzkt_info_twitter', ''),
            'tzkt_info_email': addr_db_entry.get('tzkt_info_email', ''),
            'tzkt_info_instagram': addr_db_entry.get('tzkt_info_instagram', ''),
            'tzkt_info_site': addr_db_entry.get('tzkt_info_site', ''),
            'tzkt_info_description': addr_db_entry.get('tzkt_info_description', ''),
            'tzkt_info_logo': addr_db_entry.get('tzkt_info_logo', ''),
            'tzkt_info_github': addr_db_entry.get('tzkt_info_github', ''),
            'tzkt_info_telegram': addr_db_entry.get('tzkt_info_telegram', ''),
            'tzkt_info_facebook': addr_db_entry.get('tzkt_info_facebook', ''),
            'tzkt_info_reddit': addr_db_entry.get('tzkt_info_reddit', ''),
            'ban_status': 'banned' if addr_db_entry['address'] in banned_addrs else '',
            'mint_count': 0,
            'bought_prices': src.datasets.FloatSet(),
            'author_sold_prices': src.datasets.FloatSet(),
            'secondary_sold_prices': src.datasets.FloatSet(),
            'available_prices': src.datasets.FloatSet(),
            'in_op_count': addr_db_entry['in_op_count'],
            'out_op_count': addr_db_entry['out_op_count'],
            'money_received': addr_db_entry['money_received'],
            'money_sent': addr_db_entry['money_sent'],
            # 'first_op_has_reveal': int(addr_db_entry['first_op_has_reveal']),
        }
    return addrs_ds


def init_swaps_ds():
    swaps_ds = {}
    for swap_db_entry in swaps_db.values():
        swap_db_entry['state'] = 'NOT_EXISTS'
        token_db_entry = tokens_db[str(swap_db_entry['token_id'])]
        swaps_ds[str(swap_db_entry['swap_id'])] = {
            'swap_id': str(swap_db_entry['swap_id']),
            'token_id': str(swap_db_entry['token_id']),
            'price': swap_db_entry['price'] / 1e6,
            'total_count': swap_db_entry['initial_count'],
            'created': src.datasets.TrEvent(swap_db_entry['created_row_id']),
            'closed': src.datasets.TrEvent(),
            'by_author': int(swap_db_entry['swap_sender'] == token_db_entry['mint_sender']),
            'created_by': swap_db_entry['swap_sender'],
            'sold_count': 0,
            'available_count': 0,
            'returned_count': 0,
            'sold_price_sum': 0,
        }
    return swaps_ds


def get_addr_category(addr, author):
    if addr == config.name2addr['art_house_contract']:
        return 'swap'
    elif addr == config.name2addr['burn']:
        return 'burn'
    elif addr == author:
        return 'author'
    elif addr.startswith('KT'):
        return 'ext'
    else:
        return 'user'


print('Initializing datasets...')

tokens_ds = init_tokens_ds()
addrs_ds = init_addrs_ds()
swaps_ds = init_swaps_ds()
sells_ds = {}
transfers_ds = {}


def process_mint(tr_index_entry):
    token_id = nft_log_entry['token_id']
    token_count = nft_log_entry['count']
    tokens_receiver = nft_log_entry['tokens_receiver']

    meta_creator = created_token_db_entry['meta_creator']
    assert created_token_db_entry['state'] == 'NOT_EXISTS'
    created_token_db_entry['state'] = 'CREATED'
    assert created_token_db_entry['own_counts_by_address'] == None
    created_token_db_entry['own_counts_by_address'] = Counter({
        tokens_receiver: token_count,
    })

    author = ah_log_entry['mint_sender']
    assert ah_log_entry['count'] == nft_log_entry['count']
    assert ah_log_entry['tokens_receiver'] == nft_log_entry['tokens_receiver']
    assert ah_log_entry['tokens_receiver'] == created_token_db_entry['mint_tokens_receiver']
    assert ah_log_entry['method'] == 'apply_mint'

    addrs_ds[author]['mint_count'] += token_count

    receiver_category = get_addr_category(tokens_receiver, author)
    assert receiver_category in ['author', 'user']

    assert created_token_db_entry['own_counts_by_category'] == None
    created_token_db_entry['own_counts_by_category'] = Counter({
        receiver_category: token_count,
    })

    assert tr_volume == 0
    assert created_swap_db_entry is None
    assert money_log_entry is None

    transfers_ds[str(nft_log_entry['row_id'])] = {
        'tr': src.datasets.TrEvent(nft_log_entry['row_id']),
        'category': f'mint->{receiver_category}',
        'token_id': str(token_id),
        'price': 0,
        'count': token_count,
        'swap_id': '',
        'sender': '',
        'receiver': nft_log_entry['tokens_receiver'],
        'method': 'mint_OBJKT',
    }


def post_process():
    for token_db_entry in tokens_db.values():
        assert token_db_entry['state'] == 'CREATED'
        token_ds_entry = tokens_ds[str(token_db_entry['token_id'])]

        author_ds_entry = addrs_ds[token_ds_entry['issuer']]
        if author_ds_entry['ban_status'] == 'banned' and token_ds_entry['ban_status'] == '':
            token_ds_entry['ban_status'] = 'author_banned'
        if token_ds_entry['ban_status'] == 'banned' and author_ds_entry['ban_status'] == '':
            author_ds_entry['ban_status'] = 'some_tokens_banned'

        token_ds_entry['author_owns_count'] = token_db_entry['own_counts_by_category']['author']
        token_ds_entry['burn_count'] = token_db_entry['own_counts_by_category']['burn']
        token_ds_entry['other_own_count'] = token_db_entry['own_counts_by_category']['user']
        token_ds_entry['other_own_count'] += token_db_entry['own_counts_by_category']['ext']

        token_ds_entry['author_sent_count'] = max(0, token_db_entry['author_other_balance']) + \
                                              min(0, token_db_entry['author_swap_balance'])

        assert token_ds_entry['author_sent_count'] >= 0

        del token_ds_entry, token_db_entry

    for swap_db_entry in swaps_db.values():
        swap_ds_entry = swaps_ds[str(swap_db_entry['swap_id'])]
        swap_ds_entry['available_count'] = max(0, swap_ds_entry['available_count'])
        swap_ds_entry['returned_count'] = max(0, swap_ds_entry['returned_count'])
        token_ds_entry = tokens_ds[str(swap_db_entry['token_id'])]
        token_db_entry = tokens_db[str(swap_db_entry['token_id'])]
        author_ds_entry = addrs_ds[str(token_ds_entry['issuer'])]

        if swap_db_entry['state'] == 'ACTIVE':
            token_ds_entry['available_prices'].add(swap_ds_entry['price'], swap_ds_entry['available_count'])
            author_ds_entry['available_prices'].add(swap_ds_entry['price'], swap_ds_entry['available_count'])
        else:
            assert swap_db_entry['state'] == 'CLOSED', (swap_db_entry['state'], swap_db_entry['swap_id'])

        del token_ds_entry, token_db_entry

    for token_db_entry in tokens_db.values():
        token_ds_entry = tokens_ds[str(token_db_entry['token_id'])]

        # assert token_ds_entry['mint_count'] == token_ds_entry['author_owns_count'] + \
        #        token_ds_entry['available_prices'].count('all') + token_ds_entry['other_own_count'] + \
        #        token_ds_entry['burn_count'], token_db_entry['token_id']

        # assert token_ds_entry['author_sent_count'] <= token_ds_entry['other_own_count'] + \
        #        token_ds_entry['available_prices'].count('all'), token_db_entry['token_id']

        del token_ds_entry, token_db_entry

    # TODO: check assertions


for nft_log_entry in nft_state_log:
    nft_log_entry_method = nft_log_entry['method']
    assert nft_log_entry_method in ['apply_transfer', 'apply_mint'], nft_log_entry_method
    tr_index_entry = nft_log_entry['tr_index_entry']

    ah_log_entry = tr_index_entry['ah_log_entry']
    money_log_entry = tr_index_entry['money_log_entry']
    created_swap_db_entry = tr_index_entry['created_swap']
    created_token_db_entry = tr_index_entry['created_token']
    tr_info = tr_index_entry['tr_info']
    tr_volume = tr_info['volume']

    if nft_log_entry_method == 'apply_mint':
        process_mint(tr_index_entry)
        continue

    assert nft_log_entry_method == 'apply_transfer'

    for tx in nft_log_entry['txs']:
        assert created_token_db_entry is None

        tx_from = tx['from']
        tx_to = tx['to']
        tx_token_id = int(tx['token_id'])
        tx_count = int(tx['count'])

        if tx_count == 0:
            continue
        if tx_from == tx_to:
            continue

        token_db_entry = tokens_db[str(tx_token_id)]
        token_ds_entry = tokens_ds[str(tx_token_id)]
        author = token_ds_entry['issuer']
        author_db_entry = addrs_db[author]
        author_ds_entry = addrs_ds[author]

        sender_category = get_addr_category(tx_from, author)
        receiver_category = get_addr_category(tx_to, author)

        price = 0
        swap_id = ''
        method = ''

        if ah_log_entry and ah_log_entry['method'] == 'apply_cancel_swap':
            assert sender_category == 'swap'
            assert receiver_category in ['author', 'user']
            assert tr_volume == 0

            swap_id = str(ah_log_entry['swap_id'])

            swap_db_entry = swaps_db[str(ah_log_entry['swap_id'])]
            swap_db_entry['state'] = 'CLOSED'

            swap_ds_entry = swaps_ds[str(ah_log_entry['swap_id'])]
            swap_ds_entry['closed'].set_row_id(ah_log_entry['row_id'])

            swap_ds_entry['returned_count'] = swap_ds_entry['available_count']
            swap_ds_entry['available_count'] = 0

            del swap_db_entry, swap_ds_entry

        elif sender_category == 'swap':
            assert ah_log_entry['method'] == 'apply_collect'
            assert receiver_category in ['author', 'user']
            assert tr_volume >= 0

            swap_id = str(ah_log_entry['swap_id'])

            swap_ds_entry = swaps_ds[str(ah_log_entry['swap_id'])]
            swap_db_entry = swaps_db[str(ah_log_entry['swap_id'])]

            assert swap_db_entry['state'] == 'ACTIVE'
            assert created_swap_db_entry is None
            price_mutez = swap_db_entry['price']
            price = price_mutez / 1e6

            assert ah_log_entry['count'] == tx_count
            assert len(nft_log_entry['txs']) == 1

            if swap_db_entry['price'] == 0:
                assert money_log_entry is None
                money_log_entry = {
                    'royalties': 0,
                    'comission': 0,
                    'seller_income': 0,
                }

            else:
                assert money_log_entry
                assert money_log_entry['token_id'] == tx_token_id
                assert money_log_entry['token_count'] == tx_count

                assert abs(round(money_log_entry['price'] * 1e6) - price_mutez * tx_count) <= 1, (
                    round(money_log_entry['price'] * 1e6),
                    price_mutez,
                )
                assert money_log_entry['royalties_receiver'] == token_ds_entry['issuer']
                assert money_log_entry['payer'] == tx_to
                assert money_log_entry['seller'] == swap_ds_entry['created_by']

            by_author = int(swap_ds_entry['created_by'] == token_ds_entry['issuer'])

            sells_ds[str(tr_info['row_id'])] = {
                'tr': src.datasets.TrEvent(tr_info['row_id']),
                'token_id': str(tx_token_id),
                'count': tx_count,
                'seller': swap_ds_entry['created_by'],
                'buyer': tx_to,
                'price': price,
                'swap_id': swap_ds_entry['swap_id'],
                'author': token_ds_entry['issuer'],
                'by_author': by_author,
                'total_royalties': money_log_entry['royalties'],
                'total_comission': money_log_entry['comission'],
                'total_seller_income': money_log_entry['seller_income'],
            }

            if by_author:
                token_ds_entry['author_sold_prices'].add(price, tx_count)
                author_ds_entry['author_sold_prices'].add(price, tx_count)
            else:
                token_ds_entry['secondary_sold_prices'].add(price, tx_count)
                author_ds_entry['secondary_sold_prices'].add(price, tx_count)

            addrs_ds[tx_to]['bought_prices'].add(price, tx_count)
            swap_ds_entry['sold_count'] += tx_count
            swap_ds_entry['available_count'] -= tx_count
            swap_ds_entry['sold_price_sum'] += price * tx_count

            # assert swap_ds_entry['available_count'] >= 0

            del swap_ds_entry, swap_db_entry, by_author

        else:
            assert sender_category in ['author', 'user', 'ext'], sender_category

            if receiver_category == 'swap':
                if tr_volume > 0:
                    print('Swap with non-zero volume ' + tr_info['hash'])

                if not ah_log_entry:
                    # If token is sent to the Art House without calling contract
                    # it is equivalent to sending it to trash
                    receiver_category = 'burn'

                else:
                    assert ah_log_entry['method'] == 'apply_swap'
                    if tr_volume > 0:
                        print('apply_swap with non-zero volume ' + tr_info['hash'])

                    swap_id = str(created_swap_db_entry['swap_id'])

                    swap_db_entry = swaps_db[str(created_swap_db_entry['swap_id'])]
                    assert swap_db_entry['state'] == 'NOT_EXISTS'
                    swap_db_entry['state'] = 'ACTIVE'

                    swap_ds_entry = swaps_ds[str(created_swap_db_entry['swap_id'])]
                    swap_ds_entry['available_count'] = swap_ds_entry['total_count']
                    del swap_db_entry, swap_ds_entry

            elif receiver_category == 'burn':
                assert tr_volume == 0
                assert ah_log_entry is None

            elif receiver_category == 'ext':
                assert tr_volume >= 0
                # we do not assign price in this case

            elif receiver_category in ['user', 'author']:
                assert ah_log_entry is None

                if sender_category == 'ext':
                    assert tr_volume >= 0
                    if tr_volume > 0:
                        assert money_log_entry
                        assert money_log_entry['method'] == 'apply_ext_swap'
                        price = money_log_entry['price'] / 1e6
                        method = money_log_entry['call']

                else:
                    assert tr_volume == 0

            else:
                assert False

        transfers_ds[str(nft_log_entry['row_id'])] = {
            'tr': src.datasets.TrEvent(nft_log_entry['row_id']),
            'category': f'{sender_category}->{receiver_category}',
            'token_id': str(tx_token_id),
            'price': price,
            'count': tx_count,
            'swap_id': swap_id,
            'sender': tx_from,
            'receiver': tx_to,
            'method': method,
        }

        token_db_entry['own_counts_by_category'][receiver_category] += tx_count
        token_db_entry['own_counts_by_category'][sender_category] -= tx_count
        assert token_db_entry['own_counts_by_category'][sender_category] >= 0

        token_db_entry['own_counts_by_address'][tx_to] += tx_count
        token_db_entry['own_counts_by_address'][tx_from] -= tx_count
        assert token_db_entry['own_counts_by_address'][tx_from] >= 0

        if sender_category == 'author':
            if receiver_category == 'swap':
                token_db_entry['author_swap_balance'] += tx_count
            elif receiver_category == 'burn':
                pass
            else:
                token_db_entry['author_other_balance'] += tx_count
        elif receiver_category == 'burn':
            token_db_entry['author_other_balance'] -= tx_count
        elif receiver_category == 'author':
            if sender_category == 'swap':
                token_db_entry['author_swap_balance'] -= tx_count
            else:
                token_db_entry['author_other_balance'] -= tx_count

post_process()

src.datasets.make_dataset(tokens_ds, config.dataset_dir / 'tokens', tr_info_db)
src.datasets.make_dataset(addrs_ds, config.dataset_dir / 'addrs', tr_info_db)
src.datasets.make_dataset(swaps_ds, config.dataset_dir / 'swaps', tr_info_db)
src.datasets.make_dataset(sells_ds, config.dataset_dir / 'sells', tr_info_db)
src.datasets.make_dataset(transfers_ds, config.dataset_dir / 'transfers', tr_info_db)

src.datasets.validate_datasets()
