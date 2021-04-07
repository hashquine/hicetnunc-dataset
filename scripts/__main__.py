import sys
import time
import runpy

modules = {
    '1': 's1_update_blockchain_data',
    '2': 's2_download_ipfs0',
    '3': 's3_download_ipfs1',
    '4': 's4_parse_transactions',
    '5': 's5_get_tzktio_addr_meta',
    '6': 's6_make_previews',
    '7': 's7_make_db_of_static_things',
    '8': 's8_make_datasets',
    '9': 's9_export_cache',
}

modules_chars = '1234_678'

if len(sys.argv) >= 2:
    modules_chars = sys.argv[1]

print('Plan:')
modules_list = []
for module_char in modules_chars:
    if module_char in modules:
        modules_list.append(modules[module_char])
        print(f'- {modules[module_char]}')

if modules_list == []:
    print(f'Error: "{modules_chars}" is not a valid plan.')
    print('Enter list of modules numbers as an argument, for example: 12478')

print()

for module in modules_list:
    print('===========================================')
    print(f'==== {module:32s} =====')
    print('===========================================')
    print()

    time_start = time.time()
    runpy.run_module(module, run_name='__main__')

    print(f'DONE {module} in {time.time() - time_start}s')
