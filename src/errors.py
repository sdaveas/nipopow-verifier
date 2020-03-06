import json

errors = {
        'merkle': 'Merkle verification failed',
        'stack' : 'Stack length <= 0',
        'branch': 'Branch length too big',
        'merkle_index': 'Merkle index too big',
        }

def extract_message_from_error(e):
    data = json.loads(str(e.value).replace('\'', '"'))['data']
    data_l = list(data.keys())
    return data[data_l[0]]['reason']
