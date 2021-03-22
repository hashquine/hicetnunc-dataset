class NFTState:
    def __init__(self):
        self.tokens = {}
        self.next_token_id = 152

    def mint(self, pv, op):
        token_id = int(pv['token_id'])
        assert token_id == self.next_token_id
        amount = int(pv['amount'])
        creator = pv['address']
        assert token_id not in self.tokens
        self.tokens[token_id] = {
            'creator': creator,
            'total_amount': amount,
            'token_info_ipfs': pv['token_info']['0@bytes'],
            'created_stamp': lib.utils.iso_date_to_stamp(op['time']),
            'mint_tr_hash': op['hash'],
            'own_counts': {
                creator: amount,
            },
            'transfers': [],
        }
        self.next_token_id += 1

    def transfer(self, pv, op):
        assert len(pv['transfer']) == 1
        trans = pv['transfer'][0]
        sender = trans['from_']
        diff = {}
        for tx in trans['txs']:
            amount = int(tx['amount'])
            if amount == 0:
                continue
            receiver = tx['to_']
            if receiver == curate_contract:
                print(op['hash'])
            token_id = int(tx['token_id'])
            token_own_counts = self.tokens[token_id]['own_counts']
            assert sender != receiver
            sender_count = self.get_own_count(sender, token_id)
            receiver_count = self.get_own_count(receiver, token_id)
            assert sender_count >= amount
            token_own_counts[sender] = sender_count - amount
            token_own_counts[receiver] = receiver_count + amount
            diff[(sender, token_id)] = self.get_own_count(sender, token_id)
            diff[(receiver, token_id)] = self.get_own_count(receiver, token_id)
            self.tokens[token_id]['transfers'].append({
                'from': sender,
                'to': receiver,
                'count': amount,
                'stamp': lib.utils.iso_date_to_stamp(op['time']),
                'hash': op['hash'],
            })

        return {
            (sender, token_id, count)
            for (sender, token_id), count in diff.items()
        }

    def get_own_count(self, addr, token_id):
        if token_id not in self.tokens:
            raise Exception(f'Token {token_id} not found')
        return self.tokens[token_id]['own_counts'].get(addr, 0)
