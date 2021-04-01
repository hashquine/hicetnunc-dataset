import src.utils
import src.config


class NFTState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.tokens = {}
        self.next_token_id = 152

    def apply_mint(self, row_id, token_id, count, creator, tokens_receiver, info_ipfs):
        assert token_id == self.next_token_id
        assert token_id not in self.tokens
        self.tokens[token_id] = {
            'creator': creator,
            'tokens_receiver': tokens_receiver,
            'mint_count': count,
            'info_ipfs': info_ipfs,
            'mint_row_id': row_id,
            'own_counts': {
                tokens_receiver: count,
            },
            'transfers': [],
        }
        self.next_token_id += 1

    def apply_transfer(self, row_id, txs):
        diff = {}
        for tx in txs:
            count = int(tx['count'])
            if count == 0:
                continue
            sender = tx['from']
            receiver = tx['to']
            token_id = int(tx['token_id'])
            token_own_counts = self.tokens[token_id]['own_counts']
            if sender == receiver:
                diff[(sender, token_id)] = self.get_own_count(sender, token_id)
                continue
            sender_count = self.get_own_count(sender, token_id)
            receiver_count = self.get_own_count(receiver, token_id)
            assert sender_count >= count
            token_own_counts[sender] = sender_count - count
            token_own_counts[receiver] = receiver_count + count
            diff[(sender, token_id)] = self.get_own_count(sender, token_id)
            diff[(receiver, token_id)] = self.get_own_count(receiver, token_id)
            self.tokens[token_id]['transfers'].append({
                'from': sender,
                'to': receiver,
                'count': count,
                'row_id': row_id,
            })

        return {
            (addr, token_id, count)
            for (addr, token_id), count in diff.items()
        }

    def get_own_count(self, addr, token_id):
        if token_id not in self.tokens:
            raise Exception(f'Token {token_id} not found')
        return self.tokens[token_id]['own_counts'].get(addr, 0)
