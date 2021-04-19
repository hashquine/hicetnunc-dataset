from collections import Counter

import config
import src.contracts.art_house_state
import src.contracts.state_utils


def parse_ops(ops):
    global calls_counter
    global status_counter
    global errors_counter

    calls_counter = Counter()
    status_counter = Counter()
    errors_counter = Counter()

    ah_state = src.contracts.art_house_state.ArtHouseState()
    ah_state = src.contracts.state_utils.StateRecorder(ah_state)

    for op in ops:
        op_hash = op['hash']
        op_row_id = op['row_id']
        assert type(op_row_id) is int

        op_status = op['status']
        status_counter[op_status] += 1

        if op_status == 'applied':
            pass

        elif op_status in ['backtracked', 'skipped']:
            continue

        elif op_status == 'failed':
            for error in op['errors']:
                assert error['kind'] == 'temporary'
                assert error['id'] in [
                    'proto.008-PtEdo2Zk.michelson_v1.runtime_error',
                    'proto.008-PtEdo2Zk.michelson_v1.script_rejected',
                    'proto.008-PtEdo2Zk.contract.balance_too_low',
                    'proto.008-PtEdo2Zk.gas_exhausted.operation',
                ], error['id']
                # if error['id'] == 'proto.008-PtEdo2Zk.michelson_v1.script_rejected':
                #     print(op_hash, op['parameters'])
                errors_counter[error['id']] += 1

            continue

        else:
            raise Exception(f'Unknown op status = {op_status}, hash = {op_hash}')

        op_type = op['type']

        if op_type == 'origination':
            assert op is ops[0]
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
        assert storage_value['curate'] == config.name2addr['curate_contract']
        assert storage_value['genesis'] == '2021-04-15T02:09:41Z'
        assert storage_value['hdao'] == config.name2addr['hdao_contract']
        assert storage_value['locked'] == 'true'
        assert storage_value['manager'] == config.name2addr['comission_wallet']
        assert storage_value['metadata'] == '521'
        assert storage_value['objkt'] == config.name2addr['nft_contract']
        assert int(storage_value['objkt_id'])
        assert storage_value['royalties'] == '522'
        assert storage_value['size'] == '0'
        assert int(storage_value['swap_id']) >= 0
        assert storage_value['swaps'] == '523'

        if call == 'genesis':
            assert op is ops[1]
            continue

        assert params['entrypoint'] == params['call']

        if call == 'curate':
            assert params['branch'] == 'LRR'
            assert params['id'] == 2
            assert set(value.keys()) == { 'hDAO_amount', 'objkt_id' }
            assert int(value['hDAO_amount']) >= 0
            assert int(value['objkt_id'])
            # assert op['volume'] == 0
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

            ah_state.apply_collect(
                row_id=op_row_id,
                count=int(value['objkt_amount']),
                swap_id=int(value['swap_id']),
            )
            new_swap_count = ah_state.swaps[int(value['swap_id'])]['remaining_count']

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
            if op['volume'] != 0:
                print(f'Non-zero volume of swap op {op_hash}')

            swap_id = ah_state.next_swap_id
            try:
                ah_state.apply_swap(
                    row_id=op_row_id,
                    swap_sender=op['sender'],
                    count=int(value['objkt_amount']),
                    token_id=int(value['objkt_id']),
                    price=int(value['xtz_per_objkt']),
                )
            except Exception:
                print(op)

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

            objkt_id = ah_state.next_token_id
            ah_state.apply_mint(
                row_id=op_row_id,
                mint_sender=op['sender'],
                tokens_receiver=value['address'],
                count=int(value['amount']),
                info_ipfs=value['metadata'],
                royalties=int(value['royalties']),
            )

            assert len(big_map_diff) == 1
            assert objkt_id == int(big_map_diff[0]['key']), (repr(objkt_id), repr(big_map_diff[0]['key']))
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

            ah_state.apply_cancel_swap(
                row_id=op_row_id,
                swap_id=int(value['cancel_swap']),
            )

            swap_id = int(value['cancel_swap'])
            assert big_map_diff[0]['key'] == str(swap_id)
            assert big_map_diff[0]['action'] == 'remove'

        else:
            raise Exception(f'Unknown art_house call "{call}"')

    return ah_state.log
