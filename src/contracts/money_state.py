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
            'total_royalties': 0,
        })
        self.tokens = defaultdict(lambda: {})
        self.comission_wallet = {
            'comission_income': 0,
            'percent_income': 0,
            'other_income': 0,
            'spending': 0,
        }

    def apply_swap_sell(
            self, row_id, token_id, token_count,
            payer, price, seller, seller_income,
            comission, royalties_receiver, royalties,
    ):
        self.addrs[payer]['total_bought'] += price
        self.addrs[seller]['total_sold'] += seller_income
        self.addrs[royalties_receiver]['total_royalties'] += royalties
        self.comission_wallet['comission_income'] += comission

        self.balances[royalties_receiver] += royalties
        self.balances[payer] -= price
        self.balances[seller] += seller_income
        self.balances[src.config.name2addr['comission_wallet']] += comission

    def apply_comission_wallet_baking_percent(self, row_id, sender, volume):
        assert sender == src.config.name2addr['baking_benjamins']
        assert volume > 0
        self.comission_wallet['percent_income'] += volume
        self.balances[src.config.name2addr['baking_benjamins']] -= volume
        self.balances[src.config.name2addr['comission_wallet']] += volume

    def apply_comission_wallet_spending(self, row_id, receiver, volume):
        assert volume > 0
        self.comission_wallet['spending'] += volume
        self.balances[receiver] += volume
        self.balances[src.config.name2addr['comission_wallet']] -= volume
