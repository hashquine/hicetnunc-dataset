class ArtHouseState:
    def __init__(self):
        self.extended_logging = False
        self.reset()

    def reset(self):
        self.swaps = {}
        self.next_swap_id = 0
        self.tokens = {}
        self.next_token_id = 152

    def apply_mint(self, row_id, tokens_receiver, mint_sender, count, info_ipfs, royalties):
        token_id = self.next_token_id
        self.next_token_id += 1
        self.tokens[token_id] = {
            'mint_ah_row_id': row_id,
            'tokens_receiver': tokens_receiver,
            'mint_sender': mint_sender,
            'info_ipfs': info_ipfs,
            'mint_count': count,
            'royalties': royalties,
        }

    def apply_swap(self, row_id, count, swap_sender, token_id, price):
        swap_id = self.next_swap_id
        self.next_swap_id += 1

        self.swaps[swap_id] = {
            'created_row_id': row_id,
            'initial_count': count,
            'swap_sender': swap_sender,
            'remaining_count': count,
            'token_id': token_id,
            'price': price,
            'active': True,
        }

    def apply_cancel_swap(self, row_id, swap_id):
        assert self.swaps[swap_id]['active']
        self.swaps[swap_id]['active'] = False

    def apply_collect(self, row_id, count, swap_id):
        self.swaps[swap_id]['remaining_count'] -= count
        assert self.swaps[swap_id]['remaining_count'] >= 0
