from collections import Counter

import config
import src.tr.utils
import src.contracts.money_state
import src.contracts.state_utils


def parse_trs(trs):
    ext_swaps_examples = {}

    money_state = src.contracts.money_state.MoneyState()
    money_state = src.contracts.state_utils.StateRecorder(money_state)

    for tr in trs:

        nft_calls = Counter()
        hdao_calls = Counter()
        last_nft_op = None
        for op in tr['ops']:
            if op['type'] == 'transaction' and op['receiver'] == config.name2addr['nft_contract']:
                nft_calls[op['parameters']['call']] += 1
                last_nft_op = op
            if op['type'] == 'transaction' and op['receiver'] == config.name2addr['hdao_contract']:
                hdao_calls[op['parameters']['call']] += 1
        nft_calls = dict(nft_calls)
        hdao_calls = dict(hdao_calls)

        money_delta = src.tr.utils.get_tr_money_delta(tr)
        known_money_delta = {
            config.addr2name[addr]: delta
            for addr, delta in money_delta.items()
            if addr in config.addr2name
        }
        ops_volume = src.tr.utils.get_ops_volume(tr['ops'])

        if nft_calls == {'transfer': 1}:

            tr_ops = tr['ops']

            first_contract = tr['ops'][0]['receiver']
            first_call = tr['ops'][0]['parameters']['call']

            transfer = last_nft_op['parameters']['value']['transfer']
            assert len(transfer) == 1
            sender = transfer[0]['from_']

            assert len(transfer[0]['txs']) == 1
            receiver = transfer[0]['txs'][0]['to_']

            token_id = int(transfer[0]['txs'][0]['token_id'])
            token_count = int(transfer[0]['txs'][0]['amount'])

            if token_count == 0:
                continue

            if (first_contract, first_call) in [
                # opTx8EHENV4LvsexZRGMeXopiU5sEf4m9tnfewNYEk137w6yQrS
                ('KT1MMLb2FVrrE9Do74J3FH1RNNc4QhDuVCNX', 'launchExchange'),

                # ooRHqHnqk3W4hS3h5GSaKQng9bwKGHri5hHHs8cLBf8gw7vyDuv
                ('KT1HzEyact4wXoST7hTAGqoKiKkPvAwt4rCR', 'tezToTokenPayment'),

                # ooF1bszbutpvvb5LWrcmd5A1WoqSKGicB2wr7SsVruKbWoaDasD
                ('KT1HzEyact4wXoST7hTAGqoKiKkPvAwt4rCR', 'tokenToTezPayment'),

                # oopnhfjaK6M56tqBf5MCZRkgfuV6QfSFWFX6bWBhQfdRJhBy9wG
                ('KT1HzEyact4wXoST7hTAGqoKiKkPvAwt4rCR', 'investLiquidity'),

                # ooZ6j78JzwLaH6yVrMnXwXsbun9QwxpT1MxScsfNtT5gtUrFhpa
                ('KT1XJZfADhJkFJVXU75bmAzDAMwxTYvSW1QJ', 'tezToTokenPayment'),

                # onxKKXChLbjXkRBPFn4AQRRnk6meG6Dav8iSxvTtiGJXoZkbdvr
                ('KT1XJZfADhJkFJVXU75bmAzDAMwxTYvSW1QJ', 'investLiquidity'),

                # opPyKPjpMhhjHuSy3CYKEnXPWGARuNbqdkvePHYpu8CsvUgmZ1w
                ('KT1XJZfADhJkFJVXU75bmAzDAMwxTYvSW1QJ', 'tokenToTezPayment'),

                # ootfvp2R3rkqduMZsYtT4zcxa7v8aZhH1ZCtGtf5E3taZXWW9ge
                ('KT1XJZfADhJkFJVXU75bmAzDAMwxTYvSW1QJ', 'divestLiquidity'),

                ('KT1LpvCL8ooYqMX4pnjSjZKaghBPReQPX8br', 'tezToTokenPayment'),
                ('KT1LpvCL8ooYqMX4pnjSjZKaghBPReQPX8br', 'tokenToTezPayment'),
                ('KT1LpvCL8ooYqMX4pnjSjZKaghBPReQPX8br', 'investLiquidity'),
                ('KT1LpvCL8ooYqMX4pnjSjZKaghBPReQPX8br', 'divestLiquidity'),

                ('KT1DCegbuJXoF1eEwX7stzEb6vBVahcPVzQY', 'tezToTokenPayment'),
                ('KT1DCegbuJXoF1eEwX7stzEb6vBVahcPVzQY', 'tokenToTezPayment'),
                ('KT1DCegbuJXoF1eEwX7stzEb6vBVahcPVzQY', 'investLiquidity'),
                ('KT1DCegbuJXoF1eEwX7stzEb6vBVahcPVzQY', 'divestLiquidity'),

                # ??? ooyRrqQbj1zQGfWqG37nzBqzemubPwyeLgmoE8tn4PVVLZn1mq5
                ('KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9', 'swap'),
            ]:
                ext_swaps_examples[(first_contract, first_call)] = tr['hash']

                money_state.apply_ext_swap(
                    row_id=last_nft_op['row_id'],
                    token_id=token_id, token_count=token_count,
                    sender=sender, receiver=receiver,
                    price=ops_volume / 2 / token_count,
                    contract=first_contract, call=first_call,
                )
                continue

            if (first_contract, first_call) != (config.name2addr['art_house_contract'], 'collect'):
                raise Exception(f'Unexpected method {first_call} of external contract {first_contract}')

            assert len(tr_ops) in [5, 6], tr['hash']

            # when the first transfer between users (with non-zero XTZ volume) will happen,
            # this assert will fail
            assert sender == config.name2addr['art_house_contract']

            # get buyer money
            assert tr_ops[0]['parameters']['call'] == 'collect'
            assert tr_ops[0]['receiver'] == config.name2addr['art_house_contract']
            assert tr_ops[0]['volume'] > 0
            payer = tr_ops[0]['sender']
            price = tr_ops[0]['volume']

            # pay royalties
            assert 'parameters' not in tr_ops[1]
            if tr_ops[1]['volume'] == 0:
                print('Zero royalties', tr['hash'])
            royalties_receiver = tr_ops[1]['receiver']
            royalties = tr_ops[1]['volume']

            # pay comission
            assert 'parameters' not in tr_ops[2]
            assert tr_ops[2]['receiver'] == config.name2addr['comission_wallet']
            assert tr_ops[2]['volume'] > 0
            comission = tr_ops[2]['volume']

            # pay to seller
            assert 'parameters' not in tr_ops[3]
            assert tr_ops[3]['volume'] > 0
            seller = tr_ops[3]['receiver']
            seller_income = tr_ops[3]['volume']

            if len(tr_ops) == 6:
                # give hDAO tokens
                assert tr_ops[4]['receiver'] == config.name2addr['hdao_contract']
                assert tr_ops[4]['parameters']['call'] == 'hDAO_batch'
                assert tr_ops[4]['volume'] == 0

            # transfer NFT
            assert tr_ops[-1]['parameters']['call'] == 'transfer'
            assert tr_ops[-1]['receiver'] == config.name2addr['nft_contract']
            assert tr_ops[-1]['volume'] == 0

            money_state.apply_swap_sell(
                row_id=last_nft_op['row_id'],
                token_id=token_id,
                token_count=token_count,
                payer=payer,
                price=price,
                seller=seller,
                seller_income=seller_income,
                comission=comission,
                royalties_receiver=royalties_receiver,
                royalties=royalties,
            )
            continue

        elif nft_calls == {}:

            if hdao_calls:
                continue

            known_money_addrs = set(known_money_delta.keys())
            if known_money_addrs in [{'baking_benjamins'}, set()]:
                for op in tr['ops']:
                    assert op['receiver'] not in config.addr2name
                continue

            assert 'comission_wallet' in known_money_addrs

            if 'baking_benjamins' in known_money_addrs:
                assert known_money_addrs == {'baking_benjamins', 'comission_wallet'}
                assert known_money_delta['baking_benjamins'] < 0
                assert known_money_delta['comission_wallet'] > 0
                assert known_money_delta['comission_wallet'] <= -known_money_delta['baking_benjamins']
                money_state.apply_comission_wallet_baking_percent(
                    row_id=tr['ops'][0]['row_id'],
                    sender=config.name2addr['baking_benjamins'],
                    volume=known_money_delta['comission_wallet'],
                )
                continue

            assert known_money_addrs == {'comission_wallet'}
            assert known_money_delta['comission_wallet'] < 0
            other_addrs = set(money_delta.keys()) - {config.name2addr['comission_wallet']}
            assert len(other_addrs) == 1
            other_addr = list(other_addrs)[0]
            volume = money_delta[other_addr]
            assert volume > 0
            assert money_delta == {
                config.name2addr['comission_wallet']: -volume,
                other_addr: volume
            }
            money_state.apply_comission_wallet_spending(
                row_id=tr['ops'][0]['row_id'],
                receiver=other_addr,
                volume=volume,
            )

        else:
            raise Exception(f'Unhandled case: {nft_calls}')

    return money_state.log
