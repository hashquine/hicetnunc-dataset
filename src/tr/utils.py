import config


def get_ops_volume(ops):
    res = 0
    for op in ops:
        assert op['volume'] >= 0
        res += op['volume']
    return res


def get_tr_money_delta(tr):
    res = {}
    for op in tr['ops']:
        if op['volume'] == 0:
            continue
        sender, receiver = op['sender'], op['receiver']
        res[sender] = res.get(sender, 0) - op['volume']
        res[receiver] = res.get(receiver, 0) + op['volume']
    return res


def get_addr_signature(addr):
    return config.addr2name.get(addr, '*')


def get_op_signature(op):
    if op['status'] != 'applied':
        return op['status']
    if op['type'] != 'transaction':
        return op['type']
    call = op.get('parameters', {'call': ''})['call']
    if op['volume'] > 0:
        return (
            call,
            get_addr_signature(op['sender']) + ' > ' + get_addr_signature(op['receiver']),
        )
    return call


def get_tr_signature(tr):
    ext_count = 0
    res = tuple()
    has_any_applied = False
    for op in tr['ops']:
        if op['type'] == 'reveal':
            continue
        if op['status'] == 'applied':
            has_any_applied = True
        if op['sender'] not in config.addr2name and op.get('receiver') not in config.addr2name:
            ext_count += 1
        else:
            res += (get_op_signature(op),)
    if not has_any_applied:
        return tr['ops'][0]['status']
    res = (ext_count > 0,) + res
    return res


def get_ops_addrs(ops):
    res = set()
    for op in ops:
        res.add(op['sender'])
        if 'receiver' in op:
            res.add(op['receiver'])
    return res
