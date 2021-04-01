from collections import defaultdict, Counter

class AddrsState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.addrs = defaultdict(lambda: {
            'first_op_row_id': -1,
            'out_op_count': 0,
            'in_op_count': 0,
            'money_received': 0,
            'money_sent': 0,
            'first_op_has_reveal': False,
            'out_calls': Counter(),
        })

    def check_first_addr_op(self, row_id, addr):
        if not addr or addr in self.addrs:
            return
        self.addrs[addr]['first_op_row_id'] = row_id

    def apply_op(self, row_id, sender, receiver, call, volume):
        self.check_first_addr_op(row_id, sender)
        self.addrs[sender]['out_op_count'] += 1
        self.addrs[sender]['money_sent'] += volume
        self.addrs[sender]['out_calls'][call] += 1
        if receiver:
            self.addrs[receiver]['in_op_count'] += 1
            self.addrs[receiver]['money_received'] += 1
            self.check_first_addr_op(row_id, receiver)
        if call == '__reveal__':
            self.addrs[sender]['first_op_has_reveal'] = True
