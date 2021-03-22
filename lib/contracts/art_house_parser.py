
calls_counter = Counter()
status_counter = Counter()
errors_counter = Counter()


def parse_ops(ops):

    art_house_state = ArtHouseState()

    for op in art_house_ops:
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
                    'proto.008-PtEdo2Zk.michelson_v1.script_rejected',
                ]
                # if error['id'] == 'proto.008-PtEdo2Zk.michelson_v1.script_rejected':
                #     print(op_hash, op['parameters'])
                errors_counter[error['id']] += 1

            continue

        else:
            raise Exception(f'Unknown op status = {op_status}, hash = {op_hash}')

        op_type = op['type']

        if op_type == 'origination':
            assert op is art_house_ops[0]
            continue

        assert op_type == 'transaction'

        params = op['parameters']
        call = params['call']
        calls_counter[call] += 1
        value = params['value']

        assert op['entrypoint_id'] == params['id']

        storage = op['storage']
        assert set(storage.keys()) == {'value'}
        storage_value = storage['value']

        assert set(storage_value.keys()) == {
            'curate', 'genesis', 'hdao', 'locked', 'manager', 'metadata', 'objkt',
            'objkt_id', 'royalties', 'size', 'swap_id', 'swaps',
        }
        assert storage_value['curate'] == curate_contract
        assert storage_value['genesis'] == '2021-04-15T02:09:41Z'
        assert storage_value['hdao'] == hdao_contract
        assert storage_value['locked'] == 'true'
        assert storage_value['manager'] == comission_wallet
        assert storage_value['metadata'] == '521'
        assert storage_value['objkt'] == nft_contract
        assert int(storage_value['objkt_id'])
        assert storage_value['royalties'] == '522'
        assert storage_value['size'] == '0'
        assert int(storage_value['swap_id']) >= 0
        assert storage_value['swaps'] == '523'

        if call == 'genesis':
            assert op is art_house_ops[1]
            continue

        assert params['entrypoint'] == params['call']

        if call == 'curate':
            assert params['branch'] == 'LRR'
            assert params['id'] == 2
            assert set(value.keys()) == { 'hDAO_amount', 'objkt_id' }
            assert int(value['hDAO_amount']) >= 0
            assert int(value['objkt_id'])
            assert op['volume'] == 0
            # curate_stamps.append(lib.utils.iso_date_to_stamp(op['time']))
            assert 'big_map_diff' not in op
            continue

        big_map_diff = op['big_map_diff']

        if call == 'collect':
            assert params['branch'] == 'LRL'
            assert params['id'] == 1
            assert set(value.keys()) == { 'objkt_amount', 'swap_id' }
            assert int(value['objkt_amount'])
            assert int(value['swap_id']) >= 0
            assert op['volume'] >= 0

            art_house_state.collect(value, op)
            new_swap_count = art_house_state.swaps[int(value['swap_id'])]['remaining_count']

            assert len(big_map_diff) == 1
            swap_id = int(value['swap_id'])
            assert big_map_diff[0]['key'] == str(swap_id)
            if new_swap_count == 0:
                assert big_map_diff[0]['action'] == 'remove'
            else:
                assert big_map_diff[0]['action'] == 'update'
                assert big_map_diff[0]['value']['objkt_amount'] == str(new_swap_count)

        elif call == 'swap':
            assert params['branch'] == 'RRL'
            assert params['id'] == 5
            assert set(value.keys()) == { 'objkt_amount', 'objkt_id', 'xtz_per_objkt' }
            assert int(value['objkt_amount'])
            assert int(value['objkt_id'])
            assert int(value['xtz_per_objkt']) >= 0
            assert op['volume'] == 0

            swap_id = art_house_state.next_swap_id
            art_house_state.swap(value, op)

            assert len(big_map_diff) == 1
            assert swap_id == int(big_map_diff[0]['key'])
            assert big_map_diff[0]['key'] == str(int(storage_value['swap_id']) - 1)
            assert big_map_diff[0]['action'] == 'update'
            assert big_map_diff[0]['value'] == {
                'issuer': op['sender'],
                **value,
            }

        elif call == 'mint_OBJKT':
            assert params['branch'] == 'RLR'
            assert params['id'] == 4
            assert set(value.keys()) == { 'address', 'amount', 'metadata', 'royalties' }
            assert int(value['amount'])
            assert int(value['royalties']) >= 0
            assert value['metadata'].startswith('ipfs://')
            assert op['volume'] == 0

            objkt_id = art_house_state.next_token_id
            art_house_state.mint(value, op)

            assert len(big_map_diff) == 1
            assert objkt_id == int(big_map_diff[0]['key'])
            assert big_map_diff[0]['key'] == str(int(storage_value['objkt_id']) - 1)
            assert big_map_diff[0]['action'] == 'update'
            assert big_map_diff[0]['value'] == {
                'issuer': op['sender'],
                'royalties': value['royalties'],
            }

        elif call == 'cancel_swap':
            assert params['branch'] == 'LL'
            assert params['id'] == 0
            assert set(value.keys()) == { 'cancel_swap' }
            assert int(value['cancel_swap']) >= 0
            assert op['volume'] == 0
            assert len(big_map_diff) == 1

            art_house_state.cancel_swap(value, op)

            swap_id = int(value['cancel_swap'])
            assert big_map_diff[0]['key'] == str(swap_id)
            assert big_map_diff[0]['action'] == 'remove'

        else:
            raise Exception(f'Unknown art_house call "{call}"')

