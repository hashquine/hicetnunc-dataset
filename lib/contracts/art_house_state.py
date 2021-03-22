class ArtHouseState:
    def __init__(self):
        self.swaps = {}
        self.next_swap_id = 0
        self.tokens = {}
        self.next_token_id = 152

    def mint(self, pv, op):
        token_id = self.next_token_id
        self.next_token_id += 1
        self.tokens[token_id] = {}

    def swap(self, pv, op):
        swap_id = self.next_swap_id
        self.next_swap_id += 1

        assert int(value['objkt_amount'])
        assert int(value['objkt_id'])
        assert int(value['xtz_per_objkt']) >= 0

        self.swaps[swap_id] = {
            'initial_count': int(value['objkt_amount']),
            'remaining_count': int(value['objkt_amount']),
            'token_id': int(value['objkt_id']),
            'price': int(value['xtz_per_objkt']),
            'active': True,
        }
        # TODO: check sender is token creator

    def cancel_swap(self, pv, op):
        swap_id = int(pv['cancel_swap'])
        assert self.swaps[swap_id]['active']
        self.swaps[swap_id]['active'] = False

    def collect(self, pv, op):
        count = int(value['objkt_amount'])
        swap_id = int(value['swap_id'])
        self.swaps[swap_id]['remaining_count'] -= count
        assert self.swaps[swap_id]['remaining_count'] >= 0
