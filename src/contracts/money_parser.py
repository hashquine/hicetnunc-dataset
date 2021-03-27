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
            assert last_nft_op['parameters']['call'] == 'transfer'
            transfer = last_nft_op['parameters']['value']['transfer']
            assert len(transfer) == 1
            sender = transfer[0]['from_']

            # when the first transfer between users (with non-zero price) will happen,
            # this assert will fail
            assert sender == src.config.name2addr['art_house_contract']
            assert money_delta[src.config.name2addr['art_house_contract']] < 1e-10

            assert len(transfer[0]['txs']) == 1
            receiver = transfer[0]['txs'][0]['to_']

            token_id = int(transfer[0]['txs'][0]['token_id'])
            token_count = int(transfer[0]['txs'][0]['amount'])
            comission_wallet_income = money_delta[src.config.name2addr['comission_wallet']]

            beneficiaries = {}
            payers = {}
            for addr, delta in money_delta.items():
                if addr in [
                    src.config.name2addr['art_house_contract'],
                    src.config.name2addr['comission_wallet'],
                ]:
                    continue
                if delta > 0:
                    beneficiaries[addr] = delta
                elif delta < 0:
                    payers[addr] = delta

            if receiver == src.config.name2addr['comission_wallet']:
                assert len(payers) == 0
                assert len(beneficiaries) == 1
                beneficiary = list(beneficiaries)[0]
                payer = src.config.name2addr['comission_wallet']
                assert comission_wallet_income < 0
                price = abs(comission_wallet_income) / (1.0 - 0.025)
                comission = price * 0.025

            elif len(beneficiaries) == 0:
                assert len(payers) == 1
                payer = list(payers)[0]
                assert money_delta[payer] == -comission_wallet_income
                assert comission_wallet_income > 0
                price = abs(comission_wallet_income)
                beneficiary = src.config.name2addr['comission_wallet']
                comission = price * 0.025

            else:
                assert len(payers) == 1
                assert len(beneficiaries) == 1
                assert comission_wallet_income > 0
                comission = comission_wallet_income
                payer = list(payers)[0]
                price = -money_delta[payer]
                beneficiary = list(beneficiaries)[0]

            assert type(payer) is str
            assert type(beneficiary) is str
            assert price > 0
            assert comission > 0
            assert abs(comission - price * 0.025) < 1e-6

            money_state.apply_swap_sell(
                row_id=last_nft_op['row_id'],
                token_id=token_id,
                token_count=token_count,
                payer=payer,
                beneficiary=beneficiary,
                price=price,
                comission=comission,
            )
            continue

        assert nft_calls == {}
        known_money_addrs = set(known_money_delta.keys())

        assert 'comission_wallet' in known_money_addrs

        if 'baking_benjamins' in known_money_addrs:
            assert known_money_addrs == {'baking_benjamins', 'comission_wallet'}
            assert known_money_delta['baking_benjamins'] < 0
            assert known_money_delta['comission_wallet'] > 0
            assert known_money_delta['comission_wallet'] < -known_money_delta['baking_benjamins']
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
