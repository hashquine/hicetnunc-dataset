from collections import Counter, defaultdict

import src.config


class MoneyState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.balances = Counter()
        self.addrs = defaultdict(lambda: {
            'total_bought': 0,
            'total_sold': 0,
            'events': [],
        })
        self.tokens = defaultdict(lambda: {
            'events': [],
        })
        self.comission_wallet = {
            'comission_income': 0,
            'percent_income': 0,
            'other_income': 0,
            'spending': 0,
            'events': [],
        }

    def apply_swap_sell(self, row_id, token_id, token_count, payer, beneficiary, price, comission):
        event = {
            'row_id': row_id,
            'type': 'swap_sell',
            'token_id': token_id,
            'token_count': token_count,
            'payer': payer,
            'beneficiary': beneficiary,
            'price': price,
            'comission': comission,
        }
        self.addrs[payer]['total_bought'] += price
        self.addrs[beneficiary]['total_sold'] += price - comission
        self.addrs[payer]['events'].append(event)
        self.addrs[beneficiary]['events'].append(event)
        self.tokens[token_id]['events'].append(event)
        self.comission_wallet['comission_income'] += comission
        self.comission_wallet['events'].append(event)

        self.balances[payer] -= price
        self.balances[beneficiary] += price - comission
        self.balances[src.config.name2addr['comission_wallet']] += comission

    def apply_comission_wallet_baking_percent(self, row_id, sender, volume):
        assert sender == src.config.name2addr['baking_benjamins']
        assert volume > 0
        event = {
            'row_id': row_id,
            'type': 'comission_wallet_baking_percent',
            'sender': sender,
            'receiver': src.config.name2addr['comission_wallet'],
            'volume': volume,
        }
        self.comission_wallet['events'].append(event)
        self.comission_wallet['percent_income'] += volume
        self.balances[src.config.name2addr['baking_benjamins']] -= volume
        self.balances[src.config.name2addr['comission_wallet']] += volume

    def apply_comission_wallet_spending(self, row_id, receiver, volume):
        assert volume > 0
        event = {
            'row_id': row_id,
            'type': 'comission_wallet_spending',
            'sender': src.config.name2addr['comission_wallet'],
            'receiver': receiver,
            'volume': volume,
        }
        self.comission_wallet['events'].append(event)
        self.comission_wallet['spending'] += volume
        self.balances[receiver] += volume
        self.balances[src.config.name2addr['comission_wallet']] -= volume
