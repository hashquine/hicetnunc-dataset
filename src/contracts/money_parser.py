from collections import Counter

import src.config
import src.tr.utils
import src.contracts.money_state
import src.contracts.state_utils


def parse_trs(trs):
    money_state = src.contracts.money_state.MoneyState()
    money_state = src.contracts.state_utils.StateRecorder(money_state)

    for tr in trs:

        nft_calls = Counter()
        last_nft_op = None
        for op in tr['ops']:
            if op['type'] == 'transaction' and op['receiver'] == src.config.name2addr['nft_contract']:
                nft_calls[op['parameters']['call']] += 1
                last_nft_op = op
        nft_calls = dict(nft_calls)

        money_delta = src.tr.utils.get_tr_money_delta(tr)
        known_money_delta = {
            src.config.addr2name[addr]: delta
            for addr, delta in money_delta.items()
            if addr in src.config.addr2name
        }

        if nft_calls == {'transfer': 1}:

            tr_ops = tr['ops']

            first_contract = tr['ops'][0]['receiver']
            first_call = tr['ops'][0]['parameters']['call']

            if (first_contract, first_call) in [
                ('KT1MMLb2FVrrE9Do74J3FH1RNNc4QhDuVCNX', 'launchExchange'),
                ('KT1HzEyact4wXoST7hTAGqoKiKkPvAwt4rCR', 'tezToTokenPayment'),
                ('KT1HzEyact4wXoST7hTAGqoKiKkPvAwt4rCR', 'tokenToTezPayment'),
                ('KT1HzEyact4wXoST7hTAGqoKiKkPvAwt4rCR', 'investLiquidity'),
            ]:
                continue

            assert len(tr_ops) in [6]

            if len(tr['ops']) == 7:
                assert tr['ops'][0]['type'] == 'reveal'
                tr_ops = tr['ops'][1:]

            assert len(tr_ops) == 6

            # get buyer money
            assert tr_ops[0]['parameters']['call'] == 'collect'
            assert tr_ops[0]['receiver'] == src.config.name2addr['art_house_contract']
            assert tr_ops[0]['volume'] > 0
            payer = tr_ops[0]['sender']
            price = tr_ops[0]['volume']

            # pay royalties
            assert 'parameters' not in tr_ops[1]
            assert tr_ops[1]['volume'] > 0
            royalties_receiver = tr_ops[1]['receiver']
            royalties = tr_ops[1]['volume']

            # pay comission
            assert 'parameters' not in tr_ops[2]
            assert tr_ops[2]['receiver'] == src.config.name2addr['comission_wallet']
            assert tr_ops[2]['volume'] > 0
            comission = tr_ops[2]['volume']

            # pay to seller
            assert 'parameters' not in tr_ops[3]
            assert tr_ops[3]['volume'] > 0
            seller = tr_ops[3]['receiver']
            seller_income = tr_ops[3]['volume']

            # give hDAO tokens
            assert tr_ops[4]['receiver'] == src.config.name2addr['hdao_contract']
            assert tr_ops[4]['parameters']['call'] == 'hDAO_batch'
            assert tr_ops[4]['volume'] == 0

            # transfer NFT
            assert tr_ops[5]['parameters']['call'] == 'transfer'
            assert tr_ops[5]['receiver'] == src.config.name2addr['nft_contract']
            assert tr_ops[5]['volume'] == 0

            transfer = tr_ops[5]['parameters']['value']['transfer']
            assert len(transfer) == 1
            sender = transfer[0]['from_']

            # when the first transfer between users (with non-zero XTZ volume) will happen,
            # this assert will fail
            assert sender == src.config.name2addr['art_house_contract']

            assert len(transfer[0]['txs']) == 1
            receiver = transfer[0]['txs'][0]['to_']

            token_id = int(transfer[0]['txs'][0]['token_id'])
            token_count = int(transfer[0]['txs'][0]['amount'])

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

        assert nft_calls == {}

        if 'parameters' in tr['ops'][0]:
            if tr['ops'][0]['parameters']['call'] in [
                'launchExchange', 'tokenToTezPayment', 'investLiquidity',
                'tezToTokenPayment', 'divestLiquidity',
            ]:
                continue

        known_money_addrs = set(known_money_delta.keys())
        if known_money_addrs in [{'baking_benjamins'}, set()]:
            for op in tr['ops']:
                assert op['receiver'] not in src.config.addr2name
            continue

        assert 'comission_wallet' in known_money_addrs

        if 'baking_benjamins' in known_money_addrs:
            assert known_money_addrs == {'baking_benjamins', 'comission_wallet'}
            assert known_money_delta['baking_benjamins'] < 0
            assert known_money_delta['comission_wallet'] > 0
            assert known_money_delta['comission_wallet'] <= -known_money_delta['baking_benjamins']
            money_state.apply_comission_wallet_baking_percent(
                row_id=tr['ops'][0]['row_id'],
                sender=src.config.name2addr['baking_benjamins'],
                volume=known_money_delta['comission_wallet'],
            )
            continue

        assert known_money_addrs == {'comission_wallet'}
        assert known_money_delta['comission_wallet'] < 0
        other_addrs = set(money_delta.keys()) - {src.config.name2addr['comission_wallet']}
        assert len(other_addrs) == 1
        other_addr = list(other_addrs)[0]
        volume = money_delta[other_addr]
        assert volume > 0
        assert money_delta == {
            src.config.name2addr['comission_wallet']: -volume,
            other_addr: volume
        }
        money_state.apply_comission_wallet_spending(
            row_id=tr['ops'][0]['row_id'],
            receiver=other_addr,
            volume=volume,
        )

    return money_state.log
