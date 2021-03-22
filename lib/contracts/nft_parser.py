def parse_ops(ops):

    calls_counter = Counter()
    status_counter = Counter()
    errors_counter = Counter()
    senders_counter = Counter()

    nft_state = NFTState()

    for op in ops:
        op_hash = op['hash']

        op_status = op['status']
        status_counter[op_status] += 1

        if op_status == 'applied':
            pass

        elif op_status == 'backtracked':
            continue

        elif op_status == 'failed':
            for error in op['errors']:
                assert error['kind'] == 'temporary'
                assert error['id'] in [
                    'proto.008-PtEdo2Zk.michelson_v1.runtime_error',
                    'proto.008-PtEdo2Zk.gas_exhausted.operation',
                ]
                errors_counter[error['id']] += 1

            continue

        else:
            raise Exception(f'Unknown op status = {op_status}, hash = {op_hash}')

        assert op['volume'] == 0
        senders_counter[op['sender']] += 1

        op_type = op['type']
        if op_type == 'origination':
            assert op is nft_ops[0]
            continue

        assert op_type == 'transaction'

        params = op['parameters']
        call = params['call']
        calls_counter[call] += 1
        value = params['value']

        storage = op['storage']
        assert set(storage.keys()) == {'value'}
        storage_value = storage['value']

        assert set(storage_value.keys()) == {
            'administrator', 'all_tokens',
            'ledger', 'metadata', 'operators',
            'paused', 'token_metadata',
        }
        assert storage_value['administrator'] == art_house_contract
        assert int(storage_value['all_tokens']) >= 0
        assert storage_value['ledger'] == '511'
        assert storage_value['metadata'] == '512'
        assert storage_value['operators'] == '513'
        assert storage_value['token_metadata'] == '514'
        assert storage_value['paused'] == 'false'

        if call == 'set_administrator':
            assert op is nft_ops[1]
            continue

        assert params['entrypoint'] == params['call']


        if call == 'transfer':
            assert op['entrypoint_id'] == 6
            assert params['branch'] == 'RRL'
            assert params['id'] == 6
            assert set(value.keys()) == { 'transfer' }
            assert type(value['transfer']) is list
            assert len(value['transfer']) == 1
            assert set(value['transfer'][0].keys()) == { 'from_', 'txs' }
            assert value['transfer'][0]['from_']
            assert len(value['transfer'][0]['txs']) >= 1

            for tx in value['transfer'][0]['txs']:
                assert set(tx.keys()) == {'amount', 'to_', 'token_id'}

            diff_set = nft_state.transfer(value, op)

            if len(diff_set) == 0:
                assert 'big_map_diff' not in op
                continue

            big_map_diff = op['big_map_diff']
            assert len(big_map_diff) == len(diff_set)
            big_map_diff_set = set()
            for big_map_diff_item in big_map_diff:
                assert big_map_diff_item['action'] == 'update'
                big_map_diff_set.add((
                    big_map_diff_item['key']['0@address'],
                    int(big_map_diff_item['key']['1@nat']),
                    int(big_map_diff_item['value']),
                ))
            assert big_map_diff_set == diff_set

        elif call == 'mint':
            assert op['sender'] == art_house_contract
            assert op['is_internal']
            assert op['entrypoint_id'] == 2
            assert params['branch'] == 'LRL'
            assert params['id'] == 2
            assert set(value.keys()) == { 'address', 'amount', 'token_id', 'token_info' }
            assert int(value['amount'])
            assert int(value['token_id'])
            assert value['address'] == op['creator']
            assert set(value['token_info'].keys()) == {'0@bytes'}
            assert value['token_info']['0@bytes'].startswith('ipfs://')
            assert storage_value['all_tokens'] == str(int(value['token_id']) + 1)

            big_map_diff = op['big_map_diff']
            assert len(big_map_diff) == 2
            assert big_map_diff[0]['key'] == value['token_id']
            assert big_map_diff[0]['action'] == 'update'
            assert big_map_diff[0]['value'] == {
                'token_id': value['token_id'],
                'token_info': value['token_info'],
            }
            assert big_map_diff[1]['key'] == {
                '0@address': value['address'],
                '1@nat': value['token_id'],
            }
            assert big_map_diff[1]['action'] == 'update'
            assert big_map_diff[1]['value'] == value['amount']
            nft_state.mint(value, op)

        else:
            raise Exception(f'Unknown call: {call}')
